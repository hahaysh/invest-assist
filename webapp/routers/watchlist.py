import csv
import re
from pathlib import Path
import logging
import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import yfinance as yf

from config import WATCHLIST_CSV

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

logger = logging.getLogger(__name__)
_watchlist_lock = threading.Lock()

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

SUPPORTED_TEMPLATE_LANGUAGES = {"ko", "en", "ja", "zh", "fr"}


class WatchlistItem(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: str = Field(..., min_length=1, max_length=255)
    market: str = Field(..., min_length=1, max_length=20)
    watch_reason: str = Field(default="", max_length=2000)
    ideal_entry: float
    trigger_condition: str = Field(default="", max_length=2000)
    invalidation: str = Field(default="", max_length=2000)
    risk_notes: str = Field(default="", max_length=2000)
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


def _candidate_tickers(ticker: str) -> list[str]:
    normalized = _normalize_ticker(ticker)
    if re.fullmatch(r"\d{6}", normalized):
        return [f"{normalized}.KS", f"{normalized}.KQ", normalized]
    if normalized.endswith(".KS") or normalized.endswith(".KQ"):
        base = normalized.rsplit(".", 1)[0]
        return [normalized, base]
    return [normalized]


def _extract_price_from_ticker(yf_ticker: Any, info: dict[str, Any]) -> float | None:
    price = _extract_price(info)
    if price is not None:
        return price

    try:
        fast_info = getattr(yf_ticker, "fast_info", None)
        if fast_info:
            for key in ("lastPrice", "last_price", "regularMarketPrice"):
                value = fast_info.get(key) if hasattr(fast_info, "get") else None
                if value is not None:
                    return float(value)
    except Exception as exc:
        logger.debug("fast_info price fetch failed: %s", exc)

    try:
        hist = yf_ticker.history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            close_series = hist.get("Close")
            if close_series is not None and not close_series.dropna().empty:
                return float(close_series.dropna().iloc[-1])
    except Exception as exc:
        logger.debug("history price fetch failed: %s", exc)

    return None


def _headline(news_items: list[dict[str, Any]]) -> str:
    titles: list[str] = []
    for item in news_items[:2]:
        title = str(item.get("title") or "").strip()
        if title:
            titles.append(title)
    return " / ".join(titles)


def _normalize_language(lang: str | None) -> str:
    raw = (lang or "").strip().lower()
    if not raw:
        return "ko"
    base = raw.split("-", 1)[0].split("_", 1)[0]
    return base if base in SUPPORTED_TEMPLATE_LANGUAGES else "ko"


def _build_templates(company: str, market: str, price: float | None, news_summary: str, lang: str | None = None) -> dict[str, str]:
    language = _normalize_language(lang)
    is_krx = market == "KRX"

    if language == "en":
        reason = f"Monitor {company} valuation and growth" if is_krx and not news_summary else (
            f"{company} momentum: {news_summary}" if is_krx else (
                f"Track {company}'s growth sustainability" if not news_summary else f"{company} news momentum: {news_summary}"
            )
        )
        trigger = (
            f"Price holds near KRW {price:,.0f} with volume pickup" if is_krx and price is not None else
            "Upward earnings guidance or margin improvement" if is_krx else
            f"Price holds near ${price:,.2f} with earnings surprise" if price is not None else
            "Revenue re-acceleration and guidance upgrade"
        )
        invalidation = (
            "Core business growth slows or quarterly guidance is cut" if is_krx else
            "Growth deceleration or delay in AI/core business monetization"
        )
        risk = (
            "Policy/regulatory issues and valuation pressure" if is_krx else
            "Valuation risk, rates, and regulation"
        )
    elif language == "ja":
        reason = f"{company}のバリュエーション/成長を監視" if is_krx and not news_summary else (
            f"{company}のモメンタム: {news_summary}" if is_krx else (
                f"{company}の成長持続性を点検" if not news_summary else f"{company}のニュースモメンタム: {news_summary}"
            )
        )
        trigger = (
            f"価格が{price:,.0f}KRW付近で下支え + 出来高増加を確認" if is_krx and price is not None else
            "業績ガイダンス上方修正または利益率改善を確認" if is_krx else
            f"価格が${price:,.2f}付近で下支え + 決算サプライズを確認" if price is not None else
            "売上成長率の再加速とガイダンス上方修正を確認"
        )
        invalidation = (
            "主力事業の成長鈍化、または四半期ガイダンス下方修正" if is_krx else
            "成長率急減、またはAI/中核事業の収益化遅延"
        )
        risk = (
            "政策/規制リスクとバリュエーション負担" if is_krx else
            "バリュエーション負担、金利・規制リスク"
        )
    elif language == "zh":
        reason = f"跟踪{company}估值与增长" if is_krx and not news_summary else (
            f"{company}动量: {news_summary}" if is_krx else (
                f"评估{company}增长持续性" if not news_summary else f"{company}新闻动量: {news_summary}"
            )
        )
        trigger = (
            f"价格在{price:,.0f}KRW附近企稳且成交量放大" if is_krx and price is not None else
            "确认业绩指引上调或利润率改善" if is_krx else
            f"价格在${price:,.2f}附近企稳且业绩超预期" if price is not None else
            "收入增速回升并上调指引"
        )
        invalidation = (
            "核心业务增速放缓或季度指引下调" if is_krx else
            "增速明显下滑或AI/核心业务变现延迟"
        )
        risk = (
            "政策/监管因素与估值压力" if is_krx else
            "估值压力、利率与监管风险"
        )
    elif language == "fr":
        reason = f"Surveiller la valorisation et la croissance de {company}" if is_krx and not news_summary else (
            f"Momentum de {company} : {news_summary}" if is_krx else (
                f"Vérifier la durabilité de la croissance de {company}" if not news_summary else f"Momentum actualités de {company} : {news_summary}"
            )
        )
        trigger = (
            f"Le cours tient près de {price:,.0f} KRW avec hausse des volumes" if is_krx and price is not None else
            "Relèvement du guidance ou amélioration des marges" if is_krx else
            f"Le cours tient près de ${price:,.2f} avec surprise sur les résultats" if price is not None else
            "Rebond de la croissance du chiffre d'affaires et relèvement du guidance"
        )
        invalidation = (
            "Ralentissement du cœur d'activité ou baisse du guidance trimestriel" if is_krx else
            "Décélération de la croissance ou retard de monétisation IA/cœur d'activité"
        )
        risk = (
            "Enjeux politiques/réglementaires et pression de valorisation" if is_krx else
            "Risque de valorisation, taux et réglementation"
        )
    else:
        if is_krx:
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
    temp_path = file_path.with_suffix(".tmp")
    with _watchlist_lock:
        try:
            with temp_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=WATCHLIST_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            temp_path.replace(file_path)
        except OSError as exc:
            temp_path.unlink(missing_ok=True)
            logger.error("Failed to write watchlist CSV: %s", exc)
            raise HTTPException(status_code=500, detail="데이터 저장에 실패했습니다") from exc


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
async def enrich_watchlist_item(
    ticker: str | None = None,
    company_name: str | None = None,
    lang: str | None = None,
) -> dict[str, str | float | None]:
    resolved = _resolve_ticker(ticker, company_name)

    best: dict[str, Any] | None = None
    last_error: Exception | None = None

    for symbol in _candidate_tickers(resolved):
        try:
            yf_ticker = yf.Ticker(symbol)
            info = dict(yf_ticker.info or {})
            news_items = list(getattr(yf_ticker, "news", []) or [])
            price = _extract_price_from_ticker(yf_ticker, info)
            currency = str(info.get("currency") or "").upper()
            score = 0
            if info.get("longName") or info.get("shortName"):
                score += 2
            if price is not None:
                score += 3
            if symbol.endswith(".KS") or symbol.endswith(".KQ"):
                if currency == "KRW":
                    score += 2

            if (best is None) or (score > best["score"]):
                best = {
                    "symbol": symbol,
                    "info": info,
                    "news_items": news_items,
                    "price": price,
                    "currency": currency,
                    "score": score,
                }
        except Exception as exc:
            last_error = exc

    if best is None:
        raise HTTPException(status_code=502, detail=f"시세/뉴스 조회 실패: {last_error}")

    info = best["info"]
    news_items = best["news_items"]
    price = best["price"]
    used_symbol = best["symbol"]
    currency = best["currency"]

    company = str(
        info.get("longName")
        or info.get("shortName")
        or (company_name or "")
        or _display_ticker(used_symbol)
    ).strip()

    market = _infer_market(used_symbol, info)
    news_summary = _headline(news_items)
    templates = _build_templates(company, market, price, news_summary, lang=lang)

    return {
        "ticker": _display_ticker(used_symbol),
        "company_name": company,
        "market": market,
        "ideal_entry": price,
        "currency": currency or ("KRW" if market == "KRX" else "USD"),
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
