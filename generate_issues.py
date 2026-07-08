import csv, json, os
from datetime import datetime, timedelta

CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'prices.csv')
OUT_PATH = os.path.join(os.path.dirname(__file__), 'issues_data.js')

METALS = [
    ('알루미늄(서구산)',  '알루미늄_서구산_incl'),
    ('알루미늄(비서구산)','알루미늄_비서구산_incl'),
    ('구리(99.99%)',      '구리_9999pct이상_incl'),
    ('납(99.99%)',        '납_9999pct이상_incl'),
    ('아연',              '아연_incl'),
    ('주석(99.85%)',      '주석_9985pct이상_incl'),
    ('주석(99.99%)',      '주석_9999pct이상_incl'),
    ('니켈(합금용)',      '니켈_합금용_incl'),
    ('니켈(도금용)',      '니켈_도금용_incl'),
]

# Pre-written summaries: date -> {tag, tag_type, body, sources}
SUMMARIES = {
    '2026-06-24': {
        'tag': '전품목 하락', 'tag_type': 'down',
        'body': '미국-이란 핵 협상 타결 기대감으로 호르무즈 해협 봉쇄 우려가 완화되며 중동산 알루미늄 추가 공급 전망이 부각됐습니다. 동시에 중국의 부진한 경제 지표(제조업 PMI 하락)가 수요 약화 우려를 자극하며 비철금속 전반에 매도세가 집중됐습니다. LME 알루미늄 현금가는 $3,263 → $3,148/t으로 단일 세션 최대 낙폭(-3.52%)을 기록했습니다.',
        'sources': [{'title': 'Discovery Alert — LME Aluminium Prices on 24 June 2026', 'url': 'https://discoveryalert.com.au/aluminium-prices-geopolitics-lme-selloff-june-2026/'}],
    },
    '2026-06-16': {
        'tag': '알루미늄 급락', 'tag_type': 'down',
        'body': '미국-이란 협상 진전으로 호르무즈 해협이 재개방되면서 페르시아만 알루미늄 공급 증가 가능성이 가격을 압박했습니다. 중국의 알루미늄 생산 확대 및 인도네시아 제련소 생산 증가도 하락을 가속했습니다. 6월 한 달간 LME 알루미늄은 약 16% 하락하며 2008년 이후 최대 월간 낙폭을 기록했습니다.',
        'sources': [{'title': 'Discovery Alert — LME Aluminium Price Falls Below $3,500', 'url': 'https://discoveryalert.com.au/lme-aluminium-price-below-3500-inventory-signals-2026/'}],
    },
    '2026-06-08': {
        'tag': '구리·주석 하락', 'tag_type': 'down',
        'body': '중동 지정학적 불확실성 지속과 중국 경기 둔화 우려로 비철금속 전반이 약세를 보였습니다. 주석은 5월 역대 최고가($59,000/t) 도달 이후 차익 실현 매물이 집중되며 조정 국면에 접어들었습니다.',
        'sources': [{'title': 'EBN — LME 비철금속 약세 흐름, 구리·주석 낙폭 확대', 'url': 'https://www.ebn.co.kr/news/articleView.html?idxno=1711562'}],
    },
    '2026-05-07': {
        'tag': '주석 급등', 'tag_type': 'up',
        'body': '인도네시아의 정제주석 수출량이 전년 동기 대비 40% 이상 급감했습니다(수출 허가 지연·불법채굴 단속 강화). AI 서버·반도체 납땜 수요가 구조적으로 증가하며 공급 부족이 심화됐습니다. LME 주석 재고는 사상 최저 수준으로 하락, 6월 2일 톤당 $59,000의 역대 최고가를 기록하는 랠리의 시작점이 됐습니다.',
        'sources': [
            {'title': 'Outlook Money — Tin Roars To New Record High', 'url': 'https://www.outlookmoney.com/commodities/tin-price-hits-record-high-rally-over-35-percent-in-2026-here-is-why'},
            {'title': 'BigGo Finance — Tin Prices Soar to Record Highs', 'url': 'https://finance.biggo.com/news/Cfsk6JsBZ4N-kGRr8eaG'},
        ],
    },
    '2026-05-12': {
        'tag': '비철금속 반등', 'tag_type': 'up',
        'body': '미-중 무역 협상 재개 기대감과 AI·데이터센터 관련 비철금속 수요 전망 개선으로 전반적인 반등세가 나타났습니다. 달러 약세 전환도 원자재 가격 상승에 기여했습니다.',
        'sources': [{'title': '킵뉴스 — 구리 가격 강세 재점화, AI·에너지 전환 수요', 'url': 'https://kidd.co.kr/news/244600'}],
    },
    '2026-04-09': {
        'tag': '관세 충격', 'tag_type': 'down',
        'body': '트럼프 행정부의 상호관세 발표로 글로벌 경기침체 우려가 극도로 높아지며 위험자산 전반에 대한 매도세가 집중됐습니다. 미국의 알루미늄·철강 50% 품목관세 정책이 글로벌 교역 위축 불안을 자극했습니다.',
        'sources': [{'title': 'CODIT — 트럼프 행정부의 알루미늄·구리 50% 관세와 한국의 대응', 'url': 'https://thecodit.com/blog/non-ferrous-metals-policy-kr'}],
    },
    '2026-03-09': {
        'tag': '알루미늄 급등', 'tag_type': 'up',
        'body': '미국 Section 232 알루미늄 관세의 50% 상향 확정 발표로 미국 수입업체들의 선매 수요가 급증했습니다. LME 현물가는 $3,520/t에 도달했으며, LME 창고 재고가 역사적 저점(27만 톤)으로 하락하며 공급 긴박감이 극대화됐습니다.',
        'sources': [
            {'title': 'Discovery Alert — LME Aluminium Price Surge $3,520', 'url': 'https://discoveryalert.com.au/lme-aluminium-price-increase-geopolitical-supply-constraints-2026/'},
            {'title': '한국경제 — 천장 뚫린 알루미늄값', 'url': 'https://www.hankyung.com/amp/2026041371345'},
        ],
    },
    '2026-03-04': {
        'tag': '주석 급락', 'tag_type': 'down',
        'body': '미얀마 와주(Wa State) 주석광산 수출 제한 완화 가능성이 보도되며 공급 우려가 일부 해소됐습니다. 고가(LME $50,000/t 이상) 부담에 따른 수요 억제 심리와 투기 세력의 단기 차익 실현 매물이 동시에 출회하며 낙폭이 확대됐습니다.',
        'sources': [{'title': 'International Tin Association — Tin Hits Nominal All-Time High', 'url': 'https://www.internationaltin.org/tin-hits-nominal-all-time-high/'}],
    },
    '2026-02-25': {
        'tag': '비철금속 급등', 'tag_type': 'up',
        'body': '미-러 우크라이나 종전 협상 기대감과 중국의 경기 부양책 발표가 맞물리며 비철금속 전반에 강한 매수세가 유입됐습니다. 주석은 인도네시아 수출 허가 지연이 지속되는 가운데 미국 관세 리스크가 겹치며 공급 우려가 재부각됐습니다.',
        'sources': [{'title': '철강금속신문 — 공급 차질 우려 커진 비철시장', 'url': 'https://www.snmnews.com/news/articleView.html?idxno=569187'}],
    },
    '2026-02-26': {
        'tag': '비철금속 급등', 'tag_type': 'up',
        'body': '전일(25일) 강세 흐름이 이어지며 주석이 추가 상승했습니다. 인도네시아 수출 허가 지연 장기화와 미국 관세 정책 불확실성이 공급 우려를 지속시켰습니다.',
        'sources': [{'title': '철강금속신문 — 공급 차질 우려 커진 비철시장', 'url': 'https://www.snmnews.com/news/articleView.html?idxno=569187'}],
    },
    '2026-02-03': {
        'tag': '주석·니켈 급락', 'tag_type': 'down',
        'body': '주석 펀드 순매수 포지션이 12월 고점(5,144 lot)에서 2,239 lot으로 대폭 축소되며 투기 세력의 차익 실현 매물이 집중됐습니다. 미얀마 주석 수출 재개 가능성이 대두되며 공급 우려도 일부 해소됐습니다. 니켈은 인도네시아 과잉 공급 구조가 지속되며 동반 약세를 보였습니다.',
        'sources': [{'title': 'Fastmarkets — Monthly Base Metals Market Update 2026', 'url': 'https://www.fastmarkets.com/metals-and-mining/base-metals/monthly-base-metals-market-update-2026/'}],
    },
    '2026-01-26': {
        'tag': '주석 역대 최고가', 'tag_type': 'up',
        'body': 'LME 주석 3개월물이 $51,500/t을 돌파하며 월간 26.1% 상승했습니다. ① 콩고(DRC) Bisie 광산 가동 중단, ② 미얀마 와주 채굴 제한, ③ 인도네시아 수출 허가 지연(정상 대비 20~30% 감소)이라는 3중 공급 차질이 발생했습니다. AI 서버, 전기차, 태양광 납땜 수요 급증이 겹치며 역대 최고가를 경신했습니다.',
        'sources': [
            {'title': 'SunSirs — Tin Prices Surge Over 25% Since Start of 2026', 'url': 'https://www.sunsirs.com/uk/detail_news-30029.html'},
            {'title': 'Coface — Data demand sends tin surging', 'url': 'https://www.coface.com/news-economy-and-insights/tin-is-riding-high-on-the-metals-market-s-latest-surge'},
        ],
    },
    '2026-01-19': {
        'tag': '비철금속 급락', 'tag_type': 'down',
        'body': '주석이 $50,000/t을 상회하며 수요 억제 심리가 확산됐습니다. 거시경제 역풍(고금리 장기화 우려, 달러 강세)으로 전반적인 차익 실현 매물이 출회됐습니다. 니켈은 인도네시아 구조적 과잉 공급이 지속되는 가운데 단기 과매수 포지션이 해소되며 낙폭이 컸습니다.',
        'sources': [
            {'title': 'Shanghai Metals Market — 비철금속 전반 하락', 'url': 'https://news.metal.com/ko/newscontent/103946323'},
            {'title': 'CNews — 비철금속 공급측 요인 강세 기조', 'url': 'https://www.thecommoditiesnews.com/news/articleView.html?idxno=10255'},
        ],
    },
}

