# Daily Briefing Runbook

**출력 경로**: `reports/daily/YYYY-MM-DD.md`  
**실행 시각**: 매일 09:00 KST (전일 장 마감 데이터 기준)  
**참조 파일**: `data/investor_profile.md`, `data/portfolio.csv`, `data/watchlist.csv`

---

## STEP 0 — 날짜 확인 & 파일 경로 설정

```
TODAY = 실행일 (YYYY-MM-DD, KST)
OUTPUT = reports/daily/{TODAY}.md
```

---

## STEP 1 — 시장 데이터 수집

수집 대상 (전일 종가 기준):
- 코스피 종가 / 등락률
- 코스닥 종가 / 등락률
- S&P500 종가 / 등락률
- 나스닥 종가 / 등락률
- USDKRW 환율
- 미국 10Y 국채 금리
- 달러인덱스 (DXY)
- WTI 유가
- 금 현물가
- VIX

---

## STEP 2 — 브리핑 생성 프롬프트

아래 프롬프트를 Claude에 전달한다. 포트폴리오 세부 수치는 파일을 참조하고 프롬프트에 직접 나열하지 않는다.

```
당신은 유승호 투자자의 개인 투자 비서입니다.
투자 스타일: value / quality / cash flow / shareholder return / margin of safety
주요 섹터: 한국(반도체·금융·자동차), 미국(금융·헬스케어·에너지·플랫폼)
참조 파일: data/investor_profile.md, data/portfolio.csv, data/watchlist.csv

오늘 날짜: {TODAY}
시장 데이터: [STEP 1 수집값 삽입]

아래 순서로 일일 투자 브리핑을 작성하라.
형식: 실행용 bullet 위주. 문장형 설명 최소화.

1. 시장 요약 & 원인 분석 (3~5 bullet)
2. 미국↔한국 시장 연결 해석 (2~3 bullet)
3. 금리·달러·USDKRW·원자재·VIX 체크 (각 1줄)
4. 섹터 로테이션 신호 (강세/약세 섹터, 이유 1줄씩)
5. 보유 종목 영향 (portfolio.csv 참조, 섹터별 그룹으로 묶어서)
6. Watchlist 영향 (watchlist.csv 참조, 트리거 근접 종목 우선)
7. 당일 주요 일정 (경제지표 발표·실적·이벤트)
8. 시나리오 (Bullish / Base / Bear 각 2줄)
9. 액션 아이디어 (매수·매도·대기·모니터링 구분)
10. Thesis 변화 체크 (훼손 있으면 종목명과 사유 명시, 없으면 "변화 없음")
```

---

## STEP 3 — 파일 저장

생성된 브리핑을 `{OUTPUT}`에 저장.  
파일 헤더 형식:
```markdown
# 일일 투자 브리핑 — {TODAY}
_생성 시각: {KST timestamp}_
```

---

## STEP 4 — Google Sheets 기록

시트: `일일브리핑`  
스키마: `docs/google_sheets_schema.md` 참조  
기록 항목: 날짜, 실행시각_KST, 시장국면, 주요 지수·지표값, 강세/약세섹터, 핵심동인Top3, 포트폴리오액션요약, 오늘주요일정, 리포트파일 경로, 생성시각  
**긴 본문은 절대 시트에 기록하지 않는다.**

기록 성공 여부를 확인한다.

---

## STEP 5 — Telegram 전송

STEP 4 성공 시에만 실행.  
규칙: `prompts/telegram_summary_rules.md` 참조  
Daily 요약 (5~8줄) 전송.

---

## STEP 6 — 로그 기록

`logs/daily_YYYY-MM-DD.log`에 실행 결과 저장:
- 실행 시각
- 출력 파일 경로
- Google Sheets 기록 결과 (성공/실패)
- Telegram 전송 결과 (성공/실패/스킵)
- 오류 발생 시 오류 메시지
