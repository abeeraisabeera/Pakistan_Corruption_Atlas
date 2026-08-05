from collections.abc import AsyncGenerator
import os
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# libpq/Neon query params that asyncpg does not accept
_ASYNCPG_STRIP_PARAMS = {
    "sslmode",
    "channel_binding",
    "sslrootcert",
    "sslcert",
    "sslkey",
}


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    if settings.use_sqlite:
        return settings.sqlite_url
    return settings.database_url


def _engine_kwargs(url: str) -> dict:
    """Normalize Neon/Postgres URLs for asyncpg (no sslmode query args)."""
    if url.startswith("sqlite"):
        return {"url": url, "echo": False}

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    want_ssl = False
    if "sslmode" in query:
        mode = (query.get("sslmode") or ["prefer"])[0].lower()
        want_ssl = mode in {"require", "verify-ca", "verify-full"}
        for key in list(_ASYNCPG_STRIP_PARAMS):
            query.pop(key, None)
    elif "neon.tech" in (parsed.hostname or ""):
        want_ssl = True

    clean = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
    kwargs: dict = {"url": clean, "echo": False}
    if want_ssl:
        kwargs["connect_args"] = {"ssl": True}
    # Serverless (Vercel) must not hold pooled connections across invocations
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        kwargs["poolclass"] = NullPool
    return kwargs


engine = create_async_engine(**_engine_kwargs(_database_url()))
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from app import models  # noqa: F401
    from app.services.seed import seed_if_empty

    async with engine.begin() as conn:
        # SQLite demos: recreate schema when doing a full seed replace so new columns apply
        if settings.use_sqlite and settings.replace_seed_on_startup:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    if settings.seed_on_startup:
        async with SessionLocal() as session:
            await seed_if_empty(session)
