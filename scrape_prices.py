"""
Korean Public Nonferrous Metal Price Scraper
Source: https://www.pps.go.kr/bichuk/bbs/list.do?key=00825

Table structure per detail page row:
  <td>MATERIAL</td>
  <td>LOCATION</td>
  <td>PRICE원/톤</td>   ← base price (부가세 미포함 기준 단가)
  <td>QUOTA</td>
  <td>YYYY.MM.DD</td>
  <td>VAT_RATE</td>     ← e.g. 0.0 or 10.0
  <td>VAT_AMOUNT</td>

Output CSV columns:
  date, <material>_excl, <material>_incl  (×9 materials, KRW/ton)
"""

import urllib.request
import re
import csv
import time
import ssl
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL  = "https://www.pps.go.kr"
LIST_URL  = BASE_URL + "/bichuk/bbs/list.do?key=00825&pageIndex={page}"
VIEW_URL  = BASE_URL + "/bichuk/bbs/view.do?key=00825&bbsSn={sn}"

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "data", "prices.csv")
LOG_FILE   = os.path.join(os.path.dirname(__file__), "data", "scrape.log")

USER_AGENT   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DELAY_LIST   = 0.2
DELAY_DETAIL = 0.35
START_DATE   = "2012-01-06"

# 9 target materials
# Some posts use 99.90% instead of 99.99% for tin - both are accepted.
MATERIALS = [
    "알루미늄(서구산)",
    "알루미늄(비서구산)",
    "구리(99.99%이상)",
    "납(99.99%이상)",
    "아연",
    "주석(99.85%이상)",
    "주석(99.99%이상)",   # some posts: 99.90%이상
    "니켈(합금용)",
    "니켈(도금용)",
]

# Alternate spellings found in older posts
ALIASES: dict[str, list[str]] = {
    "주석(99.99%이상)": ["주석(99.90%이상)", "주석(99.99%이상)"],
    "납(99.99%이상)":   ["납(99.99%이상)", "납"],
}

# CSV header: date, then excl_vat and incl_vat price per material
def _col(mat: str) -> str:
    return mat.replace("(", "_").replace(")", "").replace("%", "pct").replace(".", "")

CSV_HEADER = ["date"]
for m in MATERIALS:
    col = _col(m)
    CSV_HEADER += [f"{col}_excl", f"{col}_incl"]

# ---------------------------------------------------------------------------
# SSL / HTTP
# ---------------------------------------------------------------------------

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def fetch(url: str, retries: int = 3) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, context=_ssl_ctx, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as exc:
            if attempt == retries - 1:
                raise
            log(f"  retry {attempt+1}/{retries}: {exc}")
            time.sleep(2)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
_log_f = open(LOG_FILE, "w", encoding="utf-8")


def log(msg: str) -> None:
    line = f"{datetime.now().strftime('%H:%M:%S')} {msg}"
    print(line)
    _log_f.write(line + "\n")
    _log_f.flush()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_total_and_pages(html: str) -> tuple[int, int]:
    m = re.search(r'txt-color-darken[^"]*">\s*(\d[\d,]+)\s*</span>', html)
    if not m:
        raise ValueError("Total post count not found in list HTML")
    total = int(m.group(1).replace(",", ""))
    return total, -(-total // 10)


def parse_bbssns(html: str) -> list[str]:
    return re.findall(r"goView\('(\d+)'", html)


def parse_date(html: str) -> str | None:
    """Extract the sale date from the detail page.
    Handles two formats:
      - YYYY.MM.DD</td>  (normal)
      - YYYYMMDD</td>    (some older posts, e.g. 2016-12-26)
    """
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})</td>", html)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(\d{4})(\d{2})(\d{2})</td>", html)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _search_material(html: str, names: list[str]) -> int | None:
    """
    Find the first occurrence of any name in `names` inside a <td> and return
    the price (KRW/ton) from the next price cell.

    Expected row structure:
      <td>NAME</td>
      <td ...>LOCATION</td>    ← skip
      <td>PRICE원/톤</td>       ← capture
    """
    for name in names:
        escaped = re.escape(name)
        # Strict: td→td→price td
        m = re.search(
            escaped + r"</td>\s*<td[^>]*>.*?</td>\s*<td[^>]*>([\d,]+)원/톤</td>",
            html,
            re.DOTALL,
        )
        if m:
            return int(m.group(1).replace(",", ""))

        # Fallback: find name, grab next 원/톤 within 400 chars
        idx = html.find(f">{name}<")
        if idx == -1:
            idx = html.find(name)
        if idx != -1:
            snippet = html[idx: idx + 400]
            fm = re.search(r"([\d,]+)원/톤", snippet)
            if fm:
                val = int(fm.group(1).replace(",", ""))
                if 100_000 <= val <= 999_999_999:
                    return val
    return None


def parse_vat_rate(html: str, after_idx: int) -> float:
    """
    Find the VAT rate (부가세율) cell that appears after `after_idx`.
    Returns 0.0 if not found.
    """
    snippet = html[after_idx: after_idx + 300]
    m = re.search(r"<td[^>]*>\s*([\d.]+)\s*</td>", snippet)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return 0.0


