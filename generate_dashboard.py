"""
Generate a self-contained dashboard.html from data/prices.csv.
Run this script whenever the CSV is updated.
"""

import csv
import json
import os
from datetime import datetime

CSV_PATH  = os.path.join(os.path.dirname(__file__), "data", "prices.csv")
OUT_PATH  = os.path.join(os.path.dirname(__file__), "dashboard.html")

MATERIALS = [
    {"key": "알루미늄_서구산",  "label": "알루미늄(서구산)",   "col": 1},
    {"key": "알루미늄_비서구산","label": "알루미늄(비서구산)", "col": 3},
    {"key": "구리",             "label": "구리(99.99%이상)",   "col": 5},
    {"key": "납",               "label": "납(99.99%이상)",     "col": 7},
    {"key": "아연",             "label": "아연",               "col": 9},
    {"key": "주석_9985",        "label": "주석(99.85%이상)",   "col": 11},
    {"key": "주석_9999",        "label": "주석(99.99%이상)",   "col": 13},
    {"key": "니켈_합금",        "label": "니켈(합금용)",       "col": 15},
    {"key": "니켈_도금",        "label": "니켈(도금용)",       "col": 17},
]

COLORS = [
    "#3B82F6","#EF4444","#10B981","#F59E0B",
    "#8B5CF6","#EC4899","#14B8A6","#F97316","#6366F1",
]

def load_csv():
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if not row or not row[0]:
                continue
            entry = {"date": row[0]}
            for m in MATERIALS:
                ci = m["col"]
                try:
                    entry[m["key"] + "_excl"] = int(row[ci])     if row[ci]   else None
                    entry[m["key"] + "_incl"] = int(row[ci + 1]) if row[ci+1] else None
                except (ValueError, IndexError):
                    entry[m["key"] + "_excl"] = None
                    entry[m["key"] + "_incl"] = None
            rows.append(entry)
    # sort ascending by date
    rows.sort(key=lambda r: r["date"])
    return rows