THRESHOLD_DAY = 2.0  # % daily change threshold
SKIP_ABS = 50.0      # skip anomalies (data gaps show as ±100%)

def fmt_date(d):
    dt = datetime.strptime(d, '%Y-%m-%d')
    return f"{str(dt.year)[2:]}년 {dt.month:02d}월 {dt.day:02d}일"

def run():
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r['date'])

    cutoff = (datetime.now() - timedelta(days=183)).strftime('%Y-%m-%d')
    recent = [r for r in rows if r['date'] >= cutoff]

    # Find significant daily changes grouped by date
    events = {}  # date -> list of {name, diff, pct, direction}
    for i in range(1, len(recent)):
        today = recent[i]
        prev  = recent[i - 1]
        date  = today['date']
        for name, col in METALS:
            try:
                t = int(today[col]); p = int(prev[col])
            except (ValueError, KeyError):
                continue
            if p == 0: continue
            pct = (t - p) / p * 100
            if abs(pct) >= THRESHOLD_DAY and abs(pct) < SKIP_ABS:
                if date not in events:
                    events[date] = []
                events[date].append({
                    'name': name,
                    'diff': abs(t - p),
                    'pct': round(pct, 1),
                    'direction': 'up' if pct > 0 else 'down',
                })

    # Build issue list newest-first
    issues = []
    for date in sorted(events.keys(), reverse=True):
        items = events[date]
        summ = SUMMARIES.get(date, {})

        # Auto-determine tag if no summary
        if not summ:
            downs = sum(1 for x in items if x['direction'] == 'down')
            ups   = sum(1 for x in items if x['direction'] == 'up')
            if downs > 0 and ups == 0:
                tag, tag_type = '가격 하락', 'down'
            elif ups > 0 and downs == 0:
                tag, tag_type = '가격 상승', 'up'
            else:
                tag, tag_type = '혼조세', 'mixed'
        else:
            tag      = summ.get('tag', '')
            tag_type = summ.get('tag_type', 'mixed')

        issues.append({
            'date':     date,
            'date_fmt': fmt_date(date),
            'tag':      tag,
            'tag_type': tag_type,
            'items':    items,
            'body':     summ.get('body', ''),
            'sources':  summ.get('sources', []),
        })

    now = datetime.now()
    latest_date = max(events.keys()) if events else '-'
    generated   = now.strftime('%Y-%m-%d %H:%M')

    js = f"const ISSUES_META = {json.dumps({'latest': latest_date, 'generated': generated}, ensure_ascii=False)};\n"
    js += f"const ISSUES_DATA = {json.dumps(issues, ensure_ascii=False, indent=2)};\n"

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f"Issues written: {len(issues)} events → {OUT_PATH}")

if __name__ == '__main__':
    run()
