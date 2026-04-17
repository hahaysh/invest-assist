import csv
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf

from config import WATCHLIST_CSV

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

WATCHLIST_COLUMNS = [
    "ticker",
    "company_name",
    "market",
    "watch_reason",
    "ideal_entry",
    "trigger_condition",
    "invalidation",
    "risk_notes",
    "priority",
]


class WatchlistItem(BaseModel):
    ticker: str
    company_name: str
    market: str
    watch_reason: str
    ideal_entry: float
    trigger_condition: str
    invalidation: str
    risk_notes: str
    priority: int


def _normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _display_ticker(ticker: str) -> str:
    normalized = _normalize_ticker(ticker)
    if normalized.endswith(".KS") or normalized.endswith(".KQ"):
        return normalized.rsplit(".", 1)[0]
    return normalized


def _resolve_ticker(ticker: str | None, company_name: str | None) -> str:
    if ticker:
        return _normalize_ticker(ticker)

    query = (company_name or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="ticker 또는 company_name 중 하나는 필요합니다.")

    try:
        search = yf.Search(query, max_results=5)
        quotes = getattr(search, "quotes", []) or []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"종목 검색 실패: {exc}") from exc

    if not quotes:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {query}")

    symbol = str(quotes[0].get("symbol") or "").strip()
    if not symbol:
        raise HTTPException(status_code=404, detail=f"종목 심볼을 찾을 수 없습니다: {query}")

    return _normalize_ticker(symbol)


def _infer_market(ticker: str, info: dict[str, Any]) -> str:
    exchange = str(info.get("exchange") or info.get("fullExchangeName") or "").upper()
    market = str(info.get("market") or "").upper()
    normalized = _normalize_ticker(ticker)

    if normalized.endswith(".KS") or normalized.endswith(".KQ"):
        return "KRX"
    if re.fullmatch(r"\d{6}", normalized):
        return "KRX"
    if exchange in {"KSC", "KOSPI", "KOE", "KOSDAQ"}:
        return "KRX"
    if exchange in {"NMS", "NAS", "NGM", "NASDAQ", "NCM", "NGS"} or "NASDAQ" in exchange:
        return "NASDAQ"
    if exchange in {"NYQ", "NYS", "NYSE"} or "NYSE" in exchange:
        return "NYSE"
    if market in {"US_MARKET", "US"}:
        return "NASDAQ"
    return "US" if re.fullmatch(r"[A-Z]{1,5}", normalized) else "KRX"


def _extract_price(info: dict[str, Any]) -> float | None:
    for key in ("currentPrice", "regularMarketPrice", "previousClose"):
        value = info.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def _headline(news_items: list[dict[str, Any]]) -> str:
    titles: list[str] = []
    for item in news_items[:2]:
        title = str(item.get("title") or "").strip()
        if title:
            titles.append(title)
    return " / ".join(titles)


def _build_templates(company: str, market: str, price: float | None, news_summary: str) -> dict[str, str]:
    if market == "KRX":
        reason = f"{company} 밸류/성장 모니터링" if not news_summary else f"{company} 모멘텀: {news_summary}"
        trigger = (
            f"가격 {price:,.0f}원 부근 지지 + 거래량 증가 확인"
            if price is not None
            else "실적 가이던스 상향 또는 이익률 개선 확인"
        )
        invalidation = "핵심 사업 성장 둔화 또는 분기 실적 가이던스 하향"
        risk = "정책/규제 이슈 및 밸류에이션 부담"
    else:
        reason = f"{company} 성장 지속 여부 점검" if not news_summary else f"{company} 뉴스 모멘텀: {news_summary}"
        trigger = (
            f"가격 ${price:,.2f} 부근 지지 + 실적 서프라이즈 확인"
            if price is not None
            else "매출 성장률 반등 및 가이던스 상향 확인"
        )
        invalidation = "성장률 급감 또는 AI/핵심 사업 수익화 지연"
        risk = "밸류에이션 부담, 금리 및 규제 리스크"

    return {
        "watch_reason": reason,
        "trigger_condition": trigger,
        "invalidation": invalidation,
        "risk_notes": risk,
    }


