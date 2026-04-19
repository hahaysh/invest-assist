# 🦞 OpenClaw Personal Investment Assistant — Setup Guide

> 🇰🇷 [한국어 버전 → README.ko.md](./README.ko.md)

Azure Linux VM setup for automatically generating daily investment briefings via OpenClaw and delivering them through Telegram.

## 🧭 Document Order (OpenClaw → Webapp)

1. OpenClaw Overview
2. OpenClaw Installation & Operations
3. Webapp Deployment & Execution
4. Webapp Architecture & Features
5. Contributor Prompt Templates

Read the sections below in order for a step-by-step walkthrough.

## 🚀 Service Access (Ready to Use)

> **Web Dashboard**: <http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/>
>
> View portfolio, manage watchlist, and check daily/weekly reports.

## 1) OpenClaw Overview

## 📋 Implemented Features

- 📊 **Daily at 09:00 KST** — Auto-generate daily investment briefing + Telegram delivery
- 📋 **Every Monday 09:10 KST** — Weekly portfolio report auto-generation
- 💹 **Real-time Market Data** — yfinance-based (KOSPI, S&P500, USDKRW, VIX, etc.)
- 📁 **Markdown Reports** — Accumulated file storage
- 🤖 **AI Scenario Analysis** — OpenClaw agent auto-writes Bullish/Base/Bear scenarios
- 🌐 **Web Portfolio/Watchlist Management** — FastAPI + SPA-based CRUD
- 🌍 **Multi-language Web UI** — Korean, English, Japanese, Chinese, French (UI labels/buttons/notifications; stored data and report content are preserved as-is)
- ✨ **Watchlist Autofill** — ticker/name-based enrich to suggest market/price/analysis text
- 🔒 **Autofill Lock** — Save/Cancel buttons disabled during loading to ensure input consistency
- 📱 **Mobile-responsive UI** — Optimized layout for smartphones and tablets

## 🏗️ Repository Structure

```text
investment-assistant/
├── openclaw/                   # OpenClaw configuration and guides
│   ├── docs/                   # Step-by-step setup guides
│   ├── scripts/                # Installation scripts
│   ├── skills/                 # OpenClaw skill definitions
│   └── data-templates/         # Data file templates
├── webapp/                     # Webapp source code
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Data/report path configuration
│   ├── routers/                # API routers (reports/portfolio/watchlist)
│   └── static/                 # SPA static files (index.html)
└── README.md
```

### OpenClaw VM Structure (Azure Linux VM)

```text
~/investment-assistant/         # Actual operating folder on VM
├── data/
│   ├── investor_profile.md     # Investor profile
│   ├── portfolio.csv           # Holdings
│   └── watchlist.csv           # Watchlist
├── reports/
│   ├── daily/                  # Daily briefings (YYYY-MM-DD.md)
│   └── weekly/                 # Weekly reports (YYYY-Wxx.md)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py        # Briefing generation script
```

## ✅ Prerequisites

- Ubuntu 24.04 LTS (Azure VM)
- OpenClaw installed and running (`openclaw-gateway` process)
- Telegram bot connected
- Python 3.x
- Python environment capable of running FastAPI/uvicorn

## 🚀 Installation Steps

| Step | Description |
| ---- | ----------- |
| [Step 1](./openclaw/docs/step1-project-setup.md) | Create project folder and data files |
| [Step 2](./openclaw/docs/step2-skills.md) | Register OpenClaw skills |
| [Step 3](./openclaw/docs/step3-briefing-script.md) | Briefing generation Python script |
| [Step 4](./openclaw/docs/step4-cron.md) | Register cron schedule |
| [Step 5](./openclaw/docs/step5-test.md) | Test and verification |

## ⚠️ Known Issues & Tips

See [troubleshooting.md](./openclaw/docs/troubleshooting.md)

## 2) Webapp Deployment & Operations

## 🌐 Azure Linux VM Webapp Deployment Guide (Copy & Paste)

