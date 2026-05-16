"""
my_custom_strategy — TEST MODE (always returns BUY to verify pipeline)
"""

from app.trading.strategy import BaseStrategy


class MyCustomStrategy(BaseStrategy):

    name        = "my_custom_strategy"
    description = "EMA crossover + RSI confluence — signals only on cross events"
    timeframe   = "1m"

    stop_loss_percent     = 0.02
    take_profit_percent   = 0.04
    trailing_stop_percent = 0.015

    async def generate_signal(self, dataframe) -> str:
        return "BUY"
