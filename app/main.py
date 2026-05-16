"""
main.py — Phase 7 application entry point.

Phase 7 addition:
  - Import + register ai_metrics_router  (/ai-metrics)
  - No other changes from Phase 6
"""

import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.positions import (
    analytics_router,
    positions_router,
)
from app.api.strategies import strategies_router
from app.api.copilot    import copilot_router
from app.api.ai_metrics import ai_metrics_router     # Phase 7
from app.api.ai_toggle  import ai_toggle_router      # Phase 7
from app.config import settings
from app.database import (
    AsyncSessionLocal,
    close_db,
    init_db,
)
from app.logger import get_logger
from app.services.analytics_service import AnalyticsService
from app.services.strategy_config_service import StrategyConfigService
from app.services.copilot_service import CopilotService
from app.tasks.rollup import RollupTask
from app.trading.trading_bot import TradingBot
from app.websocket.manager import (
    router as ws_router,
)

logger = get_logger("main")

trading_bot:  TradingBot   | None = None
bot_task:     asyncio.Task | None = None
rollup_task:  RollupTask   | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global trading_bot, bot_task, rollup_task

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
    # ANALYTICS SERVICE + ROLLUP TASK
    # =====================================================

    analytics = AnalyticsService(session_factory=AsyncSessionLocal)
    app.state.analytics = analytics

    rollup_task = RollupTask(analytics=analytics)
    await rollup_task.start()
    logger.info("analytics_service_initialized")

    # =====================================================
    # STRATEGY CONFIG SERVICE
    # =====================================================

    strategy_config_service = StrategyConfigService(
        session_factory=AsyncSessionLocal
    )
    app.state.strategy_config_service = strategy_config_service
    logger.info("strategy_config_service_initialized")

    # =====================================================
    # COPILOT SERVICE
    # =====================================================

    copilot = CopilotService()
    app.state.copilot = copilot
    logger.info("copilot_service_initialized")

    # =====================================================
    # OPTIONAL TRADING RUNTIME
    # =====================================================

    if settings.ENABLE_TRADING:

        logger.warning("trading_runtime_enabled")

        trading_bot = TradingBot()
        trading_bot.event_bus._redis_pub = None

        app.state.lifecycle   = trading_bot.lifecycle
        app.state.trading_bot = trading_bot

        bot_task = asyncio.create_task(
            trading_bot.start(),
            name="trading_bot",
        )

        logger.info("trading_bot_started")

    else:

        logger.warning("trading_runtime_disabled")

        app.state.lifecycle   = None
        app.state.trading_bot = None

    logger.info("application_started")

    yield

    # =====================================================
    # SHUTDOWN
    # =====================================================

    logger.warning("application_shutting_down")

    if rollup_task:
        try:
            await rollup_task.stop()
        except Exception as e:
            logger.exception("rollup_task_shutdown_error", error=str(e))

    if trading_bot:
        try:
            await trading_bot.stop()
        except Exception as e:
            logger.exception("trading_bot_shutdown_error", error=str(e))

    if bot_task:
        try:
            bot_task.cancel()
        except Exception:
            pass

    try:
        await redis_client.close()
    except Exception as e:
        logger.exception("redis_shutdown_error", error=str(e))

    try:
        await close_db()
    except Exception as e:
        logger.exception("database_shutdown_error", error=str(e))

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
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# ROUTERS
# =====================================================

app.include_router(positions_router)
app.include_router(analytics_router)
app.include_router(strategies_router)
app.include_router(copilot_router)
app.include_router(ai_metrics_router)   # Phase 7
app.include_router(ai_toggle_router)    # Phase 7
app.include_router(ws_router)


# =====================================================
# ROOT
# =====================================================

@app.get("/")
async def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "running",
    }


@app.get("/health")
async def health():
    return {
        "status":              "healthy",
        "trading_enabled":     settings.ENABLE_TRADING,
        "trading_bot_running": (
            trading_bot.running if trading_bot else False
        ),
    }


@app.get("/status")
async def status():
    open_count = 0

    if trading_bot:
        try:
            positions  = await trading_bot.lifecycle.get_open_positions()
            open_count = len(positions)
        except Exception as e:
            logger.exception("status_endpoint_error", error=str(e))

    return {
        "environment":    settings.ENVIRONMENT,
        "paper_trading":  settings.PAPER_TRADING,
        "testnet":        settings.BINANCE_TESTNET,
        "trading_enabled": settings.ENABLE_TRADING,
        "open_positions": open_count,
    }
