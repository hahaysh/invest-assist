"""
Google Sheets 연결 테스트 스크립트
- config/secrets.env 에서 크레덴셜 로드
- Refresh Token으로 Access Token 발급
- 일일브리핑 시트에 테스트 행 추가
"""

import os
import sys
import json
import requests
from datetime import datetime

# ── 1. secrets.env 로드 ──────────────────────────────────────────────────────
ENV_PATH = os.path.join(os.path.dirname(__file__), "../config/secrets.env")

def load_env(path):
    if not os.path.exists(path):
        print(f"[ERROR] 파일 없음: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

load_env(ENV_PATH)

CLIENT_ID       = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET   = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REFRESH_TOKEN   = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
SPREADSHEET_ID  = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")

missing = [k for k, v in {
    "GOOGLE_CLIENT_ID": CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": CLIENT_SECRET,
    "GOOGLE_REFRESH_TOKEN": REFRESH_TOKEN,
    "GOOGLE_SHEETS_SPREADSHEET_ID": SPREADSHEET_ID,
}.items() if not v]

if missing:
    print(f"[ERROR] secrets.env에 값이 없는 항목: {', '.join(missing)}")
    sys.exit(1)

# ── 2. Access Token 발급 ─────────────────────────────────────────────────────
print("[ 1/3 ] Access Token 발급 중...")
token_resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN,
    "grant_type":    "refresh_token",
})

if token_resp.status_code != 200:
    print(f"[ERROR] 토큰 발급 실패: {token_resp.text}")
    sys.exit(1)

access_token = token_resp.json().get("access_token")
print(f"       ✅ Access Token 발급 성공")

# ── 3. 시트 이름 확인 ────────────────────────────────────────────────────────
print("[ 2/3 ] 스프레드시트 탭 확인 중...")
headers = {"Authorization": f"Bearer {access_token}"}
meta_resp = requests.get(
    f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}",
    headers=headers,
)

if meta_resp.status_code != 200:
    print(f"[ERROR] 스프레드시트 접근 실패: {meta_resp.text}")
    sys.exit(1)

sheets = [s["properties"]["title"] for s in meta_resp.json().get("sheets", [])]
print(f"       발견된 탭: {sheets}")

target = "일일브리핑"
if target not in sheets:
    print(f"[WARNING] '{target}' 탭이 없습니다. 탭을 먼저 생성해주세요.")
    print(f"          현재 탭 목록: {sheets}")
    sys.exit(1)
print(f"       ✅ '{target}' 탭 확인")

# ── 4. 테스트 행 추가 ────────────────────────────────────────────────────────
print("[ 3/3 ] 테스트 행 추가 중...")
now_kst = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
today   = datetime.now().strftime("%Y-%m-%d")

test_row = [
    today,           # 날짜
    datetime.now().strftime("%H:%M"),  # 실행시각_KST
    "테스트",        # 시장국면
    "", "", "", "", "", "", "", "", "", "", "", "", "", "",  # 지수/지표 (빈값)
    "",              # 강세섹터
    "",              # 약세섹터
    "연결테스트",    # 핵심동인Top3
    "테스트행",      # 포트폴리오액션요약
    "",              # 오늘주요일정
    "TEST",          # 리포트파일
    now_kst,         # 생성시각
]

append_resp = requests.post(
    f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    f"/values/{requests.utils.quote(target)}!A1:append"
    f"?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
    headers={**headers, "Content-Type": "application/json"},
    data=json.dumps({"values": [test_row]}),
)

if append_resp.status_code != 200:
    print(f"[ERROR] 행 추가 실패: {append_resp.text}")
    sys.exit(1)

updated = append_resp.json().get("updates", {}).get("updatedRange", "")
print(f"       ✅ 테스트 행 추가 성공 → {updated}")

print()
print("=" * 50)
print("  Google Sheets 연결 테스트 완료 ✅")
print(f"  스프레드시트: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print("  확인 후 테스트 행은 직접 삭제해주세요.")
print("=" * 50)
