# Google Sheets 수동 설정 절차

> 개발자가 아닌 분도 따라할 수 있도록 단계별로 작성했습니다.

---

## Part 1: Google Cloud 프로젝트 생성 및 API 활성화

### 1-1. Google Cloud Console 접속
1. [https://console.cloud.google.com](https://console.cloud.google.com) 접속
2. 로그인 후 상단의 프로젝트 선택 드롭다운 클릭
3. "새 프로젝트" 클릭 → 이름 입력 (예: `invest-assistant`) → "만들기"

### 1-2. Google Sheets API 활성화
1. 왼쪽 메뉴 > "API 및 서비스" > "라이브러리"
2. 검색창에 "Google Sheets API" 입력
3. 결과 클릭 → "사용 설정" 버튼 클릭

### 1-3. Google Drive API 활성화 (시트 접근용)
1. 동일하게 "Google Drive API" 검색 → 사용 설정

---

## Part 2: OAuth2 사용자 인증 정보 생성

### 2-1. 동의 화면 설정
1. "API 및 서비스" > "OAuth 동의 화면"
2. User Type: "외부" 선택 → "만들기"
3. 앱 이름 입력, 이메일 입력 → "저장 후 계속"
4. 범위 추가: `spreadsheets` + `drive.file` → "저장 후 계속"
5. 테스트 사용자에 본인 Gmail 추가 → "저장 후 계속"

### 2-2. 사용자 인증 정보 (Client ID / Secret) 발급
1. "API 및 서비스" > "사용자 인증 정보" > "+ 사용자 인증 정보 만들기" > "OAuth 클라이언트 ID"
2. 애플리케이션 유형: "데스크톱 앱" 선택
3. 이름 입력 → "만들기"
4. 팝업에서 **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사
   → `config/secrets.env`의 `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`에 붙여넣기

### 2-3. Refresh Token 발급 (최초 1회)
터미널에서 아래 명령 실행 (Python 필요):

```bash
pip install google-auth-oauthlib
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_config({
  'installed': {
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_CLIENT_SECRET',
    'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob'],
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token'
  }
}, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file'])
creds = flow.run_local_server(port=0)
print('Refresh Token:', creds.refresh_token)
"
```

브라우저 인증 완료 후 출력된 Refresh Token을 `GOOGLE_REFRESH_TOKEN`에 저장.

---

## Part 3: Google Sheets 스프레드시트 생성

### 3-1. 스프레드시트 생성
1. [https://sheets.google.com](https://sheets.google.com) 접속
2. "새 스프레드시트" 생성
3. 제목: `투자 비서 데이터`

### 3-2. 탭 생성
1. 하단 "+" 버튼으로 시트 추가
2. 시트1 이름을 `일일브리핑`으로 변경
3. 시트2 이름을 `주간포트폴리오리포트`으로 변경

### 3-3. 헤더 행 입력
각 시트의 1행에 `docs/google_sheets_schema.md`의 컬럼명을 순서대로 입력.

### 3-4. Spreadsheet ID 복사
URL: `https://docs.google.com/spreadsheets/d/{ID}/edit`  
`{ID}` 부분을 복사 → `GOOGLE_SHEETS_SPREADSHEET_ID`에 저장.

---

## Part 4: secrets.env 완성 확인

```env
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
GOOGLE_REFRESH_TOKEN=1//xxxxxxxxxxx
GOOGLE_SHEETS_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

완료 후 브리핑 스크립트를 실행하면 자동으로 데이터가 기록됩니다.
