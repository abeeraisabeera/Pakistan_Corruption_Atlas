"""Staff API key verification with in-memory failure lockout."""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.config import settings
from app.security.hashing import verify_secret


@dataclass
class ApiKeyPrincipal:
    key_id: str
    permissions: frozenset[str]


# Failure tracking: fingerprint -> (failures, lock_until)
_failures: dict[str, tuple[int, float]] = {}


def _fingerprint(raw_key: str) -> str:
    # Do not store raw keys; short stable id for lockout buckets.
    import hashlib

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]


def is_locked(raw_key: str) -> bool:
    fp = _fingerprint(raw_key)
    entry = _failures.get(fp)
    if not entry:
        return False
    failures, lock_until = entry
    if lock_until and time.time() < lock_until:
        return True
    if lock_until and time.time() >= lock_until:
        _failures.pop(fp, None)
    return False


def register_failure(raw_key: str) -> None:
    fp = _fingerprint(raw_key)
    failures, _ = _failures.get(fp, (0, 0.0))
    failures += 1
    lock_until = 0.0
    if failures >= settings.api_key_max_failures:
        lock_until = time.time() + settings.api_key_lockout_seconds
    _failures[fp] = (failures, lock_until)


def register_success(raw_key: str) -> None:
    _failures.pop(_fingerprint(raw_key), None)


def verify_api_key(raw_key: str | None) -> ApiKeyPrincipal | None:
    if not raw_key or not settings.api_key_hashes:
        return None
    if is_locked(raw_key):
        return None
    for idx, hashed in enumerate(settings.api_key_hashes):
        if verify_secret(raw_key, hashed):
            register_success(raw_key)
            return ApiKeyPrincipal(
                key_id=f"key-{idx}",
                permissions=frozenset({"admin", "export", "write"}),
            )
    register_failure(raw_key)
    return None


def reset_lockouts_for_tests() -> None:
    _failures.clear()
