from datetime import datetime, timedelta

from app.config import settings
from app.logger import get_logger

logger = get_logger("risk_manager")


class RiskManager:

    def __init__(self):
        self.daily_drawdown  = 0.0
        self.open_positions  = 0
        self.trade_history   = []
        self.emergency_mode  = False
        self.last_trade_time = None

        # FIX 1: track open symbols → prevents duplicate positions per symbol
        self._open_symbols: set[str] = set()

    async def validate_trade(
        self,
        symbol: str,
        signal: str,
        strategy,
    ) -> bool:

        logger.info("validating_trade", symbol=symbol, signal=signal)

        if self.emergency_mode:
            logger.warning("trade_rejected_emergency_mode")
            return False

        if self.daily_drawdown >= settings.MAX_DAILY_DRAWDOWN:
            logger.warning("trade_rejected_max_drawdown")
            return False

        if self.open_positions >= settings.MAX_OPEN_POSITIONS:
            logger.warning("trade_rejected_max_positions")
            return False

        # FIX 1: one position per symbol max
        if symbol in self._open_symbols:
            logger.warning(
                "trade_rejected_symbol_already_open",
                symbol=symbol,
            )
            return False

        if not self.validate_cooldown():
            logger.warning("trade_rejected_cooldown")
            return False

        logger.info("trade_approved", symbol=symbol)
        return True

    def validate_cooldown(self) -> bool:
        if self.last_trade_time is None:
            return True
        return (datetime.utcnow() - self.last_trade_time) > timedelta(minutes=1)

    async def register_trade(self, symbol: str):
        self.open_positions += 1
        self.last_trade_time = datetime.utcnow()
        self._open_symbols.add(symbol)
        logger.info(
            "trade_registered",
            symbol=symbol,
            open_positions=self.open_positions,
            open_symbols=list(self._open_symbols),
        )

    async def close_trade(self, symbol: str | None = None):
        if self.open_positions > 0:
            self.open_positions -= 1
        if symbol:
            self._open_symbols.discard(symbol)
        logger.info(
            "trade_closed",
            symbol=symbol,
            open_positions=self.open_positions,
            open_symbols=list(self._open_symbols),
        )

    async def activate_emergency_stop(self):
        logger.critical("emergency_stop_activated")
        self.emergency_mode = True

    async def deactivate_emergency_stop(self):
        logger.warning("emergency_stop_deactivated")
        self.emergency_mode = False

    def is_symbol_open(self, symbol: str) -> bool:
        return symbol in self._open_symbols
