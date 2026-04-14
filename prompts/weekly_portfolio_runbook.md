# Weekly Portfolio Runbook

**출력 경로**: `reports/weekly/YYYY-Wxx.md`  
**실행 시각**: 매주 월요일 09:10 KST (전주 금요일 종가 기준)  
**참조 파일**: `data/investor_profile.md`, `data/portfolio.csv`, `data/watchlist.csv`

---

## STEP 0 — 날짜 확인 & 파일 경로 설정

```
WEEK_START = 전주 월요일 (YYYY-MM-DD)
WEEK_END   = 전주 금요일 (YYYY-MM-DD)
WEEK_NUM   = ISO 주차 (예: W15)
OUTPUT     = reports/weekly/{YYYY}-{WEEK_NUM}.md
```

---

## STEP 1 — 주간 데이터 수집

수집 대상 (전주 금요일 종가 vs 전전주 금요일 종가):
- 코스피 주간 등락률
- 코스닥 주간 등락률
- S&P500 주간 등락률
- 나스닥 주간 등락률
- USDKRW 주간 변화
- 미국 10Y 금리 주간 변화
- WTI 주간 변화
- VIX 주간 변화
- 벤치마크 수익률 (S&P500 + 코스피 가중 평균 or 지정 벤치마크)

---

## STEP 2 — 주간 리포트 생성 프롬프트

```
당신은 유승호 투자자의 개인 투자 비서입니다.
투자 스타일: value / quality / cash flow / shareholder return / margin of safety
주요 섹터: 한국(반도체·금융·자동차), 미국(금융·헬스케어·에너지·플랫폼)
참조 파일: data/investor_profile.md, data/portfolio.csv, data/watchlist.csv

분석 기간: {WEEK_START} ~ {WEEK_END}
주간 시장 데이터: [STEP 1 수집값 삽입]

아래 순서로 주간 포트폴리오 리포트를 작성하라.
형식: 실행용 bullet + 표 중심. 문장형 설명 최소화.

1. 주간 수익률 vs 벤치마크
   - 포트폴리오 추정 주간 수익률 (portfolio.csv 기준)
   - 벤치마크 수익률
   - 초과/미달 원인 1~2줄

2. 수익/손실 기여 종목 Top3 / Bottom3 (섹터·이유 포함)

3. 비중 변화 체크 (portfolio.csv 대비 실제 변동)

4. Thesis 점검 (각 종목: 유지 / 강화 / 약화 / 훼손)
   - 훼손 항목은 사유와 대응 방향 명시

5. 밸류에이션 변화 (주요 보유 종목 PER/PBR/FCF yield 변화 감지)

6. 리스크 맵 (현재 가장 큰 3가지 리스크, 포트폴리오 내 노출 종목)

7. 리밸런싱 후보 (과비중/과소비중 종목, 추천 방향)

8. 다음 주 주요 촉매 (실적 발표·경제지표·이벤트)

9. Watchlist 승격 후보 (트리거 근접 또는 thesis 강화된 종목)

10. 다음 주 액션 플랜 (매수/매도/모니터링/대기, 종목별 조건 명시)
```

---

## STEP 3 — 파일 저장

생성된 리포트를 `{OUTPUT}`에 저장.  
파일 헤더:
```markdown
# 주간 포트폴리오 리포트 — {YYYY} {WEEK_NUM}
_분석 기간: {WEEK_START} ~ {WEEK_END}_  
_생성 시각: {KST timestamp}_
```

---

## STEP 4 — Google Sheets 기록

시트: `주간포트폴리오리포트`  
스키마: `docs/google_sheets_schema.md` 참조  
기록 항목: 주간시작일, 주간종료일, 포트폴리오1주수익률, 벤치마크1주수익률, 초과수익률, 최고기여종목, 최저기여종목, 투자포인트변경여부, 리밸런싱후보, 다음주주요촉매, 주간액션요약, 리포트파일 경로, 생성시각  
**긴 본문 금지. 리포트 내용은 markdown 파일 링크로 대체.**

---

## STEP 5 — Telegram 전송

STEP 4 성공 시에만 실행.  
규칙: `prompts/telegram_summary_rules.md` 참조  
Weekly 요약 (6~10줄) 전송.

---

## STEP 6 — 로그 기록

`logs/weekly_YYYY-Wxx.log`에 실행 결과 저장:
- 실행 시각
- 분석 기간
- 출력 파일 경로
- Google Sheets 기록 결과 (성공/실패)
- Telegram 전송 결과 (성공/실패/스킵)
- 오류 메시지 (있을 경우)
