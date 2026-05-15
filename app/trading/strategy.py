from abc import ABC
from abc import abstractmethod

import pandas as pd


class BaseStrategy(ABC):

    name = "base_strategy"

    description = ""

    timeframe = "1m"

    enabled = True

    risk_per_trade = 0.01

    stop_loss_percent = 0.02

    take_profit_percent = 0.04

    trailing_stop_percent = 0.01

    @abstractmethod
    async def generate_signal(
        self,
        dataframe: pd.DataFrame,
    ) -> str:
        """
        Must return:
        BUY / SELL / HOLD
        """

        raise NotImplementedError
