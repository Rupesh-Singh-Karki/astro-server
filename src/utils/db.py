from typing import AsyncGenerator, Optional, Any
import re

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from src.config import settings
from src.utils.logger import logger

log = logger(__name__)


def _make_async_uri(db_uri: str) -> str:
    """
    Ensure the DB URI uses an async driver suitable for SQLAlchemy async engines.
    If the incoming URI is like 'postgresql://...', convert to 'postgresql+asyncpg://...'.
    If it already contains '+', assume it's correct.
    """
    if "+asyncpg" in db_uri or "+psycopg" in db_uri:
        return db_uri

    if db_uri.startswith("postgresql://"):
        return db_uri.replace("postgresql://", "postgresql+asyncpg://", 1)

    return db_uri


_async_db_uri = _make_async_uri(settings.db_uri)
log.debug("Async DB URI: %s", re.sub(r"://.*?:.*?@", "://<redacted>@", _async_db_uri))

async_engine: AsyncEngine = create_async_engine(
    _async_db_uri,
    echo=False,
    pool_pre_ping=True,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — yields an AsyncSession.
    Example:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_models(engine: Optional[AsyncEngine] = None) -> None:
    """
    Create tables for all SQLModel models.
    Call at app startup if you want SQLAlchemy to create tables automatically.
    """
    eng = engine or async_engine
    async with eng.begin() as conn:
        # Use checkfirst=True to avoid "table already exists" errors
        def create_tables(connection: Any) -> None:
            SQLModel.metadata.create_all(connection, checkfirst=True)

        await conn.run_sync(create_tables)
    log.info("Database tables created (if they did not exist).")


def get_sync_engine(db_uri: Optional[str] = None) -> Engine:
    """
    Return a synchronous SQLAlchemy Engine. Useful for Alembic or scripts that are sync-only.
    Converts a +asyncpg URI back to a sync form if necessary.
    """
    uri = db_uri or settings.db_uri
    if "+asyncpg" in uri:
        sync_uri = uri.replace("+asyncpg", "")
    else:
        sync_uri = uri

    return create_engine(sync_uri, poolclass=NullPool)
