# Copilot Instructions For invest-assist

This file defines the baseline rules that GitHub Copilot always follows in this repository.

## 1) Project Purpose

- This repository is an investment assistant system built on OpenClaw + FastAPI webapp.
- Production data uses CSV/report files located at `~/investment-assistant`.
- The webapp consists of a FastAPI backend in the `webapp` folder and a single SPA (`static/index.html`).

## 2) Work Priorities

1. Preserve existing behavior (prevent regression)
2. User input data integrity
3. User-friendly error messages
4. Keep README in sync with implementation

## 3) Terminology Rules (Important)

- User-facing UI/docs: use `Watchlist` (관심종목)
- Internal API/paths/filenames: keep `watchlist`
- Report display terms:
  - Use `Portfolio Status` instead of `Holdings Status`
  - Use `Investment Logic` instead of `Thesis`

## 4) Autofill Rules

- Never overwrite existing user input; fill empty fields only.
- Disable Save/Cancel buttons during autofill.
- Always restore button state after autofill completes or fails.
- Maintain behavioral differences between edit mode and new mode.

## 5) Validation Rules

- Validate numeric field input by converting strings to numbers before checking.
- Return user-understandable messages when integer/float field type validation fails.
- Never expose raw API error `detail` objects directly in the UI.

## 6) Backend Rules

- Maintain FastAPI router responsibilities:
  - `routers/reports.py`: report list/body
  - `routers/portfolio.py`: portfolio CRUD
  - `routers/watchlist.py`: watchlist CRUD + enrich
- Handle file I/O failures explicitly with HTTPException.
- Operate gracefully when CSV files are missing where possible.

## 7) Frontend Rules

- Control buttons/modals based on key state variables (`portfolioAutofillLoading`, `watchlistAutofillLoading`).
- Use a common fetch wrapper with a consistent error handling pattern for all API calls.
- Apply term substitution rules when rendering dashboard reports.
- **i18n (multi-language) rules**:
  - All UI strings must be retrieved from the translation dictionary via the `t(key)` function. No hardcoding.
  - When adding new UI strings, add keys for all 5 languages (ko/en/ja/zh/fr) to the `TRANSLATIONS` dictionary.
  - Language selection is managed via `state.language` and changed only through `setLanguage()`.
  - Static DOM elements use `data-i18n` attributes; dynamic text uses the `t()` function.
  - Always include `lang=state.language` in watchlist enrich calls so server-generated text is also in the current language.

## 8) Documentation Update Rules

Update `README.md` (both `README.md` and `README.en.md`) when any of the following change:

- User feature flows
- API endpoints
- Terminology policy
- Deployment/execution procedures

Maintain the `OpenClaw -> Webapp` document flow order in README.

## 9) Execution / Debug Rules

- Always run from the `webapp` folder for local execution.
- If you see `Could not import module "main"`, check the execution path first.

Example:

```powershell
cd webapp
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 10) Change Principles

- Solve with minimal changes.
- Avoid unrelated file or format modifications.
- When changing functionality, provide a simple verification method (reproduction/confirmation steps).

## 11) API Endpoints (Latest)

### Portfolio Router (`/api/portfolio`)
- `GET /api/portfolio` — List portfolio holdings
- `GET /api/portfolio/summary` — Domestic/overseas summary (added 2024-04-18: current price-based return)
- `POST /api/portfolio` — Add holding
- `PUT /api/portfolio/{ticker}` — Update holding
- `DELETE /api/portfolio/{ticker}` — Delete holding
- `GET /api/portfolio/health` — Router health check

### Watchlist Router (`/api/watchlist`)
- `GET /api/watchlist` — List watchlist items
- `GET /api/watchlist/enrich` — yfinance-based autofill (query: `ticker` or `company_name`, optional `lang=ko|en|ja|zh|fr`)
- `POST /api/watchlist` — Add watchlist item
- `PUT /api/watchlist/{ticker}` — Update watchlist item
- `DELETE /api/watchlist/{ticker}` — Delete watchlist item
- `GET /api/watchlist/health` — Router health check

### Reports Router (`/api/reports`)
- `GET /api/reports/daily` — Daily report list (date array)
- `GET /api/reports/daily/{date}` — Specific date report body
- `GET /api/reports/weekly` — Weekly report list (week array)
- `GET /api/reports/weekly/{week}` — Specific week report body
- `GET /api/reports/health` — Router health check

### Main App
- `GET /` — index.html (SPA)
- `GET /health` — App health check
- `GET /api/status` — Status (briefing script existence) + latest report keys
- `POST /api/run-briefing` — Generate briefing (runs generate_briefing.py)

## 12) Data Paths & Operations Info

### File Paths
```
~/investment-assistant/
├── data/
│   ├── portfolio.csv          # Portfolio (ticker, company_name, market, holding_status, quantity, avg_cost, currency, target_weight, thesis, risk_notes, priority)
│   ├── watchlist.csv          # Watchlist (ticker, company_name, market, watch_reason, ideal_entry, trigger_condition, invalidation, risk_notes, priority)
│   └── investor_profile.md    # Investor profile (for OpenClaw)
├── reports/
│   ├── daily/                 # Daily briefings (YYYY-MM-DD.md, generated daily at 09:00)
│   └── weekly/                # Weekly reports (YYYY-Wxx.md, generated every Monday at 09:10)
└── generate_briefing.py       # OpenClaw briefing generation script
```

### Webapp Server
- **Port**: 8001 (Azure VM) / 8000 (local development)
- **Run**: `cd webapp && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`
- **Service**: systemd `investment-webapp` (VM)

### CSV Field Definitions
**portfolio.csv**:
- `ticker`: Stock symbol (e.g., 000660, AAPL)
- `company_name`: Company name
- `market`: KRX | NYSE | NASDAQ
- `holding_status`: active | cash
- `quantity`: Holding quantity (integer)
- `avg_cost`: Average cost (float)
- `currency`: KRW | USD
- `target_weight`: Target weight (float, 0.0–1.0)
- `thesis`: Investment logic
- `risk_notes`: Risk factors
- `priority`: Priority (1–5)

**watchlist.csv**:
- `ticker`: Stock symbol
- `company_name`: Company name
- `market`: KRX | NYSE | NASDAQ
- `watch_reason`: Reason for watching
- `ideal_entry`: Target entry price
- `trigger_condition`: Entry trigger condition
- `invalidation`: Invalidation condition
- `risk_notes`: Risk factors
- `priority`: Priority (1–5)
