import time
from typing import Any, Callable, TypeVar, Dict, AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.db import init_models, async_session, async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.logger import logger

# Import all models to ensure relationships are properly registered
from src.auth.model import User, UserDetails, OTPCode  # noqa: F401
from src.chat.model import ChatSession, ChatMessage  # noqa: F401

# Import auth router
from src.auth.routes.auth_routes import router as auth_router

description = """
astro-server API's
"""

log = logger()


async def create_default_admin_if_missing(session: AsyncSession) -> None:
    """No-op helper to create a default admin if it does not exist.

    This is intentionally lightweight — it logs the operation. Replace with your
    production logic (creating a seeded admin user) in a real application.
    """
    log.debug("checked for default admin (no-op)")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context.

    - initializes the DB models at startup
    - tries to create a default admin if missing (no-op in minimal setup)
    - disposes the async engine at shutdown
    """
    log.info("Starting astro-server API...")
    await init_models()
    # create_default_admin_if_missing is optional; implement as a no-op if not available
    try:
        async with async_session() as session:
            await create_default_admin_if_missing(session)
    except NameError:
        log.debug("create_default_admin_if_missing not available, skipping")
    except Exception:
        log.exception("Failed to create default admin, continuing startup")

    log.info("Startup complete.")

    yield

    log.info("Shutting down astro-server API...")
    # Properly dispose the underlying engine when shutting down
    try:
        await async_engine.dispose()
    except Exception:
        log.exception("Error on engine dispose")
    log.info("Shutdown complete.")


app = FastAPI(
    title="astro-server",
    description=description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.root_path,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)


@app.get("/", tags=["Health"])
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "message": "astro-server API is running"}


F = TypeVar("F", bound=Callable[..., Any])


@app.middleware("http")
async def process_time_log_middleware(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = str(round(time.time() - start_time, 3))
    response.headers["X-Process-Time"] = process_time
    log.info(
        "Method=%s Path=%s StatusCode=%s ProcessTime=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


# Include auth router
app.include_router(auth_router)

if __name__ == "__main__":
    # When running locally, pass the app object directly to uvicorn.run
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )
