"""FaceProof API — FastAPI application entrypoint.

Pipeline: FACE -> SEARCH -> MATCH -> FINGERPRINT -> BLOCKCHAIN -> VERIFY

Docs are served at /api/docs (Swagger) and /api/redoc.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_blockchain,
    routes_health,
    routes_pipeline,
    routes_scan,
    routes_search,
    routes_verify,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db import init_db
from app.services.blockchain_service import get_blockchain_service
from app.services.face_service import get_face_service

configure_logging()
log = get_logger("faceproof")

# Optional rate limiting via slowapi (degrades gracefully if not installed).
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
except Exception:  # noqa: BLE001
    limiter = None

DISCLAIMER = (
    "Use only images you own or have permission to process. "
    "Search results are limited to publicly accessible content. "
    "A similarity score indicates a POTENTIAL match, not a definitive identity."
)

_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Never let startup crash the process (serverless FS is read-only outside /tmp).
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
    except OSError as exc:
        log.warning("[BOOT] upload dir not writable: %s", exc)
    try:
        init_db()
        log.info("[BOOT] database ready url=%s", settings.database_url.split("://")[0])
    except Exception as exc:  # noqa: BLE001
        log.error("[BOOT] db init failed: %s", exc)
    # On serverless, skip heavy cold-start work — face + chain load lazily on
    # first request instead (keeps cold starts fast and within time limits).
    if not _SERVERLESS:
        if get_face_service().warmup():
            log.info("[BOOT] face engine warm")
        else:
            log.warning("[BOOT] face engine will load on first request")
        log.info("[BOOT] blockchain connected=%s", get_blockchain_service().status().get("connected"))
    yield


app = FastAPI(
    title="FaceProof API",
    description=(
        "AI-Powered Face Identification & Blockchain Verification.\n\n"
        "Pipeline: **FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY**.\n\n"
        f"⚠️ {DISCLAIMER}"
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

if limiter is not None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
for r in (
    routes_health.router,
    routes_scan.router,
    routes_search.router,
    routes_blockchain.router,
    routes_verify.router,
    routes_pipeline.router,
):
    app.include_router(r, prefix=API_PREFIX)


@app.get("/")
def root():
    return {
        "name": "FaceProof API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "pipeline": "FACE -> SEARCH -> MATCH -> FINGERPRINT -> BLOCKCHAIN -> VERIFY",
        "disclaimer": DISCLAIMER,
    }


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):  # pragma: no cover
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": {"code": "internal_error", "message": "Internal server error"}})
