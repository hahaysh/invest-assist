# 🦞 OpenClaw 개인 투자 비서 세팅 가이드

Azure Linux VM에서 OpenClaw를 활용해 매일 자동으로 투자 브리핑을 생성하고 Telegram으로 받는 시스템입니다.

## 📋 완성된 기능

- 📊 **매일 09:00 KST** — 일일 투자 브리핑 자동 생성 + Telegram 전송
- 📋 **매주 월요일 09:10 KST** — 주간 포트폴리오 리포트 자동 생성
- 💹 **실시간 시장 데이터** — yfinance 기반 (KOSPI, S&P500, USDKRW, VIX 등)
- 📁 **마크다운 리포트** — 파일로 누적 저장
- 🤖 **AI 시나리오 분석** — OpenClaw agent가 Bullish/Base/Bear 자동 작성
- 🌐 **웹앱 포트폴리오/관심종목 관리** — FastAPI + SPA 기반 CRUD
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
- GET /api/watchlist/enrich?ticker=...
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
