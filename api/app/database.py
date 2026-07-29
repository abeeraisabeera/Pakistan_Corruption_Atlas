from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    if settings.use_sqlite:
        return settings.sqlite_url
    return settings.database_url


engine = create_async_engine(_database_url(), echo=False)
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
