"""FastAPI dependencies for optional staff API key auth."""
from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from app.middleware.rate_limit import client_ip
from app.security.api_keys import is_locked, verify_api_key
from app.security.events import log_security_event


async def optional_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not x_api_key:
        return None
    if is_locked(x_api_key):
        log_security_event(
            "api_key_locked",
            client_ip=client_ip(request),
            path=request.url.path,
            status=429,
            request_id=getattr(request.state, "request_id", None),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API key temporarily locked due to failed attempts",
        )
    principal = verify_api_key(x_api_key)
    if principal is None:
        log_security_event(
            "api_key_invalid",
            client_ip=client_ip(request),
            path=request.url.path,
            status=401,
            request_id=getattr(request.state, "request_id", None),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return principal


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    return await optional_api_key(request, x_api_key)


def require_permission(permission: str):
    async def _dep(principal=None):  # filled by FastAPI via require_api_key composition
        # Callers should Depends(require_api_key) then check permission in-route,
        # or use this factory with an explicit principal dependency.
        raise NotImplementedError

    async def dependency(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ):
        principal = await require_api_key(request, x_api_key)
        if permission not in principal.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return principal

    return dependency
