# Telegram 수동 설정 절차

> 개발자가 아닌 분도 따라할 수 있도록 단계별로 작성했습니다.

---

## Part 1: Telegram Bot 생성

### 1-1. BotFather로 봇 만들기
1. 텔레그램 앱 열기
2. 검색창에 `@BotFather` 검색 → 공식 봇 선택 (파란 체크 표시)
3. `/start` 입력
4. `/newbot` 입력
5. 봇 이름 입력 (예: `유승호 투자 비서`)
6. 봇 username 입력 (영문, 언더스코어, 숫자만, 끝에 `bot` 필수)  
   예: `yoo_invest_assistant_bot`
7. 생성 완료 후 나타나는 **HTTP API Token** 복사
   → `config/secrets.env`의 `TELEGRAM_BOT_TOKEN`에 저장

---

## Part 2: Chat ID 확인

### 방법 A: 개인 채팅 (본인에게 전송)
1. 위에서 만든 봇을 텔레그램에서 검색해 채팅 시작 (`/start` 입력)
2. 브라우저에서 아래 URL 접속 (TOKEN은 실제 값으로 교체):
   ```
   https://api.telegram.org/bot{TOKEN}/getUpdates
   ```
3. 응답 JSON에서 `"chat":{"id":123456789}` 부분의 숫자가 Chat ID
4. `TELEGRAM_CHAT_ID`에 저장

### 방법 B: 그룹 채팅 (그룹방으로 전송하려는 경우)
1. 텔레그램 그룹 생성 후 봇을 그룹에 초대
2. 그룹에서 아무 메시지 전송
3. 위 getUpdates URL로 확인 → `"chat":{"id":-100xxxxxxxxxx}` (음수)
4. 음수 포함해서 `TELEGRAM_CHAT_ID`에 저장

---

## Part 3: 봇 권한 설정 (그룹 사용 시)

그룹 관리자 설정에서 봇을 관리자로 지정하면 메시지 전송이 더 안정적입니다.

---

## Part 4: 연결 테스트

터미널에서 아래 명령으로 봇 동작 확인:

```bash
curl -s -X POST "https://api.telegram.org/bot{TOKEN}/sendMessage" \
  -d "chat_id={CHAT_ID}" \
  -d "text=투자 비서 봇 연결 테스트 성공 ✅"
```

메시지가 수신되면 설정 완료.

---

## Part 5: secrets.env 완성 확인

```env
TELEGRAM_BOT_TOKEN=7123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

---

## 전송 규칙 참고
- 전송 내용 형식: `prompts/telegram_summary_rules.md` 참조
- Google Sheets 기록 성공 후에만 전송됩니다
- 실패 시 `logs/` 폴더에 오류 내용이 기록됩니다
