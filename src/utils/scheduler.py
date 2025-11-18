"""Background scheduler for periodic tasks."""

import asyncio
from typing import Optional, Any
import httpx
from contextlib import asynccontextmanager

from src.config import settings
from src.utils.logger import logger

log = logger(__name__)


class BackgroundScheduler:
    """Scheduler for background tasks like keep-alive pings."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def keep_alive_ping(self) -> None:
        """Ping the backend every 14 minutes to keep it alive."""
        while self._running:
            try:
                # Wait 14 minutes
                await asyncio.sleep(14 * 60)  # 14 minutes in seconds

                # Ping the health endpoint
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{settings.base_url}/health")
                    if response.status_code == 200:
                        log.info("Keep-alive ping successful")
                    else:
                        log.warning(
                            f"Keep-alive ping returned status {response.status_code}"
                        )
            except asyncio.CancelledError:
                log.info("Keep-alive ping task cancelled")
                break
            except Exception as e:
                log.error(f"Keep-alive ping failed: {e}")
                # Continue running even if one ping fails

    async def start(self) -> None:
        """Start the background scheduler."""
        if self._running:
            log.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self.keep_alive_ping())
        log.info("Background scheduler started")

    async def stop(self) -> None:
        """Stop the background scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("Background scheduler stopped")


# Singleton instance
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan_scheduler(app: Any) -> Any:
    """Lifespan context manager for FastAPI to start/stop scheduler."""
    # Startup
    await scheduler.start()
    yield
    # Shutdown
    await scheduler.stop()
