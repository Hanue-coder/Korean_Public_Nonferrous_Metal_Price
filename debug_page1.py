import urllib.request, re, ssl, csv, os

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# Check total and page 1 SNs
url = "https://www.pps.go.kr/bichuk/bbs/list.do?key=00825&pageIndex=1"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as r:
    html = r.read().decode("utf-8", errors="replace")

sns = re.findall(r"goView\('(\d+)'\)", html)
total = re.search(r'txt-color-darken[^"]*">\s*(\d[\d,]+)\s*</span>', html)
print("Total posts:", total.group(1) if total else "not found")
print("Page 1 SNs:", sns[:10])

# Check which SNs are already in CSV
csv_path = os.path.join(os.path.dirname(__file__), "data", "prices.csv")
scraped_dates = set()
with open(csv_path, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        scraped_dates.add(row["date"])
print(f"\nLatest dates in CSV: {sorted(scraped_dates)[-3:]}")

# Fetch detail page of first SN
if sns:
    sn = sns[0]
    view_url = f"https://www.pps.go.kr/bichuk/bbs/view.do?key=00825&bbsSn={sn}"
    req2 = urllib.request.Request(view_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req2, context=ssl_ctx, timeout=30) as r:
        detail_html = r.read().decode("utf-8", errors="replace")

    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})</td>", detail_html)
    m2 = re.search(r"(\d{4})-(\d{2})-(\d{2})", detail_html)
    print(f"\nFirst SN={sn}")
    print(f"Date pattern (dots): {m.group(0) if m else 'not found'}")
    print(f"Date pattern (dashes): {m2.group(0) if m2 else 'not found'}")

    # Show first 500 chars of any date-related content
    idx = detail_html.find("2026")
    if idx != -1:
        print(f"\nContext around '2026': ...{detail_html[idx-50:idx+100]}...")