### 1) Deployment Info

- Deployment path: `/home/hahaysh/webapp1/webapp`
- Service name: `investment-webapp` (systemd)
- Port: `8001`
- URL: `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/`
- Webapp data path: `~/investment-assistant/data`, `~/investment-assistant/reports`

### 2) Pre-requisite Directories

```bash
mkdir -p ~/investment-assistant/data
mkdir -p ~/investment-assistant/reports/daily
mkdir -p ~/investment-assistant/reports/weekly
```

### 3) Clone Source

```bash
mkdir -p ~/webapp1
cd ~/webapp1
git clone https://github.com/hahaysh/invest-assist .
```

### 4) Python Virtual Environment & Dependencies

```bash
cd ~/webapp1
python3 -m venv venv
source venv/bin/activate
cd webapp
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5) Manual Test Run

```bash
cd ~/webapp1/webapp
/home/hahaysh/webapp1/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Verify from another SSH session:

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8001/api/status
```

### 6) systemd Service Registration

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

### 7) Network Configuration

```bash
sudo ufw allow 8001/tcp
sudo ufw status
```

Note: Even if UFW is inactive, TCP 8001 must be allowed in Azure NSG inbound rules.

### 8) Final Verification

```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8001/api/status
curl -s http://127.0.0.1:8001/api/portfolio
curl -s http://127.0.0.1:8001/api/watchlist
```

Browser access:

- `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/`

### 9) Operations Commands

```bash
# Service status
sudo systemctl status investment-webapp --no-pager

# Service logs
sudo journalctl -u investment-webapp -n 100 --no-pager
sudo journalctl -u investment-webapp -f

# Restart service
sudo systemctl restart investment-webapp
```

### 10) Manual Code Update & Deploy

```bash
cd ~/webapp1
git pull
source venv/bin/activate
cd webapp
pip install -r requirements.txt
sudo systemctl restart investment-webapp
sudo systemctl status investment-webapp --no-pager
```

### ✅ Quick Health Checklist

- Service status: `sudo systemctl status investment-webapp --no-pager` shows `active (running)`
- API health check: `curl -s http://127.0.0.1:8001/health` returns `{"status":"ok"}`
- Status API: `curl -s http://127.0.0.1:8001/api/status` shows `status: ok` and latest report keys (`last_daily`, `last_weekly`)
- External access: `http://hahayshopenclaw.koreacentral.cloudapp.azure.com:8001/` loads correctly

## 📱 Manual Execution

```bash
# Webapp manual run (inside VM)
cd ~/webapp1/webapp
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001

# Run daily briefing immediately
python3 ~/investment-assistant/generate_briefing.py

# Run weekly report immediately
~/.npm-global/bin/openclaw agent \
  --to telegram:YOUR_CHAT_ID --deliver \
  --message "Generate weekly portfolio report. Reference ~/investment-assistant/data, run weekly-portfolio-report skill, and save to ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md"
```

`POST /api/run-briefing` calls `~/investment-assistant/generate_briefing.py`.

### Local Development (Windows)

Run in this order to avoid the `Could not import module "main"` error:

```powershell
cd C:\Demo\Copilot\invest-assist\webapp
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Checkpoints:

- Must run from the `webapp` folder where `main.py` exists.
- Running from the root `invest-assist` folder will cause an import error.
- Pre-check with `python -c "import main; print('Main module imported successfully')"`.

## 3) Webapp Architecture & Features

## 🧱 Webapp Architecture & Structure

This webapp consists of a **FastAPI backend + single HTML/JS SPA frontend + CSV file storage**.
In production, it reads and writes data/reports from `~/investment-assistant`, naturally integrating with the OpenClaw automated briefing pipeline.

### 1) Overall Architecture

```mermaid
flowchart LR
  U[User Browser]\n(Dashboard/Portfolio/Watchlist)
  FE[index.html SPA]\n(State + fetch API)
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

