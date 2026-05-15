from app.logger import get_logger
from app.services.binance_service import (
    BinanceService,
)

logger = get_logger("executor")


class Executor:

    def __init__(self):

        self.binance_service = (
            BinanceService()
        )

    async def execute_trade(
        self,
        symbol: str,
        signal: str,
        strategy,
    ):

        side = (
            "buy"
            if signal == "BUY"
            else "sell"
        )

        quantity = 0.001

        logger.warning(
            "executing_trade",
            symbol=symbol,
            side=side,
            quantity=quantity,
        )

        order = (
            await self.binance_service
            .create_market_order(
                symbol=symbol,
                side=side,
                amount=quantity,
            )
        )

        logger.info(
            "trade_executed",
            order=order,
        )

        return order
