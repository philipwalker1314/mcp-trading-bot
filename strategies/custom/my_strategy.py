from app.trading.strategy import (
    BaseStrategy,
)


class MyCustomStrategy(BaseStrategy):

    name = "my_custom_strategy"

    description = (
        "Custom strategy example"
    )

    timeframe = "1m"

    async def generate_signal(
        self,
        dataframe,
    ) -> str:

        latest = dataframe.iloc[-1]

        close_price = latest["close"]

        open_price = latest["open"]

        if close_price > open_price:
            return "BUY"

        if close_price < open_price:
            return "SELL"

        return "HOLD"