### 2) Backend Structure

```text
webapp/
├── main.py                 # FastAPI app creation, router registration, static file serving
├── config.py               # Data/report/briefing script paths
├── routers/
│   ├── reports.py          # Daily/weekly report list and body retrieval
│   ├── portfolio.py        # Portfolio CRUD + summary (/api/portfolio/summary)
│   └── watchlist.py        # Watchlist CRUD + enrich (yfinance)
└── static/
    └── index.html          # Single SPA (UI + state + API calls)
```

Key points:

- `main.py` manages CORS, routers, `/static` mount, `/api/run-briefing`, and `/api/status`.
- `config.py` defines the production data root (`~/investment-assistant/...`) as a single source.
- Each router converts file I/O failures to HTTP exceptions for user-friendly frontend messages.

### 3) Frontend Structure (SPA)

The `static/index.html` single file integrates screens, styles, state, events, and network calls.

Key state variables:

- `currentTab`, `viewerType`
- `portfolioEditTicker`, `watchlistEditTicker`
- `portfolioAutofillLoading`, `watchlistAutofillLoading`

Key behaviors:

- Dashboard: concurrent fetch of `/api/status`, `/api/reports/daily`, `/api/reports/weekly`
- Report viewer: Markdown rendering + term substitution (Thesis → Investment Logic, watchlist → Watchlist)
- Portfolio tab: concurrent fetch of `/api/portfolio` + `/api/portfolio/summary` for summary cards (Domestic/Overseas/Total)
- Portfolio modal: watchlist-based autofill + numeric type validation
- Watchlist modal: enrich autofill triggered on ticker/company blur

### 4) Data Flow

#### A. Dashboard Loading

1. `refreshDashboard()` called on SPA initialization
2. Parallel fetch of status and report list APIs
3. Display latest date + populate selection box
4. Fetch and render selected date's report body

#### B. Portfolio Autofill (Watchlist-based)

1. Select a watchlist item in the portfolio modal
2. Fetch `/api/watchlist` and `/api/portfolio` together
3. Exclude tickers already in portfolio from selection list
4. Call `/api/watchlist/enrich` for the selected ticker
5. Generate default text combining investment thesis/entry observation/invalidation conditions
6. Lock Save/Cancel buttons during autofill, unlock on completion

#### C. Watchlist Autofill

1. Enter ticker or company name in new modal and blur
2. Call `/api/watchlist/enrich`
3. Prefill market/entry price/watch reason/trigger condition/invalidation/risk notes
4. **Fill empty fields only** (preserve user-entered values)
5. Lock Save/Cancel buttons during autofill, unlock on completion

### 5) API Layer Responsibilities

- `GET /api/reports/daily`, `GET /api/reports/weekly`: filename-rule-based list retrieval
- `GET /api/reports/daily/{date}`, `GET /api/reports/weekly/{week}`: body retrieval
- `GET/POST/PUT/DELETE /api/portfolio`: portfolio CSV CRUD
- `GET/POST/PUT/DELETE /api/watchlist`: watchlist CSV CRUD
- `GET /api/watchlist/enrich`: yfinance-based enrichment (`ticker` or `company_name`, optional `lang=ko|en|ja|zh|fr`)
- `POST /api/run-briefing`: async execution of briefing generation script
- `GET /api/status`: returns latest daily/weekly report keys

### 6) Storage (File) Design

- `portfolio.csv`: portfolio source
- `watchlist.csv`: watchlist source
- `reports/daily/*.md`, `reports/weekly/*.md`: briefing/report results

Advantages:

- Simple operation/backup/portability without a database
- Shares the same data source as OpenClaw scripts

Note:

- In concurrent multi-user editing environments, CSV-based storage requires conflict management.

### 7) Extension Points

