# 🦞 OpenClaw 개인 투자 비서 세팅 가이드

Azure Linux VM에서 OpenClaw를 활용해 매일 자동으로 투자 브리핑을 생성하고 Telegram으로 받는 시스템입니다.

## 🧭 README 정리 순서 (OpenClaw → Webapp)

1. OpenClaw 공통 개요
2. OpenClaw 설치/운영 절차
3. Webapp 배포/실행
4. Webapp 아키텍처/기능
5. 작업자용 프롬프트 템플릿

아래 문서는 위 순서대로 읽으면 바로 따라할 수 있도록 구성되어 있습니다.

## 🚀 서비스 접근 (즉시 이용 가능)

> **웹앱 대시보드**: <http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/>
>
> 포트폴리오 조회, 관심종목 관리, 일/주간 리포트 확인 가능

## 1) OpenClaw 공통 개요

## 📋 완성된 기능

- 📊 **매일 09:00 KST** — 일일 투자 브리핑 자동 생성 + Telegram 전송
- 📋 **매주 월요일 09:10 KST** — 주간 포트폴리오 리포트 자동 생성
- 💹 **실시간 시장 데이터** — yfinance 기반 (KOSPI, S&P500, USDKRW, VIX 등)
- 📁 **마크다운 리포트** — 파일로 누적 저장
- 🤖 **AI 시나리오 분석** — OpenClaw agent가 Bullish/Base/Bear 자동 작성
- 🌐 **웹앱 포트폴리오/관심종목 관리** — FastAPI + SPA 기반 CRUD
- 🌍 **웹 UI 다국어 지원** — 한국어, 영어, 일본어, 중국어, 프랑스어 전환 지원 (현재 UI 라벨/버튼/알림 중심, 저장 데이터/리포트 원문은 유지)
- ✨ **관심종목 자동채움** — ticker/종목명 기반 enrich로 시장/가격/분석 문구 제안
- 🔒 **자동채움 중 저장/취소 잠금** — 로딩 중 버튼 비활성화로 입력 일관성 유지

## 🏗️ 레포 구조

```text
investment-assistant/
├── openclaw/                   # OpenClaw 설정 및 가이드
│   ├── docs/                   # 단계별 설치 가이드
│   ├── scripts/                # 설치 스크립트
│   ├── skills/                 # OpenClaw 스킬 정의
│   └── data-templates/         # 데이터 파일 템플릿
├── webapp/                     # 웹앱 소스코드
│   ├── main.py                 # FastAPI 엔트리
│   ├── config.py               # 데이터/리포트 경로 설정
│   ├── routers/                # API 라우터 (reports/portfolio/watchlist, UI: 관심종목)
│   └── static/                 # SPA 정적 파일(index.html)
└── README.md
```

### OpenClaw VM 구조 (Azure Linux VM 기준)

```text
~/investment-assistant/         # VM 상의 실제 운영 폴더
├── data/
│   ├── investor_profile.md     # 투자자 프로필
│   ├── portfolio.csv           # 보유 종목
│   └── watchlist.csv           # 관심종목
├── reports/
│   ├── daily/                  # 일일 브리핑 (YYYY-MM-DD.md)
│   └── weekly/                 # 주간 리포트 (YYYY-Wxx.md)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py        # 브리핑 생성 스크립트
```

## ✅ 사전 요구사항

- Ubuntu 24.04 LTS (Azure VM 기준)
- OpenClaw 설치 및 실행 중 (`openclaw-gateway` 프로세스)
- Telegram 봇 연결 완료
- Python 3.x
- FastAPI/uvicorn 실행 가능한 Python 환경

## 🚀 설치 순서

| 단계 | 내용 |
| ---- | ---- |
| [Step 1](./openclaw/docs/step1-project-setup.md) | 프로젝트 폴더 및 데이터 파일 생성 |
| [Step 2](./openclaw/docs/step2-skills.md) | OpenClaw 스킬 등록 |
| [Step 3](./openclaw/docs/step3-briefing-script.md) | 브리핑 생성 Python 스크립트 |
| [Step 4](./openclaw/docs/step4-cron.md) | cron 자동 스케줄 등록 |
| [Step 5](./openclaw/docs/step5-test.md) | 테스트 및 검증 |

