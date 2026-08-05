"""
Pakistan Public Corruption Atlas — FastAPI application entrypoint.
Aggregates publicly available OSINT for research and education only.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.database import init_db
from app.middleware import (
    IdempotencyMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from app.routers import analytics, export, health, network, scandals, search, stats
from app.security.events import log_security_event
from app.security.logging import configure_logging

configure_logging()

if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[FastApiIntegration()], traces_sample_rate=0.0)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Do not crash the whole serverless function if DB init fails (bad URL, cold Neon, etc.)
    try:
        await init_db()
    except Exception as exc:  # noqa: BLE001 — surface via /health/ready instead
        log_security_event(
            "startup_init_failed",
            status=500,
            error_type=type(exc).__name__,
            detail=str(exc)[:300],
        )
    yield


app = FastAPI(
    title="Pakistan Public Corruption Atlas API",
    description=(
        "OSINT research API (1960–2026). Inclusion does not imply guilt. "
        "Consult cited primary sources and court records for authoritative information."
    ),
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# Middleware order: last added runs first on request.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-API-Key", "X-Request-ID", "Idempotency-Key", "CF-Turnstile-Response"],
)
if settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.include_router(health.router, tags=["Health"])
app.include_router(scandals.router, prefix="/api/v1/scandals", tags=["Scandals"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Stats"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(network.router, prefix="/api/v1/network", tags=["Network"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"X-Request-ID": getattr(request.state, "request_id", "")},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers={"X-Request-ID": getattr(request.state, "request_id", "")},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log_security_event(
        "unhandled_exception",
        client_ip=request.client.host if request.client else None,
        path=request.url.path,
        status=500,
        request_id=getattr(request.state, "request_id", None),
        error_type=type(exc).__name__,
    )
    detail = "Internal server error"
    if not settings.is_production:
        detail = f"Internal server error: {type(exc).__name__}"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers={"X-Request-ID": getattr(request.state, "request_id", "")},
    )


@app.get("/")
async def root():
    payload = {
        "name": "Pakistan Public Corruption Atlas",
        "period": "1960–2026",
        "api_version": settings.api_version,
        "disclaimer": (
            "This project aggregates publicly available information from reputable "
            "and official sources for research, transparency, and educational purposes. "
            "Inclusion in the database does not imply guilt. Users should consult the "
            "cited primary sources and court records for authoritative information."
        ),
    }
    if settings.docs_enabled:
        payload["docs"] = "/docs"
    return payload
