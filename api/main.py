"""
Vercel / local ASGI entrypoint.

Vercel Root Directory = `api` detects FastAPI `app` here or in `app/main.py`.
"""
from app.main import app

__all__ = ["app"]
