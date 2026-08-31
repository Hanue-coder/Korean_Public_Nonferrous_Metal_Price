"""
prices.csv → data/prices.json 변환기
보고서 JS에서 fetch('data/prices.json')으로 사용

JSON 구조:
{
  "updated": "2026-06-19",
  "unit": "원/kg",
  "metals": { "AL": {"label": "알루미늄(서구산)"}, ... },
  "rows": [
    { "date": "2026-06-19", "AL_excl": 5736, "AL_incl": 6310, ... },
    ...
  ]
}
"""

import csv
import json
import math
import os

BASE_DIR = os.path.dirname(__file__)
INPUT_CSV = os.path.join(BASE_DIR, "data", "prices.csv")
OUTPUT_JSON = os.path.join(BASE_DIR, "data", "prices.json")

# CSV 컬럼 → 보고서 품목 코드 매핑
METAL_MAP = {
    "AL":  {"label": "알루미늄(서구산)",  "col_excl": "알루미늄_서구산_excl",  "col_incl": "알루미늄_서구산_incl"},
    "AL2": {"label": "알루미늄(비서구산)","col_excl": "알루미늄_비서구산_excl","col_incl": "알루미늄_비서구산_incl"},
    "CU":  {"label": "구리(99.99%이상)",  "col_excl": "구리_9999pct이상_excl",  "col_incl": "구리_9999pct이상_incl"},
    "PB":  {"label": "납(99.99%이상)",    "col_excl": "납_9999pct이상_excl",    "col_incl": "납_9999pct이상_incl"},
    "ZN":  {"label": "아연",              "col_excl": "아연_excl",              "col_incl": "아연_incl"},
    "SN":  {"label": "주석(99.85%이상)",  "col_excl": "주석_9985pct이상_excl",  "col_incl": "주석_9985pct이상_incl"},
    "SN2": {"label": "주석(99.99%이상)",  "col_excl": "주석_9999pct이상_excl",  "col_incl": "주석_9999pct이상_incl"},
    "NI":  {"label": "니켈(합금용)",      "col_excl": "니켈_합금용_excl",       "col_incl": "니켈_합금용_incl"},
    "NI2": {"label": "니켈(도금용)",      "col_excl": "니켈_도금용_excl",       "col_incl": "니켈_도금용_incl"},
}

def convert():
    rows = []
    with open(INPUT_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row["date"].strip()
            if not date:
                continue
            entry = {"date": date}
            for code, meta in METAL_MAP.items():
                incl = row.get(meta["col_incl"], "").strip()
                incl_val = int(incl) if incl else None
                # 세액=floor(공급가액×0.1) 기준: 공급가액 = ceil(고시가 / 1.1)
                excl_val = math.ceil(incl_val / 1.1) if incl_val else None
                entry[code + "_excl"] = excl_val
                entry[code + "_incl"] = incl_val
            rows.append(entry)

    rows.sort(key=lambda r: r["date"])
    latest = rows[-1]["date"] if rows else ""

    output = {
        "updated": latest,
        "unit": "원/kg",
        "metals": {code: {"label": meta["label"]} for code, meta in METAL_MAP.items()},
        "rows": rows,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    print(f"완료: {len(rows)}행 → {OUTPUT_JSON}")
    print(f"최신 날짜: {latest}")

if __name__ == "__main__":
    convert()
