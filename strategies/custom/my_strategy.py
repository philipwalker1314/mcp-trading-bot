"""
my_custom_strategy — EMA crossover + RSI confluence.
Signals only on cross events — HOLD the vast majority of the time.
EMA 8/13 crossover (faster signals than 20/50).
"""

from app.trading.strategy import BaseStrategy


class MyCustomStrategy(BaseStrategy):

    name        = "my_custom_strategy"
    description = "EMA 8/13 crossover + RSI confluence — signals only on cross events"
    timeframe   = "1m"

    stop_loss_percent     = 0.02
    take_profit_percent   = 0.04
    trailing_stop_percent = 0.015

    async def generate_signal(self, dataframe) -> str:
        if len(dataframe) < 20:
            return "HOLD"

        latest = dataframe.iloc[-1]
        prev   = dataframe.iloc[-2]

        close  = latest["close"]
        ema_8  = latest["ema_8"]
        ema_13 = latest["ema_13"]
        rsi    = latest["rsi"]

        if any(v != v for v in [ema_8, ema_13, rsi]):
            return "HOLD"

        ema_crossed_up    = prev["ema_8"] <= prev["ema_13"] and ema_8 > ema_13
        bullish_structure = close > ema_8 > ema_13
        rsi_bullish_zone  = 40 < rsi < 65

        if ema_crossed_up and bullish_structure and rsi_bullish_zone:
            return "BUY"

        ema_crossed_down  = prev["ema_8"] >= prev["ema_13"] and ema_8 < ema_13
        bearish_structure = close < ema_8 < ema_13
        rsi_bearish_zone  = 35 < rsi < 60

        if ema_crossed_down and bearish_structure and rsi_bearish_zone:
            return "SELL"

        return "HOLD"
	
