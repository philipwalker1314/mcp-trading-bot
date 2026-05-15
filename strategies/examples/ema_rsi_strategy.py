from app.trading.strategy import (
    BaseStrategy,
)


class EMARsiStrategy(BaseStrategy):

    name = "ema_rsi_strategy"

    description = (
        "EMA crossover with RSI filter"
    )

    timeframe = "1m"

    async def generate_signal(
        self,
        dataframe,
    ) -> str:

        latest = dataframe.iloc[-1]

        ema_20 = latest["ema_20"]
        ema_50 = latest["ema_50"]

        rsi = latest["rsi"]

        if (
            ema_20 > ema_50
            and rsi < 70
        ):

            return "BUY"

        if (
            ema_20 < ema_50
            and rsi > 30
        ):

            return "SELL"

        return "HOLD"