def build_html(rows):
    data_json = json.dumps(rows, ensure_ascii=False)
    materials_json = json.dumps(MATERIALS, ensure_ascii=False)
    colors_json = json.dumps(COLORS)
    last_date = rows[-1]["date"] if rows else "-"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>조달청 비철금속 판매가격 대시보드</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Pretendard", "Noto Sans KR", sans-serif; background: #F8FAFC; color: #1E293B; font-size: 14px; }}
  header {{ background: #1E3A5F; color: white; padding: 18px 28px; display: flex; justify-content: space-between; align-items: center; }}
  header h1 {{ font-size: 20px; font-weight: 700; }}
  header span {{ font-size: 12px; opacity: 0.7; }}
  .main {{ max-width: 1400px; margin: 0 auto; padding: 20px 20px 40px; }}

  /* Summary cards */
  .cards {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
  .card {{ background: white; border-radius: 10px; padding: 12px 16px; box-shadow: 0 1px 4px rgba(0,0,0,.08); cursor: pointer; border: 2px solid transparent; transition: border-color .15s; flex: 0 0 auto; min-width: 140px; }}
  .card.active {{ border-color: var(--c); }}
  .card-label {{ font-size: 12px; color: #64748B; margin-bottom: 4px; }}
  .card-price {{ font-size: 20px; font-weight: 700; color: #1E293B; }}
  .card-unit {{ font-size: 11px; color: #94A3B8; margin-left: 2px; }}
  .card-change {{ font-size: 12px; margin-top: 4px; }}
  .up {{ color: #EF4444; }} .dn {{ color: #3B82F6; }} .nc {{ color: #94A3B8; }}

  /* Controls */
  .controls {{ background: white; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }}
  .controls label {{ font-size: 12px; color: #64748B; margin-right: 6px; font-weight: 600; }}
  .controls input[type=date] {{ border: 1px solid #E2E8F0; border-radius: 6px; padding: 5px 10px; font-size: 13px; color: #1E293B; }}
  .btn-group {{ display: flex; gap: 6px; }}
  .btn {{ padding: 5px 14px; border-radius: 6px; border: 1px solid #E2E8F0; background: white; cursor: pointer; font-size: 12px; color: #475569; transition: all .15s; }}
  .btn:hover {{ background: #F1F5F9; }}
  .btn.active {{ background: #1E3A5F; color: white; border-color: #1E3A5F; }}
  .vat-toggle {{ display: flex; background: #F1F5F9; border-radius: 8px; padding: 3px; }}
  .vat-btn {{ padding: 5px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 12px; color: #64748B; background: transparent; transition: all .15s; }}
  .vat-btn.active {{ background: white; color: #1E293B; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}

  /* Chart */
  .chart-wrap {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 16px; position: relative; }}
  .chart-container {{ position: relative; width: 100%; height: 420px; }}
  .chart-wrap canvas {{ position: absolute; inset: 0; }}
  .chart-hint {{ position: absolute; top: 14px; right: 18px; font-size: 11px; color: #94A3B8; }}

  /* Table */
  .table-wrap {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow-x: auto; }}
  .table-wrap h2 {{ font-size: 14px; font-weight: 700; margin-bottom: 14px; color: #1E293B; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #F8FAFC; padding: 8px 12px; text-align: right; color: #64748B; font-weight: 600; white-space: nowrap; border-bottom: 2px solid #E2E8F0; }}
  th:first-child {{ text-align: left; }}
  td {{ padding: 7px 12px; text-align: right; border-bottom: 1px solid #F1F5F9; white-space: nowrap; }}
  td:first-child {{ text-align: left; font-weight: 600; color: #334155; }}
  tr:hover td {{ background: #F8FAFC; }}
  .empty {{ color: #CBD5E1; }}
</style>
</head>
<body>
<header>
  <h1>조달청 비철금속 원자재 판매가격</h1>
  <span>최근 데이터: {last_date} &nbsp;|&nbsp; 생성: {generated_at}</span>
</header>
<div class="main">
  <div class="cards" id="cards"></div>
  <div class="controls" style="flex-direction:column; align-items:stretch; gap:10px;">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
      <label>기간</label>
      <input type="date" id="dateFrom">
      <span style="margin:0 4px;color:#94A3B8">~</span>
      <input type="date" id="dateTo">
      <div class="btn-group" id="rangeButtons">
        <button class="btn" data-range="1">1개월</button>
        <button class="btn" data-range="3">3개월</button>
        <button class="btn" data-range="6">6개월</button>
        <button class="btn active" data-range="12">1년</button>
        <button class="btn" data-range="36">3년</button>
        <button class="btn" data-range="all">전체</button>
      </div>
      <div class="btn-group" id="granButtons" style="margin-left:auto;">
        <button class="btn active" data-gran="day">일기준</button>
        <button class="btn" data-gran="month">월기준</button>
        <button class="btn" data-gran="quarter">분기기준</button>
      </div>
    </div>
    <div style="display:flex; align-items:center; gap:12px; justify-content:flex-end;">
      <label>가격 기준</label>
      <div class="vat-toggle">
        <button class="vat-btn" id="btnIncl">부가세 포함</button>
        <button class="vat-btn active" id="btnExcl">부가세 제외</button>
      </div>
    </div>
  </div>
  <div class="chart-wrap">
    <span class="chart-hint">마우스 휠: 확대/축소 &nbsp;|&nbsp; 드래그: 이동 &nbsp;|&nbsp; 더블클릭: 초기화</span>
    <div class="chart-container"><canvas id="chart"></canvas></div>
  </div>
  <div class="controls" style="flex-direction:column; align-items:stretch; gap:10px;">
    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
      <label>기간</label>
      <input type="date" id="tableDateFrom">
      <span style="margin:0 4px;color:#94A3B8">~</span>
      <input type="date" id="tableDateTo">
      <div class="btn-group" id="tableRangeButtons">
        <button class="btn" data-trange="1">1개월</button>
        <button class="btn" data-trange="3">3개월</button>
        <button class="btn" data-trange="6">6개월</button>
        <button class="btn active" data-trange="12">1년</button>
        <button class="btn" data-trange="36">3년</button>
        <button class="btn" data-trange="all">전체</button>
      </div>
      <div class="btn-group" id="tableGranButtons" style="margin-left:auto;">
        <button class="btn active" data-tgran="day">일기준</button>
        <button class="btn" data-tgran="month">월기준</button>
        <button class="btn" data-tgran="quarter">분기기준</button>
      </div>
    </div>
    <div style="display:flex; align-items:center; gap:12px; justify-content:flex-end;">
      <label>가격 기준</label>
      <div class="vat-toggle">
        <button class="vat-btn" id="tableBtnIncl">부가세 포함</button>
        <button class="vat-btn active" id="tableBtnExcl">부가세 제외</button>
      </div>
    </div>
  </div>
  <div class="table-wrap">
    <table id="dataTable"></table>
  </div>
</div>

<script>
const ALL_DATA = {data_json};
const MATERIALS = {materials_json};
const COLORS = {colors_json};

// State
let vatMode = 'excl';
let activeGrans = new Set(['day']);  // single granularity at a time
let activeKeys = new Set(['알루미늄_서구산']);
let dateFrom = null;
let dateTo = null;

// Init
const lastRow = ALL_DATA[ALL_DATA.length - 1];
const firstDate = ALL_DATA[0]?.date ?? '';
const lastDate  = lastRow?.date ?? '';

// Default range: 1 year
const d1y = new Date(lastDate);
d1y.setMonth(d1y.getMonth() - 12);
dateFrom = d1y.toISOString().slice(0, 10);
dateTo   = lastDate;
document.getElementById('dateFrom').value = dateFrom;
document.getElementById('dateTo').value   = dateTo;

// ── Cards ──────────────────────────────────────────────────────────────────
function buildCards() {{
  const container = document.getElementById('cards');
  container.innerHTML = '';
  const prev = ALL_DATA.length >= 2 ? ALL_DATA[ALL_DATA.length - 2] : null;

  MATERIALS.forEach((m, i) => {{
    const suffix = vatMode === 'incl' ? '_incl' : '_excl';
    const cur  = lastRow?.[m.key + suffix];
    const prv  = prev?.[m.key + suffix];
    const diff = (cur != null && prv != null) ? cur - prv : null;
    const pct  = (diff != null && prv) ? (diff / prv * 100).toFixed(1) : null;

    let changeHtml = '';
    if (diff != null) {{
      const cls = diff > 0 ? 'up' : diff < 0 ? 'dn' : 'nc';
      const sign = diff > 0 ? '▲' : diff < 0 ? '▼' : '―';
      changeHtml = `<div class="card-change ${{cls}}">${{sign}} ${{Math.abs(diff).toLocaleString()}}원 (${{pct}}%)</div>`;
    }}

    const card = document.createElement('div');
    card.className = 'card' + (activeKeys.has(m.key) ? ' active' : '');
    card.style.setProperty('--c', COLORS[i]);
    card.style.borderColor = activeKeys.has(m.key) ? COLORS[i] : 'transparent';
    card.innerHTML = `
      <div class="card-label">${{m.label}}</div>
      <div class="card-price">${{cur != null ? cur.toLocaleString() : '-'}}<span class="card-unit">원/kg</span></div>
      ${{changeHtml}}
    `;
    card.addEventListener('click', () => toggleMaterial(m.key, i, card));
    container.appendChild(card);
  }});
}}

function toggleMaterial(key, idx, card) {{
  if (activeKeys.has(key)) {{
    if (activeKeys.size === 1) return;
    activeKeys.delete(key);
    card.style.borderColor = 'transparent';
    card.classList.remove('active');
  }} else {{
    activeKeys.add(key);
    card.style.borderColor = COLORS[idx];
    card.classList.add('active');
  }}
  updateChart();
}}

// ── Aggregation ────────────────────────────────────────────────────────────

function periodKey(date, gran) {{
  // Returns ISO date strings usable by time scale
  if (gran === 'day') return date;                           // 'YYYY-MM-DD'
  if (gran === 'month') return date.slice(0, 7) + '-01';    // 'YYYY-MM-01'
  if (gran === 'quarter') {{
    const m = parseInt(date.slice(5, 7));
    const qStart = [1, 1, 1, 4, 4, 4, 7, 7, 7, 10, 10, 10][m - 1];
    return date.slice(0, 4) + '-' + String(qStart).padStart(2, '0') + '-01'; // 'YYYY-Q#-01'
  }}
}}

function periodLabel(date, gran) {{
  // Human-readable label for tooltips/table
  if (gran === 'day')     return date;
  if (gran === 'month')   return date.slice(0, 7);
  if (gran === 'quarter') {{
    const m = parseInt(date.slice(5, 7));
    const q = Math.ceil(m / 3);
    return date.slice(0, 4) + '-Q' + q;
  }}
}}

function aggregateData(rows, gran) {{
  if (gran === 'day') return rows;

  const keys = MATERIALS.flatMap(m => [m.key + '_excl', m.key + '_incl']);

  // Step 1: compute period averages
  const groups = new Map();
  for (const row of rows) {{
    const pk = periodKey(row.date, gran);
    if (!groups.has(pk)) groups.set(pk, {{ sums: {{}}, counts: {{}} }});
    const g = groups.get(pk);
    for (const k of keys) {{
      if (row[k] != null) {{
        g.sums[k]   = (g.sums[k]   ?? 0) + row[k];
        g.counts[k] = (g.counts[k] ?? 0) + 1;
      }}
    }}
  }}
  const avgMap = {{}};
  for (const [pk, g] of groups) {{
    avgMap[pk] = {{}};
    for (const k of keys) {{
      avgMap[pk][k] = g.counts[k] ? Math.round(g.sums[k] / g.counts[k]) : null;
    }}
  }}

  // Step 2: fill every original day with its period average
  return rows.map(row => {{
    const pk  = periodKey(row.date, gran);
    const avg = avgMap[pk] ?? {{}};
    const entry = {{ date: row.date }};
    for (const k of keys) entry[k] = avg[k] ?? null;
    return entry;
  }});
}}

// ── Chart ──────────────────────────────────────────────────────────────────
let chart = null;

function filteredData(gran) {{
  const raw = ALL_DATA.filter(r => r.date >= dateFrom && r.date <= dateTo);
  return aggregateData(raw, gran);
}}

function allData(gran) {{
  const keys = MATERIALS.flatMap(m => [m.key+'_excl', m.key+'_incl']);
  const filled = [];
  const cur = new Date(firstDate);
  const end = new Date(lastDate);

  if (gran === 'day') {{
    // Fill all calendar dates; trading days get real values, others get null
    const dataMap = {{}};
    ALL_DATA.forEach(r => {{ dataMap[r.date] = r; }});
    while (cur <= end) {{
      const ds = cur.toISOString().slice(0, 10);
      const row = {{ date: ds }};
      keys.forEach(k => row[k] = dataMap[ds]?.[k] ?? null);
      filled.push(row);
      cur.setDate(cur.getDate() + 1);
    }}
    return filled;
  }}

  // Month / Quarter: compute period averages from trading days,
  // then fill EVERY calendar day so steps start on the 1st of each period
  const agg = aggregateData(ALL_DATA, gran);
  const periodAvgMap = {{}};  // periodKey (YYYY-MM-01 / YYYY-Q-01) -> {{key: avg}}
  agg.forEach(r => {{
    const pk = periodKey(r.date, gran);
    if (!periodAvgMap[pk]) periodAvgMap[pk] = {{}};
    keys.forEach(k => {{ if (r[k] != null) periodAvgMap[pk][k] = r[k]; }});
  }});

  while (cur <= end) {{
    const ds = cur.toISOString().slice(0, 10);
    const pk = periodKey(ds, gran);
    const avg = periodAvgMap[pk] ?? {{}};
    const row = {{ date: ds }};
    keys.forEach(k => row[k] = avg[k] ?? null);
    filled.push(row);
    cur.setDate(cur.getDate() + 1);
  }}
  return filled;
}}

function buildChart() {{
  const ctx = document.getElementById('chart').getContext('2d');
  const suffix = vatMode === 'incl' ? '_incl' : '_excl';

  const GRAN_CFG = {{
    day:     {{ alpha: '20', bw: 1.5, tension: 0.3, stepped: false, dash: [],  spanGaps: true  }},

    month:   {{ alpha: '15', bw: 2,   tension: 0,   stepped: true,  dash: [],      spanGaps: false }},
    quarter: {{ alpha: '15', bw: 2.5, tension: 0,   stepped: true,  dash: [6, 3], spanGaps: false }},
  }};
  const granLabel = {{ day: '일', month: '월평균', quarter: '분기평균' }};
  const hasDay    = activeGrans.has('day');
  const hasNonDay = activeGrans.has('month') || activeGrans.has('quarter');
  const multiGran = activeGrans.size > 1;
  // Category scale only when no day is active (equal-width steps)
  const useCatScale = hasNonDay && !hasDay;
  // For category scale: use finest non-day gran for label generation
  const catGran = activeGrans.has('month') ? 'month' : 'quarter';
  window.activeGran = [...activeGrans][0];

  // Build category labels using month as the common axis.
  // Quarter data is mapped to its starting month label so both share one consistent axis.
  let catLabels = [];
  const catByGranKey = {{}};
  if (useCatScale) {{
    // Always build month-based labels as the x-axis foundation
    const axisGran = 'month';
    const monthByPeriod = {{}};
    ALL_DATA.forEach(r => {{
      const pk = periodLabel(r.date, 'month');
      if (!monthByPeriod[pk]) monthByPeriod[pk] = {{ sums: {{}}, counts: {{}} }};
      const g = monthByPeriod[pk];
      MATERIALS.forEach(m => {{
        ['_excl','_incl'].forEach(s => {{
          const v = r[m.key+s];
          if (v != null) {{ g.sums[m.key+s] = (g.sums[m.key+s]??0)+v; g.counts[m.key+s] = (g.counts[m.key+s]??0)+1; }}
        }});
      }});
    }});
    catByGranKey['month'] = monthByPeriod;
    catLabels = Object.keys(monthByPeriod).sort();

    // For quarter: aggregate by quarter, then store at the quarter's starting month label
    if (activeGrans.has('quarter')) {{
      const qByPeriod = {{}};
      ALL_DATA.forEach(r => {{
        const mo = parseInt(r.date.slice(5,7));
        const qStartMo = [1,1,1,4,4,4,7,7,7,10,10,10][mo-1];
        const pk = r.date.slice(0,4) + '-' + String(qStartMo).padStart(2,'0');
        if (!qByPeriod[pk]) qByPeriod[pk] = {{ sums: {{}}, counts: {{}} }};
        const g = qByPeriod[pk];
        MATERIALS.forEach(m => {{
          ['_excl','_incl'].forEach(s => {{
            const v = r[m.key+s];
            if (v != null) {{ g.sums[m.key+s] = (g.sums[m.key+s]??0)+v; g.counts[m.key+s] = (g.counts[m.key+s]??0)+1; }}
          }});
        }});
      }});
      catByGranKey['quarter'] = qByPeriod;
    }}

    // Phantom: add one extra month beyond last so step extends to right edge
    const lastLbl = catLabels[catLabels.length - 1];
    const [ly, lm] = lastLbl.split('-').map(Number);
    const nd = new Date(ly, lm, 1);
    catLabels.push(`${{nd.getFullYear()}}-${{String(nd.getMonth()+1).padStart(2,'0')}}`);
  }}

  const datasets = [];
  for (const gran of ['day', 'month', 'quarter']) {{
    if (!activeGrans.has(gran)) continue;
    const cfg = GRAN_CFG[gran];
    let dataFn;
    let ptRadius = 0;

    if (useCatScale) {{
      const byPeriod = catByGranKey[gran];
      dataFn = m => {{
        const k = m.key + suffix;
        const vals = catLabels.map(pk => {{
          let lookupKey = pk;
          if (gran === 'quarter') {{
            // Map every month to its quarter-start month key
            const [y, mo] = pk.split('-').map(Number);
            const qStart = [1,1,1,4,4,4,7,7,7,10,10,10][mo-1];
            lookupKey = `${{y}}-${{String(qStart).padStart(2,'0')}}`;
          }}
          const g = byPeriod[lookupKey];
          return g?.counts[k] ? Math.round(g.sums[k] / g.counts[k]) : null;
        }});
        return vals;
      }};
    }} else {{
      const fd = allData(gran);
      ptRadius = (gran === 'day' && fd.length > 200) ? 0 : (gran === 'day' ? 2 : 0);
      dataFn = m => fd.map(r => ({{ x: r.date, y: r[m.key + suffix] ?? null }}));
    }}

    MATERIALS.filter(m => activeKeys.has(m.key)).forEach(m => {{
      const colorIdx = MATERIALS.indexOf(m);
      const color = COLORS[colorIdx];
      datasets.push({{
        type: 'line',
        label: multiGran ? `${{m.label}} (${{granLabel[gran]}})` : m.label,
        data: dataFn(m),
        borderColor: color,
        backgroundColor: color + cfg.alpha,
        borderWidth: cfg.bw,
        borderDash: cfg.dash,
        pointRadius: ptRadius,
        tension: cfg.tension,
        stepped: cfg.stepped,
        spanGaps: cfg.spanGaps ?? false,
      }});
    }});
  }}

  // Determine initial view boundaries and pan limits
  // catLabels is always month-based, so viewMin must also use month labels
  const viewMin = useCatScale ? periodLabel(dateFrom, 'month') : dateFrom;
  const viewMax = useCatScale ? catLabels[catLabels.length - 1] : dateTo;
  const dataFirst = ALL_DATA[0]?.date ?? '2012-01-06';
  const dataLast  = ALL_DATA[ALL_DATA.length - 1]?.date ?? dateTo;
  const panMin = useCatScale ? 0 : new Date(dataFirst).getTime();
  const panMax = useCatScale ? catLabels.length - 1 : new Date(dataLast).getTime();

  const xScale = useCatScale ? {{
    type: 'category',
    min: viewMin,
    max: viewMax,
    ticks: {{ maxTicksLimit: 14, font: {{ size: 11 }} }},
    grid: {{ display: false }},
    offset: true,
  }} : {{
    type: 'time',
    min: viewMin,
    max: viewMax,
    time: {{ unit: 'day', tooltipFormat: 'yyyy-MM-dd', displayFormats: {{ day: 'yy-MM-dd' }} }},
    ticks: {{ maxTicksLimit: 14, font: {{ size: 11 }} }},
    grid: {{ display: false }},
    offset: true,
  }};

  if (chart) chart.destroy();
  chart = new Chart(ctx, {{
    type: 'line',
    data: useCatScale ? {{ labels: catLabels, datasets }} : {{ datasets }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'top', labels: {{ font: {{ size: 12 }}, boxWidth: 12 }} }},
        tooltip: {{
          callbacks: {{
            title: items => items[0]?.label ?? '',
            label: c => ` ${{c.dataset.label}}: ${{c.parsed.y?.toLocaleString()}}원/kg`,
          }}
        }},
        zoom: {{
          zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, mode: 'x' }},
          pan:  {{ enabled: true, mode: 'x' }},
          limits: {{ x: {{ min: panMin, max: panMax }} }},
        }},
      }},
      scales: {{ x: xScale, y: {{
        afterDataLimits: axis => {{ axis.min -= 1000; axis.max += 1000; }},
        ticks: {{ callback: v => v.toLocaleString(), font: {{ size: 11 }} }},
        grid: {{ color: '#F1F5F9' }},
      }} }},
    }},
  }});
  chart.canvas.ondblclick = () => {{ chart.resetZoom(); }};

  // Resize chart when container size changes (handles window grow)
  if (window._chartResizeObserver) window._chartResizeObserver.disconnect();
  window._chartResizeObserver = new ResizeObserver(() => {{ if (chart) chart.resize(); }});
  window._chartResizeObserver.observe(document.querySelector('.chart-container'));
}}

function updateChart() {{
  buildChart();
}}

// ── Table ──────────────────────────────────────────────────────────────────
// Table date range (independent from chart)
const initTableTo   = lastDate;
const initTableFrom = (() => {{ const d = new Date(lastDate); d.setMonth(d.getMonth() - 12); return d.toISOString().slice(0,10); }})();
let tableDateFrom = initTableFrom;
let tableDateTo   = initTableTo;

function tableFilteredData(gran) {{
  const raw = ALL_DATA.filter(r => r.date >= tableDateFrom && r.date <= tableDateTo);
  const keys = MATERIALS.flatMap(m => [m.key+'_excl', m.key+'_incl']);

  if (gran === 'day') {{
    // Fill all calendar dates including weekends/holidays
    const dataMap = {{}};
    raw.forEach(r => {{ dataMap[r.date] = r; }});
    const emptyRow = date => {{ const r = {{ date }}; keys.forEach(k => r[k] = null); return r; }};
    const filled = [];
    const cur = new Date(tableDateFrom);
    const end = new Date(tableDateTo);
    while (cur <= end) {{
      const ds = cur.toISOString().slice(0, 10);
      filled.push(dataMap[ds] ?? emptyRow(ds));
      cur.setDate(cur.getDate() + 1);
    }}
    return filled;
  }}

  // Month / Quarter: one row per period with averaged values
  const groups = {{}};
  raw.forEach(r => {{
    const pk = periodLabel(r.date, gran);
    if (!groups[pk]) groups[pk] = {{ sums: {{}}, counts: {{}} }};
    const g = groups[pk];
    keys.forEach(k => {{
      const v = r[k];
      if (v != null) {{ g.sums[k] = (g.sums[k]??0)+v; g.counts[k] = (g.counts[k]??0)+1; }}
    }});
  }});
  return Object.keys(groups).sort().map(pk => {{
    const g = groups[pk];
    const row = {{ date: pk }};
    keys.forEach(k => {{ row[k] = g.counts[k] ? Math.round(g.sums[k]/g.counts[k]) : null; }});
    return row;
  }});
}}

let tableGran    = 'day';
let tableVatMode = 'excl';

function buildTable() {{
  const table = document.getElementById('dataTable');
  const gran   = tableGran;
  const suffix = tableVatMode === 'incl' ? '_incl' : '_excl';

  const recent = [...tableFilteredData(gran)].reverse();

  const thead = '<thead><tr><th>날짜</th>' +
    MATERIALS.map(m => `<th>${{m.label}}</th>`).join('') +
    '</tr></thead>';

  const tbody = '<tbody>' + recent.map(r => {{
    const cells = MATERIALS.map(m => {{
      const v = r[m.key + suffix];
      return `<td>${{v != null ? v.toLocaleString() : '<span class="empty">-</span>'}}</td>`;
    }}).join('');
    const dateLabel = gran === 'day' ? r.date : r.date;
    return `<tr><td>${{dateLabel}}</td>${{cells}}</tr>`;
  }}).join('') + '</tbody>';

  table.innerHTML = thead + tbody;
}}

// ── Event Wiring ───────────────────────────────────────────────────────────
document.getElementById('dateFrom').addEventListener('change', e => {{
  dateFrom = e.target.value;
  clearRangeButton();
  updateChart();
}});
document.getElementById('dateTo').addEventListener('change', e => {{
  dateTo = e.target.value;
  clearRangeButton();
  updateChart();
}});

document.getElementById('rangeButtons').addEventListener('click', e => {{
  const btn = e.target.closest('[data-range]');
  if (!btn) return;
  document.querySelectorAll('#rangeButtons .btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const range = btn.dataset.range;
  dateTo = lastDate;
  if (range === 'all') {{
    dateFrom = firstDate;
  }} else {{
    const d = new Date(lastDate);
    d.setMonth(d.getMonth() - parseInt(range));
    dateFrom = d.toISOString().slice(0, 10);
  }}
  document.getElementById('dateFrom').value = dateFrom;
  document.getElementById('dateTo').value   = dateTo;
  updateChart();
}});

function clearRangeButton() {{
  document.querySelectorAll('#rangeButtons .btn').forEach(b => b.classList.remove('active'));
}}

// Init table date inputs
document.getElementById('tableDateFrom').value = initTableFrom;
document.getElementById('tableDateTo').value   = initTableTo;

document.getElementById('tableDateFrom').addEventListener('change', e => {{
  tableDateFrom = e.target.value;
  clearTableRangeButton();
  buildTable();
}});
document.getElementById('tableDateTo').addEventListener('change', e => {{
  tableDateTo = e.target.value;
  clearTableRangeButton();
  buildTable();
}});

document.getElementById('tableRangeButtons').addEventListener('click', e => {{
  const btn = e.target.closest('[data-trange]');
  if (!btn) return;
  document.querySelectorAll('#tableRangeButtons .btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  tableDateTo = lastDate;
  if (btn.dataset.trange === 'all') {{
    tableDateFrom = firstDate;
  }} else {{
    const d = new Date(lastDate);
    d.setMonth(d.getMonth() - parseInt(btn.dataset.trange));
    tableDateFrom = d.toISOString().slice(0, 10);
  }}
  document.getElementById('tableDateFrom').value = tableDateFrom;
  document.getElementById('tableDateTo').value   = tableDateTo;
  buildTable();
}});

function clearTableRangeButton() {{
  document.querySelectorAll('#tableRangeButtons .btn').forEach(b => b.classList.remove('active'));
}}

document.getElementById('tableGranButtons').addEventListener('click', e => {{
  const btn = e.target.closest('[data-tgran]');
  if (!btn) return;
  tableGran = btn.dataset.tgran;
  document.querySelectorAll('#tableGranButtons [data-tgran]').forEach(b => {{
    b.classList.toggle('active', b.dataset.tgran === tableGran);
  }});
  buildTable();
}});

document.getElementById('tableBtnIncl').addEventListener('click', () => {{
  tableVatMode = 'incl';
  document.getElementById('tableBtnIncl').classList.add('active');
  document.getElementById('tableBtnExcl').classList.remove('active');
  buildTable();
}});
document.getElementById('tableBtnExcl').addEventListener('click', () => {{
  tableVatMode = 'excl';
  document.getElementById('tableBtnExcl').classList.add('active');
  document.getElementById('tableBtnIncl').classList.remove('active');
  buildTable();
}});

document.getElementById('granButtons').addEventListener('click', e => {{
  const btn = e.target.closest('[data-gran]');
  if (!btn) return;
  const gran = btn.dataset.gran;
  if (activeGrans.has(gran)) {{
    if (activeGrans.size === 1) return;  // at least one must stay active
    activeGrans.delete(gran);
    btn.classList.remove('active');
  }} else {{
    activeGrans.add(gran);
    btn.classList.add('active');
  }}
  updateChart();
}});

document.getElementById('btnIncl').addEventListener('click', () => {{
  vatMode = 'incl';
  document.getElementById('btnIncl').classList.add('active');
  document.getElementById('btnExcl').classList.remove('active');
  buildCards(); buildChart(); buildTable();
}});
document.getElementById('btnExcl').addEventListener('click', () => {{
  vatMode = 'excl';
  document.getElementById('btnExcl').classList.add('active');
  document.getElementById('btnIncl').classList.remove('active');
  buildCards(); buildChart(); buildTable();
}});

// ── Init ───────────────────────────────────────────────────────────────────
buildCards();
buildChart();
buildTable();
</script>
</body>
</html>
"""

def main():
    print("Loading CSV…")
    rows = load_csv()
    print(f"  {len(rows)} rows loaded")
    html = build_html(rows)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written to: {OUT_PATH}")

if __name__ == "__main__":
    main()
