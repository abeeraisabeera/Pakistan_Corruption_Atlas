"""Security event helpers (structured logs; optional DB sink later)."""
from __future__ import annotations

from typing import Any

from app.security.logging import get_logger

logger = get_logger("ppca.security")


def mask_ip(ip: str | None) -> str:
    if not ip:
        return "unknown"
    if "." in ip and ":" not in ip:
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
    if ":" in ip:
        return ip.split(":")[0] + ":xxxx"
    return "unknown"


def log_security_event(
    event: str,
    *,
    client_ip: str | None = None,
    path: str | None = None,
    status: int | None = None,
    request_id: str | None = None,
    **extra: Any,
) -> None:
    logger.warning(
        event,
        extra={
            "event": event,
            "client_ip": mask_ip(client_ip),
            "path": path,
            "status": status,
            "request_id": request_id,
            "extra": extra or None,
        },
    )
