import csv
from pathlib import Path
import logging
import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import yfinance as yf

from config import PORTFOLIO_CSV

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

logger = logging.getLogger(__name__)
_portfolio_lock = threading.Lock()

PORTFOLIO_COLUMNS = [
    "ticker",
    "company_name",
    "market",
    "holding_status",
    "quantity",
    "avg_cost",
    "currency",
    "target_weight",
    "thesis",
    "risk_notes",
    "priority",
]


class PortfolioItem(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: str = Field(..., min_length=1, max_length=255)
    market: str = Field(..., min_length=1, max_length=20)
    holding_status: str = Field(..., min_length=1, max_length=20)
    quantity: int
    avg_cost: float
    currency: str = Field(..., min_length=1, max_length=10)
    target_weight: float
    thesis: str = Field(default="", max_length=2000)
    risk_notes: str = Field(default="", max_length=2000)
    priority: int


class RegionSummary(BaseModel):
    count: int
    cost_krw: float
    market_value_krw: float
    profit_krw: float
    return_rate_krw: float
    cost_usd: float
    market_value_usd: float
    profit_usd: float
    return_rate_usd: float


class PortfolioSummary(BaseModel):
    total_count: int
    domestic_count: int
    overseas_count: int
    total_cost_krw: float
    total_market_value_krw: float
    total_profit_krw: float
    total_return_rate_krw: float
    total_cost_usd: float
    total_market_value_usd: float
    total_profit_usd: float
    total_return_rate_usd: float
    domestic: RegionSummary
    overseas: RegionSummary
    exchange_rate: float = 1300.0


def _normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _is_domestic_market(market: str) -> bool:
    return str(market).strip().upper() == "KRX"


def _ticker_candidates(ticker: str, market: str) -> list[str]:
    normalized = _normalize_ticker(ticker)
    if _is_domestic_market(market) and len(normalized) == 6 and normalized.isdigit():
        return [f"{normalized}.KS", f"{normalized}.KQ", normalized]
    return [normalized]


def _extract_price_from_fast_info(fast_info: Any) -> float | None:
    if not isinstance(fast_info, dict):
        return None
    for key in ("lastPrice", "regularMarketPrice", "previousClose"):
        value = fast_info.get(key)
        if value is not None:
            parsed = _to_float(value, default=-1.0)
            if parsed > 0:
                return parsed
    return None


def _fetch_current_price(ticker: str, market: str) -> float | None:
    for candidate in _ticker_candidates(ticker, market):
        try:
            stock = yf.Ticker(candidate)
            price = _extract_price_from_fast_info(getattr(stock, "fast_info", {}))
            if price is not None:
                return price

            hist = stock.history(period="1d")
            if not hist.empty:
                close_price = _to_float(hist["Close"].iloc[-1], default=-1.0)
                if close_price > 0:
                    return close_price
        except Exception as exc:
            logger.debug("Price fetch failed for %s: %s", candidate, exc)
            continue
    return None


def _empty_region_summary() -> RegionSummary:
    return RegionSummary(
        count=0,
        cost_krw=0.0,
        market_value_krw=0.0,
        profit_krw=0.0,
        return_rate_krw=0.0,
        cost_usd=0.0,
        market_value_usd=0.0,
        profit_usd=0.0,
        return_rate_usd=0.0,
    )


def _safe_return_rate(profit: float, cost: float) -> float:
    if cost <= 0:
        return 0.0
    return (profit / cost) * 100.0


def _accumulate_region_summary(summary: RegionSummary, currency: str, cost: float, market_value: float, profit: float) -> None:
    currency_norm = str(currency).strip().upper()
    if currency_norm == "USD":
        summary.cost_usd += cost
        summary.market_value_usd += market_value
        summary.profit_usd += profit
    else:
        summary.cost_krw += cost
        summary.market_value_krw += market_value
        summary.profit_krw += profit


def _finalize_region_summary(summary: RegionSummary) -> None:
    summary.return_rate_krw = _safe_return_rate(summary.profit_krw, summary.cost_krw)
    summary.return_rate_usd = _safe_return_rate(summary.profit_usd, summary.cost_usd)


def _fetch_exchange_rate() -> float:
    """yfinance에서 USD/KRW 환율 실시간 조회"""
    try:
        ticker = yf.Ticker("USDKRW=X")
        info = getattr(ticker, "info", {})
        current_price = info.get("currentPrice")
        if current_price is not None:
            rate = _to_float(current_price, default=-1.0)
            if rate > 0:
                return rate
    except Exception as exc:
        logger.warning("Exchange rate fetch failed: %s", exc)

    return 1300.0


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
    with _portfolio_lock:
        try:
            with temp_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=PORTFOLIO_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            temp_path.replace(file_path)
        except OSError as exc:
            temp_path.unlink(missing_ok=True)
            logger.error("Failed to write portfolio CSV: %s", exc)
            raise HTTPException(status_code=500, detail="데이터 저장에 실패했습니다") from exc


def _to_row(item: PortfolioItem) -> dict[str, str]:
    return {
        "ticker": _normalize_ticker(item.ticker),
        "company_name": item.company_name,
        "market": item.market,
        "holding_status": item.holding_status,
        "quantity": str(item.quantity),
        "avg_cost": str(item.avg_cost),
        "currency": item.currency,
        "target_weight": str(item.target_weight),
        "thesis": item.thesis,
        "risk_notes": item.risk_notes,
        "priority": str(item.priority),
    }


@router.get("/health")
async def portfolio_health() -> dict[str, str]:
    return {"status": "ok", "router": "portfolio"}


@router.get("")
async def get_portfolio() -> list[dict[str, str]]:
    return _read_rows(PORTFOLIO_CSV)


@router.get("/summary")
async def get_portfolio_summary() -> PortfolioSummary:
    rows = _read_rows(PORTFOLIO_CSV)
    active_rows = [
        row for row in rows
        if str(row.get("holding_status", "")).strip().lower() == "active"
        and _to_int(row.get("quantity", 0), default=0) > 0
    ]

    domestic = _empty_region_summary()
    overseas = _empty_region_summary()

    for row in active_rows:
        quantity = _to_int(row.get("quantity", 0), default=0)
        avg_cost = _to_float(row.get("avg_cost", 0), default=0.0)
        ticker = str(row.get("ticker", ""))
        market = str(row.get("market", ""))
        currency = str(row.get("currency", "KRW"))

        cost = quantity * avg_cost
        current_price = _fetch_current_price(ticker, market)
        effective_price = current_price if current_price is not None else avg_cost
        market_value = quantity * effective_price
        profit = market_value - cost

        region = domestic if _is_domestic_market(market) else overseas
        region.count += 1
        _accumulate_region_summary(region, currency, cost, market_value, profit)

    _finalize_region_summary(domestic)
    _finalize_region_summary(overseas)

    total_cost_krw = domestic.cost_krw + overseas.cost_krw
    total_market_value_krw = domestic.market_value_krw + overseas.market_value_krw
    total_profit_krw = domestic.profit_krw + overseas.profit_krw

    total_cost_usd = domestic.cost_usd + overseas.cost_usd
    total_market_value_usd = domestic.market_value_usd + overseas.market_value_usd
    total_profit_usd = domestic.profit_usd + overseas.profit_usd

    return PortfolioSummary(
        total_count=len(active_rows),
        domestic_count=domestic.count,
        overseas_count=overseas.count,
        total_cost_krw=total_cost_krw,
        total_market_value_krw=total_market_value_krw,
        total_profit_krw=total_profit_krw,
        total_return_rate_krw=_safe_return_rate(total_profit_krw, total_cost_krw),
        total_cost_usd=total_cost_usd,
        total_market_value_usd=total_market_value_usd,
        total_profit_usd=total_profit_usd,
        total_return_rate_usd=_safe_return_rate(total_profit_usd, total_cost_usd),
        domestic=domestic,
        overseas=overseas,
        exchange_rate=_fetch_exchange_rate(),
    )


@router.post("")
async def create_portfolio_item(item: PortfolioItem) -> dict[str, str]:
    rows = _read_rows(PORTFOLIO_CSV)
    ticker = _normalize_ticker(item.ticker)
    if any(_normalize_ticker(row.get("ticker", "")) == ticker for row in rows):
        raise HTTPException(status_code=400, detail=f"Ticker already exists: {ticker}")

    rows.append(_to_row(item))
    _write_rows(PORTFOLIO_CSV, rows)
    return {"status": "ok", "message": "Portfolio item created", "ticker": ticker}


@router.put("/{ticker}")
async def update_portfolio_item(ticker: str, item: PortfolioItem) -> dict[str, str]:
    rows = _read_rows(PORTFOLIO_CSV)
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

    _write_rows(PORTFOLIO_CSV, rows)
    return {"status": "ok", "message": "Portfolio item updated", "ticker": target}


@router.delete("/{ticker}")
async def delete_portfolio_item(ticker: str) -> dict[str, str]:
    rows = _read_rows(PORTFOLIO_CSV)
    target = _normalize_ticker(ticker)
    filtered_rows = [row for row in rows if _normalize_ticker(row.get("ticker", "")) != target]

    if len(filtered_rows) == len(rows):
        raise HTTPException(status_code=404, detail=f"Ticker not found: {target}")

    _write_rows(PORTFOLIO_CSV, filtered_rows)
    return {"status": "ok", "message": "Portfolio item deleted", "ticker": target}
