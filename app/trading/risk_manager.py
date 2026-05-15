from datetime import datetime
from datetime import timedelta

from app.config import settings
from app.logger import get_logger

logger = get_logger("risk_manager")


class RiskManager:

    def __init__(self):

        self.daily_drawdown = 0.0

        self.open_positions = 0

        self.trade_history = []

        self.emergency_mode = False

        self.last_trade_time = None

    async def validate_trade(
        self,
        symbol: str,
        signal: str,
        strategy,
    ) -> bool:

        logger.info(
            "validating_trade",
            symbol=symbol,
            signal=signal,
        )

        if self.emergency_mode:

            logger.warning(
                "trade_rejected_emergency_mode"
            )

            return False

        if (
            self.daily_drawdown
            >= settings.MAX_DAILY_DRAWDOWN
        ):

            logger.warning(
                "trade_rejected_max_drawdown"
            )

            return False

        if (
            self.open_positions
            >= settings.MAX_OPEN_POSITIONS
        ):

            logger.warning(
                "trade_rejected_max_positions"
            )

            return False

        if not self.validate_cooldown():

            logger.warning(
                "trade_rejected_cooldown"
            )

            return False

        logger.info("trade_approved")

        return True

    def validate_cooldown(self) -> bool:

        if self.last_trade_time is None:
            return True

        cooldown = timedelta(minutes=1)

        return (
            datetime.utcnow()
            - self.last_trade_time
        ) > cooldown

    async def register_trade(self):

        self.open_positions += 1

        self.last_trade_time = (
            datetime.utcnow()
        )

    async def close_trade(self):

        if self.open_positions > 0:
            self.open_positions -= 1

    async def activate_emergency_stop(self):

        logger.critical(
            "emergency_stop_activated"
        )

        self.emergency_mode = True

    async def deactivate_emergency_stop(self):

        logger.warning(
            "emergency_stop_deactivated"
        )

        self.emergency_mode = False
