"""Hash a staff API key with Argon2id for API_KEY_HASHES."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.security.hashing import hash_secret  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Argon2id hash for X-API-Key")
    parser.add_argument("--key", help="Raw API key (omit to prompt securely)")
    args = parser.parse_args()
    raw = args.key or getpass.getpass("API key: ")
    if not raw or len(raw) < 16:
        raise SystemExit("API key should be at least 16 characters")
    print(hash_secret(raw))


if __name__ == "__main__":
    main()