def parse_prices(html: str) -> dict[str, tuple[int | None, int | None]]:
    """
    Returns {material: (price_excl_vat, price_incl_vat)} for all 9 materials.
    If VAT rate in the page is > 0, derive excl from incl (÷(1+rate/100)).
    Otherwise compute incl as base * 1.1 (standard 10% VAT).
    """
    results: dict[str, tuple[int | None, int | None]] = {}

    for material in MATERIALS:
        names = ALIASES.get(material, [material])
        base_price = _search_material(html, names)

        if base_price is None:
            results[material] = (None, None)
            continue

        # Find VAT rate near this material's row
        idx = html.find(names[0]) if names[0] in html else html.find(material)
        vat_rate = parse_vat_rate(html, idx) if idx != -1 else 0.0

        # The listed price is always VAT-inclusive (부가세 10% 포함), in KRW/ton.
        # Convert to KRW/kg. Excl price is ceiling at 1 decimal place → integer.
        import math
        price_incl = base_price // 1000
        price_excl = math.ceil(base_price / 1.1 / 1000)  # ceil at first decimal → integer

        results[material] = (price_excl, price_incl)

    return results


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------

def load_scraped_dates(csv_path: str) -> set[str]:
    if not os.path.exists(csv_path):
        return set()
    scraped: set[str] = set()
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            scraped.add(row["date"])
    return scraped


# ---------------------------------------------------------------------------
# Debug mode
# ---------------------------------------------------------------------------

def debug_single(sn: str) -> None:
    log(f"[DEBUG] bbsSn={sn}")
    html = fetch(VIEW_URL.format(sn=sn))
    date = parse_date(html)
    prices = parse_prices(html)
    print(f"\nDate: {date}")
    print(f"{'Material':<25} {'Excl VAT (원/톤)':>18} {'Incl VAT (원/톤)':>18}")
    print("-" * 65)
    for mat, (excl, incl) in prices.items():
        e = f"{excl:>18,}" if excl else f"{'NOT FOUND':>18}"
        i = f"{incl:>18,}" if incl else f"{'NOT FOUND':>18}"
        print(f"{mat:<25} {e} {i}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_new_bbssns(scraped_dates: set[str]) -> list[str]:
    """Collect only bbsSns not yet in the CSV.

    Incremental mode (CSV exists): scan pages front-to-back; stop when every
    SN on a page has already been scraped.
    Full scan (first run): collect all pages.
    """
    log("Step 1: collecting new bbsSn values …")
    html0 = fetch(LIST_URL.format(page=1))
    total, pages = parse_total_and_pages(html0)
    log(f"  Total posts: {total:,}  →  {pages} pages")

    # Parse existing bbsSns from CSV dates — not possible directly, so we
    # track which SNs lead to already-scraped dates during detail scraping.
    # For the list scan, use a simpler heuristic: stop after LOOKBACK pages
    # with no new SNs found when we already have data.
    full_scan = len(scraped_dates) == 0
    # In incremental mode, only scan the first LOOKBACK pages (covers ~3 months)
    LOOKBACK = 15 if not full_scan else pages

    all_sns: list[str] = []
    seen: set[str] = set()

    for pg in range(1, LOOKBACK + 1):
        try:
            html = html0 if pg == 1 else fetch(LIST_URL.format(page=pg))
            for sn in parse_bbssns(html):
                if sn not in seen:
                    seen.add(sn)
                    all_sns.append(sn)
            log(f"  Page {pg}/{LOOKBACK}  cumulative: {len(all_sns)} sns")
        except Exception as exc:
            log(f"  ERROR page {pg}: {exc}")
        time.sleep(DELAY_LIST)

    log(f"  Collected {len(all_sns)} bbsSn values to check")
    return all_sns


def main(debug_sn: str | None = None) -> None:
    if debug_sn:
        debug_single(debug_sn)
        return

    scraped_dates = load_scraped_dates(OUTPUT_CSV)
    all_sns = collect_new_bbssns(scraped_dates)
    log(f"Step 2: {len(scraped_dates)} dates already saved - will skip")

    is_new = not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0
    csv_file = open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig")
    writer = csv.writer(csv_file)
    if is_new:
        writer.writerow(CSV_HEADER)
        csv_file.flush()

    log(f"Step 3: scraping {len(all_sns)} detail pages …")
    saved = errors = skipped_dup = skipped_old = 0

    for i, sn in enumerate(all_sns, 1):
        try:
            html  = fetch(VIEW_URL.format(sn=sn))
            date  = parse_date(html)

            if date is None:
                errors += 1
                log(f"  [{i}] bbsSn={sn}: date not found")
                time.sleep(DELAY_DETAIL)
                continue

            if date < START_DATE:
                skipped_old += 1
                time.sleep(DELAY_DETAIL)
                continue

            if date in scraped_dates:
                skipped_dup += 1
                time.sleep(DELAY_DETAIL)
                continue

            prices = parse_prices(html)
            row = [date]
            for mat in MATERIALS:
                excl, incl = prices[mat]
                row += [excl if excl is not None else "",
                        incl if incl is not None else ""]

            writer.writerow(row)
            csv_file.flush()
            scraped_dates.add(date)
            saved += 1

            if i % 100 == 0 or i == len(all_sns):
                log(f"  [{i}/{len(all_sns)}] saved={saved} dup={skipped_dup} old={skipped_old} err={errors}")

        except Exception as exc:
            errors += 1
            log(f"  ERROR bbsSn={sn}: {exc}")

        time.sleep(DELAY_DETAIL)

    csv_file.close()
    log(f"DONE - saved={saved} dup={skipped_dup} old={skipped_old} err={errors}")
    log(f"Output: {OUTPUT_CSV}")
    _log_f.close()


if __name__ == "__main__":
    # python scrape_prices.py            → full scrape
    # python scrape_prices.py debug 2606190005 → inspect one post
    if len(sys.argv) == 3 and sys.argv[1] == "debug":
        main(debug_sn=sys.argv[2])
    else:
        main()
