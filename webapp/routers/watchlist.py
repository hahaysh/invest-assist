import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