## ⚠️ 알려진 문제 및 팁

[troubleshooting.md](./openclaw/docs/troubleshooting.md) 참고

## 2) Webapp 배포/운영

## 🌐 Azure Linux VM 웹앱 배포 가이드 (복사/붙여넣기)

### 1) 배포 정보

- 배포 위치: `/home/hahaysh/webapp1/webapp`
- 서비스명: `investment-webapp` (systemd)
- 실행 포트: `8001`
- 운영 주소: `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/`
- 웹앱 데이터 경로: `~/investment-assistant/data`, `~/investment-assistant/reports`

### 2) 사전 준비

```bash
mkdir -p ~/investment-assistant/data
mkdir -p ~/investment-assistant/reports/daily
mkdir -p ~/investment-assistant/reports/weekly
```

### 3) 소스 다운로드

```bash
mkdir -p ~/webapp1
cd ~/webapp1
git clone https://github.com/hahaysh/invest-assist .
```

### 4) Python 가상환경 및 의존성 설치

```bash
cd ~/webapp1
python3 -m venv venv
source venv/bin/activate
cd webapp
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5) 수동 실행으로 1차 확인

```bash
cd ~/webapp1/webapp
/home/hahaysh/webapp1/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

다른 SSH 세션에서 확인:

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8001/api/status
```

### 6) systemd 서비스 등록

```bash
sudo tee /etc/systemd/system/investment-webapp.service > /dev/null << 'EOF'
[Unit]
Description=Investment Assistant WebApp
After=network.target

[Service]
Type=simple
User=hahaysh
Group=hahaysh
WorkingDirectory=/home/hahaysh/webapp1/webapp
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/hahaysh/webapp1/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable investment-webapp
sudo systemctl restart investment-webapp
sudo systemctl status investment-webapp --no-pager
```

### 7) 네트워크 설정

```bash
sudo ufw allow 8001/tcp
sudo ufw status
```

참고: UFW가 비활성(inactive)이어도 Azure NSG 인바운드에서 TCP 8001 허용이 필요합니다.

### 8) 최종 확인

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8001/api/status
curl -s http://127.0.0.1:8001/api/portfolio
curl -s http://127.0.0.1:8001/api/watchlist
```

브라우저 접속:

- `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/`

### 9) 운영 명령어

```bash
# 서비스 상태
sudo systemctl status investment-webapp --no-pager

# 서비스 로그
sudo journalctl -u investment-webapp -n 100 --no-pager
sudo journalctl -u investment-webapp -f

# 서비스 재시작
sudo systemctl restart investment-webapp
```

### 10) 코드 업데이트 배포(수동)

```bash
cd ~/webapp1
git pull
source venv/bin/activate
cd webapp
pip install -r requirements.txt
sudo systemctl restart investment-webapp
sudo systemctl status investment-webapp --no-pager
```

### ✅ 빠른 점검 체크리스트

- 서비스 상태: `sudo systemctl status investment-webapp --no-pager` 에서 `active (running)` 확인
- API 헬스체크: `curl -s http://127.0.0.1:8001/health` 응답이 `{"status":"ok"}` 인지 확인
- 상태 API 확인: `curl -s http://127.0.0.1:8001/api/status` 에서 `status: ok` 및 최신 리포트 키(`last_daily`, `last_weekly`) 확인
- 외부 접속: `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/` 페이지 정상 로딩 확인

## 📱 수동 실행

```bash
# 웹앱 수동 실행 (VM 내부)
cd ~/webapp1/webapp
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001

# 일일 브리핑 즉시 실행
python3 ~/investment-assistant/generate_briefing.py

# 주간 리포트 즉시 실행
~/.npm-global/bin/openclaw agent \
  --to telegram:YOUR_CHAT_ID --deliver \
  --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘."
```

`POST /api/run-briefing` API는 `~/investment-assistant/generate_briefing.py`를 호출합니다.

### 로컬 개발 실행 (Windows)

아래 순서로 실행하면 `Could not import module "main"` 오류를 피할 수 있습니다.

