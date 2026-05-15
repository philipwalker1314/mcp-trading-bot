from app.trading.strategy import (
    BaseStrategy,
)


class MyCustomStrategy(BaseStrategy):

    name = "my_custom_strategy"

    description = (
        "Force test strategy"
    )

    timeframe = "1m"

    async def generate_signal(
        self,
        dataframe,
    ) -> str:

        latest = dataframe.iloc[-1]

        close_price = latest["close"]

        ema_20 = latest["ema_20"]

        if close_price > ema_20:
            return "BUY"

        return "SELL"
