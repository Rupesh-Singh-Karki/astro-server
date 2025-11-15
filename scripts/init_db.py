#!/usr/bin/env python3
"""
Script to initialize the database and create tables.
Run this before starting the application for the first time.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.db import init_models
from src.utils.logger import logger

log = logger(__name__)


async def main() -> None:
    """Initialize database tables."""
    try:
        log.info("Initializing database tables...")
        await init_models()
        log.info("✅ Database tables created successfully!")
        log.info("You can now start the application.")
    except Exception as e:
        log.error(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
