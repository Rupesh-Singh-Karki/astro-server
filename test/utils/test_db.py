import pytest
from unittest.mock import patch, AsyncMock
from src.utils.db import _make_async_uri, get_db, init_models, get_sync_engine


def test_make_async_uri_postgresql() -> None:
    uri = "postgresql://user:pass@localhost/db"
    result = _make_async_uri(uri)
    assert result == "postgresql+asyncpg://user:pass@localhost/db"


def test_make_async_uri_already_async() -> None:
    uri = "postgresql+asyncpg://user:pass@localhost/db"
    result = _make_async_uri(uri)
    assert result == uri


def test_make_async_uri_other() -> None:
    uri = "sqlite:///db.sqlite"
    result = _make_async_uri(uri)
    assert result == uri


@pytest.mark.asyncio
async def test_get_db() -> None:
    with patch("src.utils.db.async_session") as mock_async_session:
        mock_session = AsyncMock()
        mock_async_session.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Collect all yielded sessions
        sessions = []
        async for session in get_db():
            sessions.append(session)
            break  # Only take one

        assert len(sessions) == 1
        assert sessions[0] == mock_session

        # Check that the context manager was entered
        mock_session.__aenter__.assert_called_once()


@pytest.mark.asyncio
async def test_init_models() -> None:
    with patch("src.utils.db.async_engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin.return_value = mock_conn
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.run_sync = AsyncMock()

        await init_models(mock_engine)

        mock_conn.run_sync.assert_called_once()


def test_get_sync_engine() -> None:
    with (
        patch("src.utils.db.settings") as mock_settings,
        patch("src.utils.db.create_engine") as mock_create_engine,
    ):

        mock_settings.db_uri = "postgresql+asyncpg://user:pass@localhost/db"
        mock_engine = "mock_engine"
        mock_create_engine.return_value = mock_engine

        engine = get_sync_engine()
        assert engine == mock_engine
        mock_create_engine.assert_called_once()
        args = mock_create_engine.call_args[0]
        assert "postgresql://" in args[0]  # Should convert back
