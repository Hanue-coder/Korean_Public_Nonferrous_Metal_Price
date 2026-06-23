import urllib.request
import re
import csv
import time
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = "https://www.pps.go.kr"
UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
OUT  = r"C:\Users\USER\Desktop\aluminum_prices.csv"
LOG  = r"C:\Users\USER\Desktop\scrape_log.txt"

def log(msg):
    from datetime import datetime
    line = f"{datetime.now().strftime('%H:%M:%S')} {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def fetch(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2)

# Step 1: collect all bbsSn
with open(LOG, "w", encoding="utf-8") as f:
    f.write("")
log("Start (Python scraper)")

html0 = fetch(f"{BASE}/bichuk/bbs/list.do?key=00825&pageIndex=1")
m = re.search(r'txt-color-darken">(\d[\d,]+)</span>', html0)
total = int(m.group(1).replace(",",""))
pages = -(-total // 10)
log(f"Total: {total}, Pages: {pages}")

all_sns = []
for pg in range(1, pages+1):
    try:
        html = fetch(f"{BASE}/bichuk/bbs/list.do?key=00825&pageIndex={pg}")
        sns = re.findall(r"goView\('(\d+)',\s*'0001'\)", html)
        all_sns.extend(sns)
        if pg % 50 == 0:
            log(f"List {pg}/{pages} (sns: {len(all_sns)})")
    except Exception as e:
        log(f"List error page {pg}: {e}")
    time.sleep(0.2)

log(f"All bbsSns: {len(all_sns)}")

# Step 2: fetch detail pages, find 알루미늄(서구산) row specifically
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["date","price_ton_incl_vat","kg_excl_vat","kg_incl_vat"])

ok = 0
for i, sn in enumerate(all_sns, 1):
    try:
        html = fetch(f"{BASE}/bichuk/bbs/view.do?key=00825&bbsSn={sn}")

        # Find 알루미늄(서구산) row and extract its price
        # Pattern: 알루미늄(서구산) in a td, then skip 1 td (location), then price td
        m_al = re.search(
            r'알루미늄\(서구산\)</td>\s*<td[^>]*>[^<]*</td>\s*<td>([\d,]+)원/톤</td>',
            html
        )
        if not m_al:
            # Fallback: simpler pattern
            m_al = re.search(r'알루미늄\(서구산\)[\s\S]{0,200}?([\d,]+)원/톤', html)
        if not m_al:
            continue

        price_str = m_al.group(1).replace(",","")
        ton = int(price_str)
        if ton < 500000 or ton > 100000000:
            continue

        # Get date from table
        m_dt = re.search(r'(\d{4})\.(\d{2})\.(\d{2})</td>', html)
        if not m_dt:
            continue
        date_str = f"{m_dt.group(1)}-{m_dt.group(2)}-{m_dt.group(3)}"
        if date_str < "2012-01-06":
            continue

        kg_excl = round(ton / 1.1 / 1000)
        kg_incl = round(ton / 1000)

        with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([date_str, ton, kg_excl, kg_incl])
        ok += 1

        if i % 200 == 0:
            log(f"Detail {i}/{len(all_sns)} (saved: {ok})")
    except Exception as e:
        log(f"Error [{sn}]: {e}")
    time.sleep(0.3)

log(f"DONE. {ok} records saved to {OUT}")
