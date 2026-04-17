from pathlib import Path
import re

from fastapi import APIRouter, HTTPException

from config import DAILY_REPORTS_DIR, WEEKLY_REPORTS_DIR

router = APIRouter(prefix="/api/reports", tags=["reports"])

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WEEK_PATTERN = re.compile(r"^\d{4}-W\d{2}$")


def _list_markdown_files(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []  # 디렉토리 없으면 빈 리스트 반환
    return sorted(directory.glob("*.md"), key=lambda p: p.stem, reverse=True)


def _read_report(directory: Path, stem: str) -> str:
    file_path = directory / f"{stem}.md"
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Report not found: {file_path.name}")
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {exc}") from exc


@router.get("/health")
async def reports_health() -> dict[str, str]:
    return {"status": "ok", "router": "reports"}


@router.get("/daily")
async def list_daily_reports() -> list[dict[str, str]]:
    files = _list_markdown_files(DAILY_REPORTS_DIR)
    result: list[dict[str, str]] = []
    for file_path in files:
        if _DATE_PATTERN.fullmatch(file_path.stem):
            result.append({"date": file_path.stem, "filename": file_path.name})
    return result


@router.get("/weekly")
async def list_weekly_reports() -> list[dict[str, str]]:
    files = _list_markdown_files(WEEKLY_REPORTS_DIR)
    result: list[dict[str, str]] = []
    for file_path in files:
        if _WEEK_PATTERN.fullmatch(file_path.stem):
            result.append({"week": file_path.stem, "filename": file_path.name})
    return result


@router.get("/daily/{date}")
async def get_daily_report(date: str) -> dict[str, str]:
    if not _DATE_PATTERN.fullmatch(date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    content = _read_report(DAILY_REPORTS_DIR, date)
    return {"date": date, "content": content}


@router.get("/weekly/{week}")
async def get_weekly_report(week: str) -> dict[str, str]:
    if not _WEEK_PATTERN.fullmatch(week):
        raise HTTPException(status_code=400, detail="Invalid week format. Use YYYY-WNN")
    content = _read_report(WEEKLY_REPORTS_DIR, week)
    return {"week": week, "content": content}
