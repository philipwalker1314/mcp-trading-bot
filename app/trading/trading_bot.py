import asyncio

from app.logger import get_logger
from app.trading.ai_filter import (
    AIFilter,
)
from app.trading.executor import Executor
from app.trading.market_data import (
    MarketDataService,
)
from app.trading.risk_manager import (
    RiskManager,
)
from app.trading.strategy_engine import (
    StrategyEngine,
)
from app.trading.strategy_loader import (
    StrategyLoader,
)

logger = get_logger("trading_bot")


class TradingBot:

    def __init__(self):

        self.market_data_service = (
            MarketDataService()
        )

        self.strategy_loader = (
            StrategyLoader()
        )

        self.ai_filter = AIFilter()

        self.risk_manager = (
            RiskManager()
        )

        self.executor = Executor()

        self.strategy_engine = (
            StrategyEngine(
                strategy_loader=(
                    self.strategy_loader
                ),
                ai_filter=(
                    self.ai_filter
                ),
                risk_manager=(
                    self.risk_manager
                ),
                executor=self.executor,
            )
        )

        self.running = False

        self.symbols = [
            "BTC/USDT",
        ]

    async def start(self):

        logger.info(
            "starting_trading_bot"
        )

        self.running = True

        while self.running:

            try:

                for symbol in self.symbols:

                    dataframe = (
                        await self.market_data_service
                        .get_market_dataframe(
                            symbol=symbol,
                            timeframe="1m",
                            limit=200,
                        )
                    )

                    await (
                        self.strategy_engine
                        .process_market_data(
                            dataframe=dataframe,
                            symbol=symbol,
                        )
                    )

                await asyncio.sleep(10)

            except Exception as error:

                logger.error(
                    "trading_loop_error",
                    error=str(error),
                )

                await asyncio.sleep(5)

    async def stop(self):

        logger.warning(
            "stopping_trading_bot"
        )

        self.running = False
