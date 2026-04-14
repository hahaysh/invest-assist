"""
Google OAuth2 Refresh Token 발급 스크립트
- config/secrets.env 에서 CLIENT_ID, CLIENT_SECRET 로드
- 브라우저 인증 후 Refresh Token 출력
- secrets.env 자동 업데이트
"""

import os
import sys
import re

ENV_PATH = os.path.join(os.path.dirname(__file__), "../config/secrets.env")

def load_env(path):
    env = {}
    if not os.path.exists(path):
        print(f"[ERROR] 파일 없음: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env

env = load_env(ENV_PATH)
CLIENT_ID     = env.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = env.get("GOOGLE_CLIENT_SECRET", "")

if not CLIENT_ID or not CLIENT_SECRET:
    print("[ERROR] secrets.env에 GOOGLE_CLIENT_ID 또는 GOOGLE_CLIENT_SECRET 없음")
    sys.exit(1)

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("[ERROR] 패키지 없음. 아래 명령 실행 후 다시 시도하세요:")
    print("        pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print("브라우저에서 Google 계정으로 로그인하고 권한을 허용해주세요...")
print()

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
creds = flow.run_local_server(port=0)

refresh_token = creds.refresh_token
print()
print("=" * 50)
print("  Refresh Token 발급 성공 ✅")
print("=" * 50)

# secrets.env 자동 업데이트
with open(ENV_PATH, encoding="utf-8") as f:
    content = f.read()

if "GOOGLE_REFRESH_TOKEN=" in content:
    content = re.sub(
        r"GOOGLE_REFRESH_TOKEN=.*",
        f"GOOGLE_REFRESH_TOKEN={refresh_token}",
        content
    )
else:
    content += f"\nGOOGLE_REFRESH_TOKEN={refresh_token}\n"

with open(ENV_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("  config/secrets.env 업데이트 완료")
print()
print("  이제 다시 실행하세요:")
print("  python scripts/test_sheets.py")
