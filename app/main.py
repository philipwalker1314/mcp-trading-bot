"""
main.py — Phase 2 application entry point.

Startup sequence:
1. Init DB
2. Init Redis
3. Optionally start TradingBot runtime
4. Register API routers + WebSocket endpoints

Shutdown sequence:
1. Stop TradingBot
2. Close DB
3. Close Redis
"""

import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.api.positions import (
    analytics_router,
    positions_router,
)
from app.config import settings
from app.database import (
    close_db,
    init_db,
)
from app.logger import get_logger
from app.trading.trading_bot import TradingBot
from app.websocket.manager import (
    router as ws_router,
)

logger = get_logger("main")

trading_bot: TradingBot | None = None
bot_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global trading_bot, bot_task

    logger.info(
        "application_starting",
        version=settings.APP_VERSION,
    )

    # =====================================================
    # DATABASE
    # =====================================================

    await init_db()

    logger.info("database_initialized")

    # =====================================================
    # REDIS
    # =====================================================

    redis_client = aioredis.from_url(
        settings.redis_connection_url,
        encoding="utf-8",
        decode_responses=True,
    )

    app.state.redis = redis_client

    logger.info("redis_initialized")

    # =====================================================
    # OPTIONAL TRADING RUNTIME
    # =====================================================

    if settings.ENABLE_TRADING:

        logger.warning(
            "trading_runtime_enabled"
        )

        trading_bot = TradingBot()

        # Future Redis Streams integration
        trading_bot.event_bus._redis_pub = None

        # Expose lifecycle service to APIs
        app.state.lifecycle = trading_bot.lifecycle

        bot_task = asyncio.create_task(
            trading_bot.start(),
            name="trading_bot",
        )

        logger.info(
            "trading_bot_started"
        )

    else:

        logger.warning(
            "trading_runtime_disabled"
        )

        app.state.lifecycle = None

    logger.info("application_started")

    yield

    # =====================================================
    # SHUTDOWN
    # =====================================================

    logger.warning(
        "application_shutting_down"
    )

    if trading_bot:

        try:
            await trading_bot.stop()

        except Exception as e:

            logger.exception(
                "trading_bot_shutdown_error",
                error=str(e),
            )

    if bot_task:

        try:
            bot_task.cancel()

        except Exception:
            pass

    try:
        await redis_client.close()

    except Exception as e:

        logger.exception(
            "redis_shutdown_error",
            error=str(e),
        )

    try:
        await close_db()

    except Exception as e:

        logger.exception(
            "database_shutdown_error",
            error=str(e),
        )

    logger.info("application_stopped")


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# =====================================================
# ROUTERS
# =====================================================

app.include_router(positions_router)
app.include_router(analytics_router)
app.include_router(ws_router)

# =====================================================
# ROOT
# =====================================================


@app.get("/")
async def root():

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


# =====================================================
# HEALTH
# =====================================================


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "trading_enabled": settings.ENABLE_TRADING,
        "trading_bot_running": (
            trading_bot.running
            if trading_bot
            else False
        ),
    }


# =====================================================
# STATUS
# =====================================================


@app.get("/status")
async def status():

    open_count = 0

    if trading_bot:

        try:
            positions = (
                await trading_bot.lifecycle.get_open_positions()
            )

            open_count = len(positions)

        except Exception as e:

            logger.exception(
                "status_endpoint_error",
                error=str(e),
            )

    return {
        "environment": settings.ENVIRONMENT,
        "paper_trading": settings.PAPER_TRADING,
        "testnet": settings.BINANCE_TESTNET,
        "trading_enabled": settings.ENABLE_TRADING,
        "open_positions": open_count,
    }
