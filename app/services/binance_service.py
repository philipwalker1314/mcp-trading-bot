import ccxt.async_support as ccxt

from app.config import settings
from app.logger import get_logger
from app.utils.retries import async_retry

logger = get_logger("binance_service")


class BinanceService:

    def __init__(self):

        self.exchange = ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_SECRET_KEY,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
            },
        })

        if settings.BINANCE_TESTNET:
            self.exchange.set_sandbox_mode(True)

    @async_retry()
    async def fetch_balance(self):

        logger.info("fetching_balance")

        return await self.exchange.fetch_balance()

    @async_retry()
    async def fetch_ticker(self, symbol: str):

        logger.info(
            "fetching_ticker",
            symbol=symbol,
        )

        return await self.exchange.fetch_ticker(symbol)

    @async_retry()
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 500,
    ):

        logger.info(
            "fetching_ohlcv",
            symbol=symbol,
            timeframe=timeframe,
        )

        return await self.exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    @async_retry()
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
    ):

        logger.warning(
            "market_order_requested",
            symbol=symbol,
            side=side,
            amount=amount,
            paper_trading=settings.PAPER_TRADING,
        )

        if settings.PAPER_TRADING:

            logger.info(
                "paper_trade_executed",
                symbol=symbol,
                side=side,
                amount=amount,
            )

            return {
                "paper_trade": True,
                "symbol": symbol,
                "side": side,
                "amount": amount,
            }

        return await self.exchange.create_market_order(
            symbol=symbol,
            side=side,
            amount=amount,
        )

    async def close(self):

        logger.info("closing_exchange_connection")

        await self.exchange.close()