```powershell
cd C:\Demo\Copilot\invest-assist\webapp
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

체크 포인트:

- `main.py`가 있는 `webapp` 폴더에서 실행해야 합니다.
- 루트 폴더(`invest-assist`)에서 실행하면 import 오류가 발생할 수 있습니다.
- `python -c "import main; print('Main module imported successfully')"`로 사전 확인 가능합니다.

## 3) Webapp 아키텍처/기능

## 🧱 웹앱 아키텍처 & 구조

이 웹앱은 **FastAPI 백엔드 + 단일 HTML/JS SPA 프론트엔드 + CSV 파일 저장소**로 구성됩니다.
운영 환경에서는 `~/investment-assistant` 경로의 데이터/리포트를 그대로 읽고 쓰기 때문에, OpenClaw 자동 브리핑 파이프라인과 자연스럽게 연결됩니다.

### 1) 전체 구성도

```mermaid
flowchart LR
  U[사용자 브라우저]\n(대시보드/포트폴리오/관심종목)
  FE[index.html SPA]\n(상태관리 + fetch API)
  API[FastAPI app]\n(main.py)
  R1[reports router]\n/api/reports/*
  R2[portfolio router]\n/api/portfolio/*
  R3[watchlist router]\n/api/watchlist/*
  CSV1[portfolio.csv]
  CSV2[watchlist.csv]
  REP1[daily reports/*.md]
  REP2[weekly reports/*.md]
  BR[generate_briefing.py]
  YF[yfinance]

  U --> FE
  FE --> API
  API --> R1
  API --> R2
  API --> R3

  R1 --> REP1
  R1 --> REP2
  R2 --> CSV1
  R3 --> CSV2
  R3 --> YF

  FE -->|POST /api/run-briefing| API
  API --> BR
  BR --> REP1
  BR --> REP2
```

### 2) 백엔드 구조

```text
webapp/
├── main.py                 # FastAPI 앱 생성, 라우터 등록, 정적 파일 제공
├── config.py               # 데이터/리포트/브리핑 스크립트 경로
├── routers/
│   ├── reports.py          # 일일/주간 리포트 목록/본문 조회
│   ├── portfolio.py        # 포트폴리오 CRUD + 요약(/api/portfolio/summary)
│   └── watchlist.py        # 관심종목 CRUD + enrich(yfinance)
└── static/
    └── index.html          # 단일 SPA (UI + 상태 + API 호출)
```

핵심 포인트:

- `main.py`에서 CORS, 라우터, `/static` 마운트, `/api/run-briefing`, `/api/status`를 관리합니다.
- `config.py`는 운영 데이터 루트(`~/investment-assistant/...`)를 단일 소스로 정의합니다.
- 각 라우터는 파일 I/O 실패를 HTTP 예외로 변환해 프론트에서 사용자 메시지로 표시할 수 있게 합니다.

### 3) 프론트엔드 구조(SPA)

`static/index.html` 한 파일에 화면/스타일/상태/이벤트/네트워크 호출이 통합되어 있습니다.

주요 상태:

- `currentTab`, `viewerType`
- `portfolioEditTicker`, `watchlistEditTicker`
- `portfolioAutofillLoading`, `watchlistAutofillLoading`

주요 동작:

- 대시보드: `/api/status`, `/api/reports/daily`, `/api/reports/weekly` 동시 조회
- 리포트 뷰어: Markdown 렌더링 + 용어 치환(Thesis → 투자논리, watchlist → 관심종목)
- 포트폴리오 탭: /api/portfolio + /api/portfolio/summary 동시 조회로 요약 카드(국내/해외/전체) 렌더링
- 포트폴리오 모달: 관심종목 선택 기반 자동채움 + 숫자 타입 검증
- 관심종목 모달: ticker/company blur 시 enrich 자동채움

### 4) 데이터 흐름

#### A. 대시보드 로딩

1. SPA 초기화 시 `refreshDashboard()` 호출
2. 상태/리포트 목록 API 병렬 호출
3. 최신 일자 표시 + 선택 박스 구성
4. 선택된 일자의 리포트 본문 조회 및 렌더링

#### B. 포트폴리오 자동채움(관심종목 기반)

1. 포트폴리오 모달에서 관심종목 선택
2. `/api/watchlist`와 `/api/portfolio`를 함께 조회
3. 이미 보유 중인 ticker는 선택 목록에서 제외
4. 선택 ticker 기준 `/api/watchlist/enrich` 호출
5. 투자논리/진입 관찰 포인트/무효화 조건 등을 조합해 기본 문구 생성
6. 자동채움 중 저장/취소 버튼 잠금, 완료 후 해제

#### C. 관심종목 자동채움

1. 신규 모달에서 ticker 또는 종목명 입력 후 blur
2. `/api/watchlist/enrich` 호출
3. 시장/진입가/관심 이유/진입 조건/부정 조건/위험 노트를 기본 채움
4. **빈 필드만 채움**(사용자 입력값 보존)
5. 자동채움 중 저장/취소 버튼 잠금, 완료 후 해제

### 5) API 레이어 역할

- `GET /api/reports/daily`, `GET /api/reports/weekly`: 파일명 규칙 기반 목록 조회
- `GET /api/reports/daily/{date}`, `GET /api/reports/weekly/{week}`: 본문 조회
- `GET/POST/PUT/DELETE /api/portfolio`: 포트폴리오 CSV CRUD
- `GET/POST/PUT/DELETE /api/watchlist`: 관심종목 CSV CRUD
- `GET /api/watchlist/enrich`: yfinance 기반 보강 데이터 생성 (`ticker` 또는 `company_name`, 선택 `lang=ko|en|ja|zh|fr`)
- `POST /api/run-briefing`: 브리핑 생성 스크립트 비동기 실행
- `GET /api/status`: 최근 일일/주간 리포트 키 반환

### 6) 저장소(파일) 설계

- `portfolio.csv`: 포트폴리오 원본
- `watchlist.csv`: 관심종목 원본
- `reports/daily/*.md`, `reports/weekly/*.md`: 브리핑/리포트 결과

장점:

- DB 없이도 운영/백업/이식이 단순
- OpenClaw 스크립트와 동일 데이터 소스를 공유

주의:

- 동시 다중 사용자 편집 환경에서는 CSV 기반 특성상 충돌 관리가 필요합니다.

### 7) 확장 포인트

- 인증/권한: FastAPI dependency 기반 토큰 인증 추가
- 저장소 교체: CSV 레이어를 DB(SQLModel/SQLite/PostgreSQL)로 교체
- API 분리: `static/index.html`의 네트워크 로직을 별도 JS 모듈로 분리
- 운영 강화: structured logging, request ID, 에러 추적(App Insights 등)

### 8) 신규 기여자 빠른 이해 순서

1. `webapp/main.py`에서 엔트리/라우터 구성을 확인
2. `webapp/routers/*.py`에서 API 계약과 파일 I/O 정책 확인
3. `webapp/static/index.html`에서 탭 전환/모달/자동채움 흐름 확인
4. README의 API 목록과 로컬 실행 절차로 실제 호출 테스트

## 🖥️ 웹앱 기능 요약

- 대시보드: 최신 일일/주간 리포트 조회 및 목록 확인
- 포트폴리오: 종목 CRUD, 관심종목 기반 자동채움 지원
- 관심종목: ticker 입력 후 자동채움(enrich)으로 기본 값 제안
- 자동채움 정책: 빈 필드 우선 채움, 자동채움 완료 전 저장/취소 비활성화
- 리포트 용어: 보유 종목 현황 표기는 포트 폴리오 현황으로 사용

### 웹앱 주요 API

- GET /api/portfolio
- POST /api/portfolio
- PUT /api/portfolio/{ticker}
- DELETE /api/portfolio/{ticker}
- GET /api/watchlist
- GET /api/watchlist/enrich?ticker=...&lang=en
- POST /api/watchlist
- PUT /api/watchlist/{ticker}
- DELETE /api/watchlist/{ticker}

## 📂 파일 업데이트

```bash
# 포트폴리오 수정 (매수/매도 후)
nano ~/investment-assistant/data/portfolio.csv

# 관심종목 수정
nano ~/investment-assistant/data/watchlist.csv
```

웹앱 사용이 가능한 환경이라면 CSV 수동 편집보다 웹앱 UI에서 추가/수정/삭제하는 방식이 권장됩니다.

## 👥 작업자용 프롬프트 템플릿

아래 템플릿은 최근 반영된 변경사항(관심종목 자동채움, 버튼 잠금, 용어 정리, README 동기화)을 기준으로 작성되었습니다.

### 템플릿 A: 작업 시작 컨텍스트 고정

```text
이 프로젝트는 투자 비서 웹앱이며, 최근 변경사항 기준으로 일관성을 유지해서 작업해줘.
중요 기준:
- 사용자 노출 용어는 관심종목으로 통일
- 내부 경로/API 명칭은 watchlist 유지 가능
- 자동채움 중에는 저장/취소 버튼을 비활성화
- 자동채움은 기존 입력값을 덮어쓰지 않고 빈 필드 우선 채움
- 포트폴리오 저장 시 숫자 필드는 문자열 입력도 숫자 변환 후 검증
- 에러 메시지는 object 형태가 보이지 않게 사람이 읽을 수 있게 파싱
- 대시보드 리포트 표시는 Thesis 대신 투자논리, watchlist 대신 관심종목으로 보여줘
- 문구 표준은 포트 폴리오 현황 사용
- UI 문자열은 t(key) 함수로만 출력하고, 새 문구 추가 시 TRANSLATIONS 사전 5개 언어에 모두 키를 추가해줘
- 관심종목 enrich 호출 시 lang=state.language 파라미터를 반드시 포함시켜줘
작업 방식:
- 코드 수정 후 바로 검색/검증까지 완료
- 변경 이유와 사용자 영향도를 짧게 요약
- 문서가 필요하면 README도 함께 갱신
```

### 템플릿 B: 기능 수정 요청

```text
아래 요구사항을 구현해줘.
요구사항:
1. 포트폴리오 추가/수정 화면에서 관심종목 선택 시 자동채움 동작을 개선
2. 이미 포트폴리오에 있는 종목은 관심종목 선택 목록에서 제외
3. 자동채움 실행 중 저장/취소 버튼 비활성화, 완료 후 복구
4. 자동채움은 빈 필드만 채우고 사용자가 입력한 값은 유지
5. 저장 시 숫자 필드 타입 검증 강화
6. API 에러 메시지는 사용자 친화적으로 표시
검증:
- 관심종목 선택 시 자동채움 정상 동작
- 보유 종목 중복 노출 없음
- 로딩 중 버튼 잠금 동작 확인
- 숫자 입력 오류 메시지 확인
- 기존 기능 회귀 없음
마지막에 변경 파일별 요약과 수동 테스트 체크리스트를 제공해줘.
```

### 템플릿 C: enrich API 고도화 요청

```text
watchlist enrich API를 실사용 관점으로 강화해줘.
목표:
- ticker 해석 실패를 줄이기 위해 후보 ticker 전략 보강
- 현재가 조회 실패 시 대체 경로로 가격 확보
- currency 값을 안정적으로 반환
- 오류 응답은 400/502를 구분하고 detail 메시지를 명확히 제공
프론트 연동 조건:
- 자동채움은 이 API 결과를 사용
- 빈 필드만 채우는 정책 유지
- 실패 시 사용자에게 재시도 가능한 메시지 표시
완료 후:
- 성공/실패 케이스별 예시 응답
- 회귀 위험 포인트
- 테스트 시나리오 5개를 제시해줘.
```

### 템플릿 D: README 동기화 요청

```text
최근 구현 내역 기준으로 README를 업데이트해줘.
반영 항목:
- 웹앱 핵심 기능 요약 추가
- 관심종목 자동채움 및 버튼 잠금 정책 설명
- watchlist enrich API 설명 추가
- 용어 통일: 관심종목, 포트 폴리오 현황
- 수동 CSV 편집보다 웹앱 UI 사용 권장 문구 추가
작업 원칙:
- 과장 없이 현재 구현된 기능만 문서화
- 기존 설치/배포 절차는 유지
- 변경 후 용어 검색으로 누락 검증
마지막에:
- 무엇이 왜 바뀌었는지 5줄 이내 요약
- 문서 사용자 관점에서 달라진 점을 정리해줘.
```
