"""
Async SQLAlchemy engine and session factory.
Supports PostgreSQL (asyncpg) and SQLite (aiosqlite).
"""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_engine() -> AsyncEngine:
    db_url = settings.DATABASE_URL
    connect_args: dict = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_async_engine(
            db_url,
            connect_args=connect_args,
            echo=(settings.APP_ENV == "development"),
        )
    else:
        engine = create_async_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=(settings.APP_ENV == "development"),
        )

    logger.info("Async DB engine created: %s", db_url.split("@")[-1])
    return engine


engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """Create all tables. Called on app startup."""
    import app.models.db_models  # noqa: F401 — populate metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All database tables created/verified.")
