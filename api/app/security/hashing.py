"""Argon2id helpers for staff API keys (not end-user passwords)."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def _pepper(raw: str) -> str:
    if settings.api_key_pepper:
        return f"{settings.api_key_pepper}:{raw}"
    return raw


def hash_secret(raw: str) -> str:
    return _hasher.hash(_pepper(raw))


def verify_secret(raw: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, _pepper(raw))
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
