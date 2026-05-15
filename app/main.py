import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import close_db
from app.database import init_db
from app.logger import get_logger
from app.trading.trading_bot import (
    TradingBot,
)

logger = get_logger("main")

trading_bot = TradingBot()

bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global bot_task

    logger.info(
        "application_starting",
    )

    await init_db()

    bot_task = asyncio.create_task(
        trading_bot.start()
    )

    logger.info(
        "trading_bot_started",
    )

    yield

    logger.warning(
        "application_shutdown",
    )

    await trading_bot.stop()

    if bot_task:
        bot_task.cancel()

    await close_db()

    logger.info(
        "application_stopped",
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.get("/")
async def root():

    return {
        "app": settings.APP_NAME,
        "status": "running",
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "trading_bot": trading_bot.running,
    }


@app.get("/status")
async def status():

    return {
        "environment": (
            settings.ENVIRONMENT
        ),
        "paper_trading": (
            settings.PAPER_TRADING
        ),
        "binance_testnet": (
            settings.BINANCE_TESTNET
        ),
    }
