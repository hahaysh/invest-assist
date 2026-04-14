"""
일일브리핑 Google Sheets 기록 스크립트
사용: python scripts/sheets_write_daily.py
"""

import os, sys, json, requests
from datetime import datetime

ENV_PATH = os.path.join(os.path.dirname(__file__), "../config/secrets.env")

def load_env(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

load_env(ENV_PATH)

CLIENT_ID      = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET  = os.environ["GOOGLE_CLIENT_SECRET"]
REFRESH_TOKEN  = os.environ["GOOGLE_REFRESH_TOKEN"]
SPREADSHEET_ID = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]

# Access Token 발급
r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token",
})
if r.status_code != 200:
    print(f"[ERROR] 토큰 발급 실패: {r.text}"); sys.exit(1)
access_token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# 기록할 데이터 (2026-04-14 브리핑)
now = datetime.now()
row = [
    "2026-04-14",               # 날짜
    "09:00",                    # 실행시각_KST
    "위험선호 회복",             # 시장국면
    "5967.75",                  # 코스피종가
    "+2.74",                    # 코스피1일등락률
    "1121.88",                  # 코스닥종가
    "+2.00",                    # 코스닥1일등락률
    "6885",                     # S&P500종가
    "+1.01",                    # S&P5001일등락률
    "23183",                    # 나스닥종가
    "+1.23",                    # 나스닥1일등락률
    "1484.91",                  # 원달러환율
    "4.297",                    # 미국10년물금리
    "98.54",                    # 달러인덱스
    "98.90",                    # WTI
    "4748.18",                  # 금가격
    "n/a",                      # VIX
    "반도체,에너지,금융",        # 강세섹터
    "자동차,바이오",             # 약세섹터
    "미이란휴전협상,달러약세,반도체랠리",  # 핵심동인Top3
    "전종목홀드,현금14%유지",    # 포트폴리오액션요약
    "미이란협상동향,금융실적시즌개막",     # 오늘주요일정
    "reports/daily/2026-04-14.md",        # 리포트파일
    now.strftime("%Y-%m-%d %H:%M:%S"),    # 생성시각
]

SHEET = "일일브리핑"
resp = requests.post(
    f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    f"/values/{requests.utils.quote(SHEET)}!A1:append"
    f"?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
    headers=headers,
    data=json.dumps({"values": [row]}),
)

if resp.status_code != 200:
    print(f"[ERROR] 기록 실패: {resp.text}"); sys.exit(1)

updated = resp.json().get("updates", {}).get("updatedRange", "")
print(f"✅ Google Sheets 기록 성공 → {updated}")
print(f"   시트: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
