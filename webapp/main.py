from pathlib import Path
import logging
import subprocess
import sys
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from config import BRIEFING_SCRIPT, DAILY_REPORTS_DIR, WEEKLY_REPORTS_DIR
from routers.portfolio import router as portfolio_router
from routers.reports import router as reports_router
from routers.watchlist import router as watchlist_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Investment Assistant WebApp")

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # allow_origins=["*"]와 credentials=True 조합은 보안 취약점
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(reports_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info("%s %s %s %.3fs", request.method, request.url.path, response.status_code, elapsed)
    return response


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
        logger.warning("Briefing script not found: %s", BRIEFING_SCRIPT)
        raise HTTPException(status_code=404, detail="브리핑 스크립트를 찾을 수 없습니다")

    try:
        subprocess.Popen(
            [sys.executable, str(BRIEFING_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        logger.error("Failed to start briefing script: %s", exc)
        raise HTTPException(status_code=500, detail="브리핑 생성을 시작할 수 없습니다") from exc

    return {"status": "started", "message": "브리핑 생성을 시작했습니다."}


@app.get("/api/status")
async def get_status() -> dict[str, str | None]:
    return {
        "status": "ok",
        "last_daily": _latest_stem(DAILY_REPORTS_DIR),
        "last_weekly": _latest_stem(WEEKLY_REPORTS_DIR),
    }
