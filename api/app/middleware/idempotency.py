"""Idempotency-Key support for future non-GET mutations."""
from __future__ import annotations

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

_store: dict[str, tuple[float, int, Any, dict[str, str]]] = {}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)
        if len(key) > 128:
            return JSONResponse(status_code=400, content={"detail": "Idempotency-Key too long"})

        now = time.time()
        # Evict expired
        expired = [k for k, (exp, *_rest) in _store.items() if exp < now]
        for k in expired:
            _store.pop(k, None)

        cached = _store.get(key)
        if cached:
            _exp, status, body, headers = cached
            return JSONResponse(status_code=status, content=body, headers=headers)

        response = await call_next(request)
        # Only cache JSON success-ish responses
        if 200 <= response.status_code < 300 and "application/json" in response.headers.get(
            "content-type", ""
        ):
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            import json

            try:
                body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
            _store[key] = (
                now + settings.idempotency_ttl_seconds,
                response.status_code,
                body,
                headers,
            )
            return JSONResponse(status_code=response.status_code, content=body, headers=headers)
        return response
