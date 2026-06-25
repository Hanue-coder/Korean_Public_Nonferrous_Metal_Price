import urllib.request, re, ssl, csv, os, subprocess
from datetime import datetime

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

results = []

# 1. Check scheduled task
r = subprocess.run(
    ["schtasks", "/Query", "/TN", "비철금속가격_자동업데이트", "/FO", "LIST", "/V"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
task_out = r.stdout
repeat = "Repeat: Every:" in task_out and "Disabled" not in task_out.split("Repeat: Every:")[1].split("\n")[0]
logon_mode = [l for l in task_out.splitlines() if "Logon Mode" in l]
last_result = [l for l in task_out.splitlines() if "Last Result" in l]
results.append(("예약 작업 반복 실행", "OK" if repeat else "FAIL", "1시간 반복이 비활성화되어 있음 — 하루 1회(9시)만 실행"))
results.append(("예약 작업 로그온 모드", "WARN", logon_mode[0].strip() if logon_mode else "?"))
results.append(("마지막 실행 결과", "FAIL" if "-196608" in (last_result[0] if last_result else "") else "OK",
                last_result[0].strip() if last_result else "?"))

# 2. Check Python path
py = "C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"
results.append(("Python 경로", "OK" if os.path.exists(py) else "FAIL", py))

# 3. Check CSV latest date
csv_path = os.path.join(os.path.dirname(__file__), "data", "prices.csv")
latest = "-"
if os.path.exists(csv_path):
    with open(csv_path, encoding="utf-8-sig") as f:
        dates = [r["date"] for r in csv.DictReader(f) if r.get("date")]
    latest = max(dates) if dates else "-"
today = datetime.now().strftime("%Y-%m-%d")
results.append(("CSV 최신 날짜", "OK" if latest == today else "WARN",
                f"{latest} (오늘: {today})"))

# 4. Check scraper can reach 조달청
try:
    url = "https://www.pps.go.kr/bichuk/bbs/list.do?key=00825&pageIndex=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    sns = re.findall(r"goView\('(\d+)'\)", html)
    results.append(("조달청 접속 및 SN 파싱", "OK" if sns else "FAIL",
                    f"{len(sns)}개 SN 발견 (첫번째: {sns[0] if sns else 'none'})"))
except Exception as e:
    results.append(("조달청 접속 및 SN 파싱", "FAIL", str(e)))

# 5. Check update.bat path
bat = os.path.join(os.path.dirname(__file__), "update.bat")
with open(bat, encoding="cp949", errors="ignore") as f:
    bat_content = f.read()
results.append(("update.bat 스크립트 경로", "OK" if "update.ps1" in bat_content else "FAIL",
                bat_content.strip()[:120]))

# 6. Check git remote
r2 = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True,
                    cwd=os.path.dirname(__file__))
results.append(("Git remote", "OK" if "github.com" in r2.stdout else "FAIL", r2.stdout.strip()[:80]))

print("\n" + "="*60)
print("  자동 업데이트 파이프라인 진단 결과")
print("="*60)
for name, status, detail in results:
    icon = "[OK]  " if status == "OK" else ("[WARN]" if status == "WARN" else "[FAIL]")
    print(f"{icon} {name}")
    print(f"   {detail}")
print("="*60)
