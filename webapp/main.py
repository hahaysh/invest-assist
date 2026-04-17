from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import BRIEFING_SCRIPT, DAILY_REPORTS_DIR, WEEKLY_REPORTS_DIR
from routers.portfolio import router as portfolio_router
from routers.reports import router as reports_router
from routers.watchlist import router as watchlist_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Investment Assistant WebApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _latest_stem(report_dir: Path) -> str | None:
    if not report_dir.exists() or not report_dir.is_dir():
        return None
    files = sorted(report_dir.glob("*.md"), key=lambda p: p.stem, reverse=True)
    if not files:
        return None
    return files[0].stem


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/run-briefing")
async def run_briefing() -> dict[str, str]:
    if not BRIEFING_SCRIPT.exists() or not BRIEFING_SCRIPT.is_file():
        raise HTTPException(status_code=404, detail=f"Briefing script not found: {BRIEFING_SCRIPT}")

    try:
        subprocess.Popen(
            [sys.executable, str(BRIEFING_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start briefing script: {exc}") from exc

    return {"status": "started", "message": "브리핑 생성을 시작했습니다."}


@app.get("/api/status")
async def get_status() -> dict[str, str | None]:
    return {
        "status": "ok",
        "last_daily": _latest_stem(DAILY_REPORTS_DIR),
        "last_weekly": _latest_stem(WEEKLY_REPORTS_DIR),
    }
