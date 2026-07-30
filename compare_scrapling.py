"""
Scrapling으로 조달청 최신 비철금속 고시가를 수집하고 prices.csv와 비교
Python 3.12 환경에서 실행 (pip install scrapling)
"""

import csv, os, re, math
from scrapling import Fetcher

BASE_URL  = "https://www.pps.go.kr"
LIST_URL  = BASE_URL + "/bichuk/bbs/list.do?key=00825"
VIEW_URL  = BASE_URL + "/bichuk/bbs/view.do?key=00825&bbsSn={sn}"
CSV_PATH  = os.path.join(os.path.dirname(__file__), "data", "prices.csv")

METAL_COLS = {
    "알루미늄(서구산)":    "알루미늄_서구산_incl",
    "알루미늄(비서구산)":  "알루미늄_비서구산_incl",
    "구리(99.99%이상)":    "구리_9999pct이상_incl",
    "납(99.99%이상)":      "납_9999pct이상_incl",
    "아연":                "아연_incl",
    "주석(99.85%이상)":    "주석_9985pct이상_incl",
    "주석(99.99%이상)":    "주석_9999pct이상_incl",
    "니켈(합금용)":        "니켈_합금용_incl",
    "니켈(도금용)":        "니켈_도금용_incl",
}

ALIASES = {
    "주석(99.99%이상)": ["주석(99.90%이상)", "주석(99.99%이상)"],
    "납(99.99%이상)":   ["납(99.99%이상)", "납"],
}

fetcher = Fetcher(auto_match=False)


def get_latest_bbssns(n=5):
    """목록 1페이지에서 최신 n개 글번호 수집"""
    page = fetcher.get(LIST_URL, timeout=20)
    sns = re.findall(r"goView\('(\d+)'", page.html_content)
    seen, result = set(), []
    for sn in sns:
        if sn not in seen:
            seen.add(sn)
            result.append(sn)
        if len(result) >= n:
            break
    return result


def parse_detail(sn):
    """상세 페이지에서 날짜 + 가격 파싱"""
    html = fetcher.get(VIEW_URL.format(sn=sn), timeout=20).html_content

    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})</td>", html)
    if not m:
        m = re.search(r"(\d{4})(\d{2})(\d{2})</td>", html)
    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None

    prices = {}
    for metal, col in METAL_COLS.items():
        target_names = ALIASES.get(metal, [metal])
        val = None
        for name in target_names:
            pat = re.escape(name) + r"</td>\s*<td[^>]*>.*?</td>\s*<td[^>]*>([\d,]+)원/톤</td>"
            mm = re.search(pat, html, re.DOTALL)
            if mm:
                val = int(mm.group(1).replace(",", "")) // 1000
                break
            idx = html.find(f">{name}<")
            if idx == -1:
                idx = html.find(name)
            if idx != -1:
                fm = re.search(r"([\d,]+)원/톤", html[idx:idx+400])
                if fm:
                    raw = int(fm.group(1).replace(",", ""))
                    if 100_000 <= raw <= 999_999_999:
                        val = raw // 1000
                        break
        prices[col] = val

    return date, prices


def load_csv_row(date):
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["date"] == date:
                return row
    return None


def main():
    print("=" * 65)
    print("조달청 최신 데이터 vs prices.csv 비교 (Scrapling)")
    print("=" * 65)

    sns = get_latest_bbssns(n=5)
    print(f"최신 글번호 {len(sns)}개: {sns}\n")

    for sn in sns:
        date, live = parse_detail(sn)
        if not date:
            print(f"[bbsSn={sn}] 날짜 파싱 실패\n")
            continue

        csv_row = load_csv_row(date)

        print(f"날짜: {date}  (bbsSn={sn})")
        print(f"{'품목':<20} {'조달청(실시간)':>14} {'CSV 저장값':>12} {'차이':>10} {'상태'}")
        print("-" * 65)

        all_match = True
        for metal, col in METAL_COLS.items():
            live_val = live.get(col)
            csv_val  = int(csv_row[col]) if csv_row and csv_row.get(col) else None

            if live_val is None:
                status = "수집실패"
                diff_str = "-"
                all_match = False
            elif csv_val is None:
                status = "CSV없음"
                diff_str = "-"
                all_match = False
            else:
                diff = live_val - csv_val
                diff_str = f"{diff:+,}" if diff != 0 else "0"
                status = "일치" if diff == 0 else "불일치"
                if diff != 0:
                    all_match = False

            lv = f"{live_val:,}" if live_val else "-"
            cv = f"{csv_val:,}" if csv_val else "-"
            print(f"{metal:<20} {lv:>14} {cv:>12} {diff_str:>10}  {status}")

        print(f"결과: {'모두 일치' if all_match else '차이 있음'}\n")


if __name__ == "__main__":
    main()