def _read_rows(file_path: Path) -> list[dict[str, str]]:
    if not file_path.exists() or not file_path.is_file():
        return []  # 파일 없으면 빈 리스트 반환
    
    try:
        with file_path.open("r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            return list(reader) if reader.fieldnames else []
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {exc}") from exc


def _write_rows(file_path: Path, rows: list[dict[str, str]]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=WATCHLIST_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write CSV: {exc}") from exc


def _to_row(item: WatchlistItem) -> dict[str, str]:
    return {
        "ticker": _normalize_ticker(item.ticker),
        "company_name": item.company_name,
        "market": item.market,
        "watch_reason": item.watch_reason,
        "ideal_entry": str(item.ideal_entry),
        "trigger_condition": item.trigger_condition,
        "invalidation": item.invalidation,
        "risk_notes": item.risk_notes,
        "priority": str(item.priority),
    }


@router.get("/health")
async def watchlist_health() -> dict[str, str]:
    return {"status": "ok", "router": "watchlist"}


@router.get("/enrich")
async def enrich_watchlist_item(ticker: str | None = None, company_name: str | None = None) -> dict[str, str | float | None]:
    resolved = _resolve_ticker(ticker, company_name)

    try:
        yf_ticker = yf.Ticker(resolved)
        info = dict(yf_ticker.info or {})
        news_items = list(getattr(yf_ticker, "news", []) or [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"시세/뉴스 조회 실패: {exc}") from exc

    company = str(
        info.get("longName")
        or info.get("shortName")
        or (company_name or "")
        or _display_ticker(resolved)
    ).strip()
    market = _infer_market(resolved, info)
    price = _extract_price(info)
    news_summary = _headline(news_items)
    templates = _build_templates(company, market, price, news_summary)

    return {
        "ticker": _display_ticker(resolved),
        "company_name": company,
        "market": market,
        "ideal_entry": price,
        "watch_reason": templates["watch_reason"],
        "trigger_condition": templates["trigger_condition"],
        "invalidation": templates["invalidation"],
        "risk_notes": templates["risk_notes"],
        "news_summary": news_summary,
    }


@router.get("")
async def get_watchlist() -> list[dict[str, str]]:
    return _read_rows(WATCHLIST_CSV)


@router.post("")
async def create_watchlist_item(item: WatchlistItem) -> dict[str, str]:
    rows = _read_rows(WATCHLIST_CSV)
    ticker = _normalize_ticker(item.ticker)
    if any(_normalize_ticker(row.get("ticker", "")) == ticker for row in rows):
        raise HTTPException(status_code=400, detail=f"Ticker already exists: {ticker}")

    rows.append(_to_row(item))
    _write_rows(WATCHLIST_CSV, rows)
    return {"status": "ok", "message": "Watchlist item created", "ticker": ticker}


@router.put("/{ticker}")
async def update_watchlist_item(ticker: str, item: WatchlistItem) -> dict[str, str]:
    rows = _read_rows(WATCHLIST_CSV)
    target = _normalize_ticker(ticker)
    updated = False

    for idx, row in enumerate(rows):
        if _normalize_ticker(row.get("ticker", "")) == target:
            rows[idx] = _to_row(item)
            rows[idx]["ticker"] = target
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Ticker not found: {target}")

    _write_rows(WATCHLIST_CSV, rows)
    return {"status": "ok", "message": "Watchlist item updated", "ticker": target}


@router.delete("/{ticker}")
async def delete_watchlist_item(ticker: str) -> dict[str, str]:
    rows = _read_rows(WATCHLIST_CSV)
    target = _normalize_ticker(ticker)
    filtered_rows = [row for row in rows if _normalize_ticker(row.get("ticker", "")) != target]

    if len(filtered_rows) == len(rows):
        raise HTTPException(status_code=404, detail=f"Ticker not found: {target}")

    _write_rows(WATCHLIST_CSV, filtered_rows)
    return {"status": "ok", "message": "Watchlist item deleted", "ticker": target}
