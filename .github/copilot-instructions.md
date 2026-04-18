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
