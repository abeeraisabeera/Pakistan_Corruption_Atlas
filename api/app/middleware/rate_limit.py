"""In-memory per-IP rate limiting with stricter tiers for search/export."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.security.events import log_security_event

_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def reset_rate_limits_for_tests() -> None:
    _hits.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def _limit_for_path(self, path: str) -> int:
        if path.startswith("/api/v1/export"):
            return settings.rate_limit_export
        if path.startswith("/api/v1/search"):
            return settings.rate_limit_search
        if path in ("/health", "/health/ready", "/"):
            return settings.rate_limit_default * 2
        return settings.rate_limit_default

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        if not settings.rate_limit_enabled:
            return await call_next(request)

        if len(request.url.query) > settings.max_query_string_length:
            return JSONResponse(
                status_code=414,
                content={"detail": "Query string too long"},
            )

        ip = client_ip(request)
        path = request.url.path
        limit = self._limit_for_path(path)
        window = settings.rate_limit_window_seconds
        if path.startswith("/api/v1/export"):
            key = f"{ip}:export"
        elif path.startswith("/api/v1/search"):
            key = f"{ip}:search"
        else:
            key = f"{ip}:default"

        now = time.time()
        bucket = _hits[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = int(max(1, window - (now - bucket[0])))
            log_security_event(
                "rate_limit_exceeded",
                client_ip=ip,
                path=path,
                status=429,
                request_id=getattr(request.state, "request_id", None),
                limit=limit,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(retry)},
            )
        bucket.append(now)
        response = await call_next(request)
        remaining = max(0, limit - len(bucket))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        return response
