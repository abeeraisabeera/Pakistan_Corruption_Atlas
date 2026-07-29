"""Optional Cloudflare Turnstile verification for abusive export traffic."""
from __future__ import annotations

import httpx

from app.config import settings


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> bool:
    if not settings.turnstile_secret_key:
        return True
    if not token:
        return False
    payload = {
        "secret": settings.turnstile_secret_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=payload,
        )
        data = resp.json()
        return bool(data.get("success"))
