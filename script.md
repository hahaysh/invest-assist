[원샷 프롬프트] 개인 투자 비서용 Claude Code 프로젝트 세팅

개인 투자 비서용 Claude Code 프로젝트를 세팅해라.

목표
매일 09:00 KST 일일 투자 브리핑 생성
매주 월요일 09:10 KST 주간 포트폴리오 리포트 생성
상세 분석은 markdown 파일에 저장
누적 시황 데이터는 Google Sheets에 짧은 구조화 값만 저장
핵심 요약은 Telegram으로 전송

중요 원칙
일일/주간 브리핑 프롬프트에는 종목별 비중, 수량, 평단을 장황하게 반복하지 말 것
투자 스타일, 대표 섹터 그룹, 기존 data 파일 참조만으로 동작하게 구성할 것
portfolio.csv와 watchlist.csv는 실제 투자자처럼 현실적으로 작성하되, thesis와 risk_notes는 짧고 구체적으로 유지할 것
상세 보고서는 markdown, Google Sheets는 누적 데이터 저장용이며 긴 본문을 넣지 말 것

프로젝트 구조 생성
CLAUDE.md
data/investor_profile.md
data/portfolio.csv
data/watchlist.csv
prompts/daily_briefing_runbook.md
prompts/weekly_portfolio_runbook.md
prompts/telegram_summary_rules.md
config/secrets.env.example
reports/daily/
reports/weekly/
logs/
docs/google_sheets_manual_setup.md
docs/telegram_manual_setup.md
docs/google_sheets_schema.md

투자자 프로필 작성
이름: 유승호
투자 경력: 3년
자산 통화: KRW + USD
위험 성향: 공격적 중립
스타일: value, quality, cash flow, shareholder return, margin of safety
섹션은 다음 순서로 작성:Basic Info, Investment Philosophy & Style, Preferred Sectors / Themes, Daily Reference Metrics, Current Investment Themes, Risk Management Rules, Briefing Highlights

portfolio.csv 작성
컬럼: ticker,company_name,market,holding_status,quantity,avg_cost,currency,target_weight,thesis,risk_notes,priority
포트폴리오는 한국+미국 분산 가치투자자 포맷으로 작성
한국은 반도체/금융/자동차 중심
미국은 금융/헬스케어/에너지/고품질 플랫폼 중심
실제 투자자처럼 보이는 수량, 평단, 목표비중, thesis, risk_notes를 작성
CASH 행도 포함할 것
만약 기존 고정 샘플 데이터가 이미 있으면 그것을 우선 반영하고, 없으면 위 원칙으로 현실적으로 추론할 것

watchlist.csv 작성
컬럼: ticker,company_name,market,watch_reason,ideal_entry,trigger_condition,invalidation,risk_notes,priority
관찰 종목은 한국/미국 혼합으로 구성
매수 감시 이유, 이상적 진입 조건, 트리거, 무효화 조건을 짧고 실전적으로 작성

daily_briefing_runbook.md 작성
출력 파일 경로: reports/daily/YYYY-MM-DD.md
반드시 포함:시장 요약과 원인 분석, 미국-한국 시장 연결 해석, 금리/달러/USDKRW/원자재/변동성, 섹터 로테이션, 보유 종목 영향, watchlist 영향, 당일 주요 일정, bullish/base/bear 시나리오, 액션 아이디어, thesis 변화 여부
길게 설명하지 말고, 실행용 runbook 형태로 작성할 것
브리핑 프롬프트는 투자 스타일, 대표 섹터 그룹, data 파일 참조 중심으로 짧게 유지할 것

weekly_portfolio_runbook.md 작성
출력 파일 경로: reports/weekly/YYYY-Wxx.md
반드시 포함:주간 수익률 vs 벤치마크, 수익/손실 기여 종목, 비중 변화, thesis 유지/변경/훼손, 밸류에이션 변화, 리스크 맵, 리밸런싱 후보, 다음 주 촉매, watchlist 승격 후보, 다음 주 액션 플랜
일일 runbook과 동일하게 실행형 문서로 작성할 것

telegram_summary_rules.md 작성
Daily 요약: 5~8줄
Weekly 요약: 6~10줄
Google Sheets 기록 성공 후에만 전송
핵심은 “오늘 볼 것”, “포트폴리오 중요 변화”, “즉시 확인할 리스크”

Google Sheets 설계
docs/google_sheets_schema.md에 아래 스키마를 정리할 것
탭 이름은 아래 중 하나로 구성:권장: 일일브리핑, 주간포트폴리오리포트 또는: DailyBriefings, WeeklyPortfolioReports
일일브리핑 컬럼: 날짜, 실행시각_KST, 시장국면, 코스피종가, 코스피1일등락률, 코스피1일등락률, 코스닥종가, 코스닥1일등락률, S&P500종가, S&P5001일등락률, 나스닥종가, 나스닥1일등락률, 원달러환율, 미국10년물금리, 달러인덱스, WTI, 금가격, VIX, 강세섹터, 약세섹터, 핵심동인Top3, 포트폴리오액션요약, 오늘주요일정, 리포트파일, 생성시각
주간포트폴리오리포트 컬럼: 주간시작일, 주간종료일, 포트폴리오1주수익률, 벤치마크1주수익률, 초과수익률, 최고기여종목, 최저기여종목, 투자포인트변경여부, 리밸런싱후보, 다음주주요촉매, 주간액션요약, 리포트파일, 생성시각
시트에는 숫자/짧은 메모만 저장하고 긴 본문은 markdown 파일 링크로 대체할 것

Google Sheets / Telegram 연동
credentials가 있으면 실제 연결 시도
credentials가 없으면 config/secrets.env.example에 placeholder 작성
docs/google_sheets_manual_setup.md와 docs/telegram_manual_setup.md에 비개발자 기준의 수동 설정 절차를 자세히 작성
secrets.env.example에는 최소한 아래 placeholder를 포함: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_SHEETS_SPREADSHEET_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_TIMEZONE=Asia/Seoul

스케줄 작업
daily-investment-briefing : 매일 09:00 KST
weekly-portfolio-report : 매주 월요일 09:10 KST
생성 가능하면 실제 생성
불가능하면 이유와 가장 가까운 대체 방법을 명확히 기록

최종 보고 형식
Completed tasks
Pending tasks
Minimal required values
Scheduled tasks
How to run daily job
How to run weekly job
설명보다 실행을 우선하고, 이미 만든 파일을 다시 장황하게 요약하지 마. 실제 생성 결과 중심으로만 보고해.