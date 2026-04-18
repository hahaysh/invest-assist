# Copilot Instructions For invest-assist

이 파일은 이 저장소에서 GitHub Copilot이 항상 따를 기본 규칙을 정의합니다.

## 1) 프로젝트 목적

- 이 저장소는 OpenClaw + FastAPI 웹앱 기반 투자 비서 시스템입니다.
- 운영 데이터는 `~/investment-assistant` 경로의 CSV/리포트 파일을 사용합니다.
- 웹앱은 `webapp` 폴더의 FastAPI 백엔드와 단일 SPA(`static/index.html`)로 구성됩니다.

## 2) 작업 우선순위

1. 기존 동작 보존 (회귀 방지)
2. 사용자 입력 데이터 무결성
3. 사용자 친화적 오류 메시지
4. README와 구현 동기화

## 3) 용어 규칙 (중요)

- 사용자 노출 UI/문서: `관심종목` 사용
- 내부 API/경로/파일명: `watchlist` 유지
- 리포트 표시 용어:
  - `보유 종목 현황` 대신 `포트 폴리오 현황`
  - `Thesis` 대신 `투자논리`

## 4) 자동채움(autofill) 규칙

- 기존 입력값을 덮어쓰지 말고, 빈 필드만 채운다.
- 자동채움 진행 중 저장/취소 버튼을 비활성화한다.
- 자동채움 완료/실패 후 버튼 상태를 반드시 복구한다.
- 수정 모드와 신규 모드 동작 차이를 유지한다.

## 5) 검증 규칙

- 숫자 필드 입력은 문자열이라도 숫자 변환 후 검증한다.
- 정수/실수 필드 타입 검증 실패 시 사용자 이해 가능한 메시지를 반환한다.
- API 오류 detail은 UI에 그대로 객체 형태로 노출하지 않는다.

## 6) 백엔드 규칙

- FastAPI 라우터 책임을 유지한다:
  - `routers/reports.py`: 리포트 목록/본문
  - `routers/portfolio.py`: 포트폴리오 CRUD
  - `routers/watchlist.py`: 관심종목 CRUD + enrich
- 파일 I/O 실패는 HTTPException으로 명시적으로 처리한다.
- CSV 파일이 없을 때는 가능한 범위에서 안정적으로 동작하도록 한다.

## 7) 프론트엔드 규칙

- 주요 상태 변수(`portfolioAutofillLoading`, `watchlistAutofillLoading`)를 기준으로 버튼/모달 제어를 유지한다.
- API 호출은 공통 fetch 래퍼와 일관된 에러 처리 패턴을 사용한다.
- 대시보드 리포트 렌더링 시 용어 치환 규칙을 유지한다.

## 8) 문서 업데이트 규칙

아래 항목이 변경되면 `README.md`도 함께 업데이트한다.

- 사용자 기능 흐름
- API 엔드포인트
- 용어 정책
- 배포/실행 절차

README는 `OpenClaw -> Webapp` 순서의 문서 동선을 유지한다.

## 9) 실행/디버그 규칙

- 로컬 실행 시 반드시 `webapp` 폴더에서 실행한다.
- `Could not import module "main"` 오류가 보이면 실행 경로를 먼저 점검한다.

예시:

```powershell
cd webapp
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 10) 변경 원칙

- 최소 변경으로 해결한다.
- 관련 없는 파일/포맷 변경을 피한다.
- 기능 변경 시 간단한 검증 방법(재현/확인 단계)을 함께 제시한다.

## 11) API 엔드포인트 (최신)

### Portfolio Router (`/api/portfolio`)
- `GET /api/portfolio` — 포트폴리오 목록 조회
- `GET /api/portfolio/summary` — 국내/해외 요약 (2024-4-18 추가: 현재가 기반 수익률)
- `POST /api/portfolio` — 종목 추가
- `PUT /api/portfolio/{ticker}` — 종목 수정
- `DELETE /api/portfolio/{ticker}` — 종목 삭제
- `GET /api/portfolio/health` — 라우터 헬스체크

### Watchlist Router (`/api/watchlist`)
- `GET /api/watchlist` — 관심종목 목록 조회
- `GET /api/watchlist/enrich` — yfinance 기반 자동채움 (query: ticker 또는 company_name)
- `POST /api/watchlist` — 관심종목 추가
- `PUT /api/watchlist/{ticker}` — 관심종목 수정
- `DELETE /api/watchlist/{ticker}` — 관심종목 삭제
- `GET /api/watchlist/health` — 라우터 헬스체크

### Reports Router (`/api/reports`)
- `GET /api/reports/daily` — 일일 리포트 목록 (date 배열)
- `GET /api/reports/daily/{date}` — 특정 일자 리포트 본문
- `GET /api/reports/weekly` — 주간 리포트 목록 (week 배열)
- `GET /api/reports/weekly/{week}` — 특정 주 리포트 본문
- `GET /api/reports/health` — 라우터 헬스체크

### Main App
- `GET /` — index.html (SPA)
- `GET /health` — 앱 헬스체크
- `GET /api/status` — 상태(브리핑 스크립트 존재 여부) + 최신 리포트 키
- `POST /api/run-briefing` — 브리핑 생성 (generate_briefing.py 실행)

## 12) 데이터 경로 & 운영 정보

### 파일 경로
```
~/investment-assistant/
├── data/
│   ├── portfolio.csv          # 포트폴리오 (ticker, company_name, market, holding_status, quantity, avg_cost, currency, target_weight, thesis, risk_notes, priority)
│   ├── watchlist.csv          # 관심종목 (ticker, company_name, market, watch_reason, ideal_entry, trigger_condition, invalidation, risk_notes, priority)
│   └── investor_profile.md    # 투자자 프로필 (OpenClaw 용)
├── reports/
│   ├── daily/                 # 일일 브리핑 (YYYY-MM-DD.md, 매일 09:00 생성)
│   └── weekly/                # 주간 리포트 (YYYY-Wxx.md, 매주 월요일 09:10 생성)
└── generate_briefing.py       # OpenClaw 브리핑 생성 스크립트
```

### 웹앱 서버
- **포트**: 8001 (Azure VM) / 8000 (로컬 개발)
- **실행**: `cd webapp && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`
- **서비스**: systemd `investment-webapp` (VM)

### CSV 필드 정의
**portfolio.csv**:
- `ticker`: 상장 심볼 (예: 000660, AAPL)
- `company_name`: 종목명
- `market`: KRX | NYSE | NASDAQ
- `holding_status`: active | cash
- `quantity`: 보유 수량 (정수)
- `avg_cost`: 평균 단가 (실수)
- `currency`: KRW | USD
- `target_weight`: 목표 비중 (실수, 0.0~1.0)
- `thesis`: 투자 논리
- `risk_notes`: 위험 요소
- `priority`: 우선순위 (1~5)

**watchlist.csv**:
- `ticker`: 상장 심볼
- `company_name`: 종목명
- `market`: KRX | NYSE | NASDAQ
- `watch_reason`: 관심 이유
- `ideal_entry`: 진입 목표가
- `trigger_condition`: 진입 조건
- `invalidation`: 무효 조건
- `risk_notes`: 위험 요소
- `priority`: 우선순위 (1~5)