- Auth: Add token-based authentication via FastAPI dependency
- Storage: Replace CSV layer with a DB (SQLModel/SQLite/PostgreSQL)
- API separation: Extract network logic from `static/index.html` to a separate JS module
- Production hardening: structured logging, request IDs, error tracking (App Insights, etc.)

### 8) New Contributor Quick Start Order

1. Check entry/router configuration in `webapp/main.py`
2. Review API contracts and file I/O policies in `webapp/routers/*.py`
3. Follow tab switching/modal/autofill flows in `webapp/static/index.html`
4. Test actual calls using the API list and local execution procedure in README

## 🖥️ Webapp Feature Summary

- Dashboard: View latest daily/weekly reports and list
- Portfolio: CRUD, watchlist-based autofill support
- Watchlist: Enter ticker → autofill (enrich) suggests default values
- Autofill policy: Fill empty fields first, disable Save/Cancel before autofill completes
- Report terms: Use "Portfolio Status" instead of "Holdings Status"
- Language: UI supports 5 languages (ko/en/ja/zh/fr); language setting persists via localStorage

### Webapp Key APIs

- GET /api/portfolio
- POST /api/portfolio
- PUT /api/portfolio/{ticker}
- DELETE /api/portfolio/{ticker}
- GET /api/watchlist
- GET /api/watchlist/enrich?ticker=...&lang=en
- POST /api/watchlist
- PUT /api/watchlist/{ticker}
- DELETE /api/watchlist/{ticker}

## 📂 File Updates

```bash
# Update portfolio (after buy/sell)
nano ~/investment-assistant/data/portfolio.csv

# Update watchlist
nano ~/investment-assistant/data/watchlist.csv
```

If the web UI is available, using Add/Edit/Delete through the dashboard is recommended over direct CSV editing.

## 👥 Contributor Prompt Templates

The templates below are based on the latest changes (watchlist autofill, button lock, terminology, README sync).

### Template A: Session Context Setup

```text
This project is an investment assistant webapp. Work consistently based on the latest changes.
Key rules:
- Use "Watchlist" for user-facing terms
- Internal paths/API names can keep "watchlist"
- Disable Save/Cancel buttons during autofill
- Autofill fills empty fields only; do not overwrite user input
- Validate numeric fields by converting strings to numbers before saving
- Error messages must be human-readable, not raw objects
- In report rendering: display "Investment Logic" instead of "Thesis", "Watchlist" instead of "watchlist"
- Use "Portfolio Status" as the standard term
- All UI strings must go through t(key); never hardcode; add new keys to all 5 languages in TRANSLATIONS
- Always include lang=state.language when calling watchlist enrich
Work approach:
- Complete search/verification immediately after code changes
- Briefly summarize the reason for the change and user impact
- Update README if documentation is affected
```

### Template B: Feature Modification Request

```text
Please implement the following requirements.
Requirements:
1. Improve autofill behavior when selecting a watchlist item in the portfolio add/edit screen
2. Exclude tickers already in portfolio from the watchlist selection list
3. Disable Save/Cancel buttons during autofill, restore on completion
4. Autofill fills empty fields only; preserve user-entered values
5. Strengthen numeric field type validation on save
6. Display API error messages in a user-friendly format
Verification:
- Autofill works correctly when selecting a watchlist item
- No duplicate display of held tickers
- Button lock during loading confirmed
- Numeric input error messages confirmed
- No regression in existing features
Provide a per-file change summary and manual test checklist at the end.
```

### Template C: Enrich API Enhancement Request

```text
Enhance the watchlist enrich API from a practical usage perspective.
Goals:
- Improve candidate ticker strategy to reduce ticker resolution failures
- Find alternative price retrieval path when current price fetch fails
- Return currency value reliably
- Distinguish 400/502 error responses with clear detail messages
Frontend integration conditions:
- Autofill uses this API result
- Maintain "fill empty fields only" policy
- Show user a retryable message on failure
On completion:
- Example responses for success/failure cases
- Regression risk points
- 5 test scenarios
```
