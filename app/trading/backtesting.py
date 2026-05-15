import pandas as pd

from app.logger import get_logger

logger = get_logger("backtesting")


class Backtester:

    def __init__(
        self,
        strategy,
    ):

        self.strategy = strategy

        self.results = []

    async def run(
        self,
        dataframe: pd.DataFrame,
    ):

        logger.info(
            "backtest_started",
            strategy=self.strategy.name,
        )

        for i in range(100, len(dataframe)):

            chunk = dataframe.iloc[:i]

            signal = (
                await self.strategy
                .generate_signal(chunk)
            )

            self.results.append(signal)

        logger.info(
            "backtest_completed",
            total_signals=len(self.results),
        )

        return self.results
