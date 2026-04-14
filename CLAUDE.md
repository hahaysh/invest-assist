# 개인 투자 비서 — Claude Code 프로젝트

## 역할
유승호 투자자의 일일/주간 투자 브리핑을 자동 생성하고, Google Sheets에 누적 저장하며, Telegram으로 핵심 요약을 전달한다.

## 핵심 파일 참조
- `data/investor_profile.md` — 투자 철학, 스타일, 리스크 규칙 (브리핑 프롬프트 작성 시 항상 참조)
- `data/portfolio.csv` — 보유 종목 현황 (수량/평단은 파일에서 읽음, 프롬프트에 반복 금지)
- `data/watchlist.csv` — 관찰 종목 (진입 조건/트리거 파일에서 읽음)
- `prompts/daily_briefing_runbook.md` — 일일 브리핑 실행 절차
- `prompts/weekly_portfolio_runbook.md` — 주간 리포트 실행 절차
- `prompts/telegram_summary_rules.md` — Telegram 전송 규칙

## 출력 파일 경로
- 일일 브리핑: `reports/daily/YYYY-MM-DD.md`
- 주간 리포트: `reports/weekly/YYYY-Wxx.md`
- 실행 로그: `logs/`

## 운영 원칙
1. 브리핑 프롬프트에 종목별 수량·평단을 반복하지 않는다. 파일 참조로 대체.
2. Google Sheets에는 숫자와 짧은 메모만 저장. 긴 본문은 markdown 파일 링크.
3. Telegram 전송은 Google Sheets 기록 성공 후에만 실행.
4. 투자 스타일과 섹터 그룹 기준으로 분석 프레임을 유지한다.

## 환경 변수
`config/secrets.env.example`을 복사해 `config/secrets.env`를 만들고 실제 값을 채울 것.

## 스케줄
- 매일 09:00 KST: `prompts/daily_briefing_runbook.md` 실행
- 매주 월요일 09:10 KST: `prompts/weekly_portfolio_runbook.md` 실행
