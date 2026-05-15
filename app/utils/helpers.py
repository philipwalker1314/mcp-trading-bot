from decimal import Decimal
from decimal import ROUND_DOWN

import pandas as pd


class TradingHelpers:

    @staticmethod
    def round_step_size(
        value: float,
        step: float,
    ) -> float:
        """
        Round values safely for exchange precision.
        """

        decimal_value = Decimal(str(value))
        decimal_step = Decimal(str(step))

        return float(
            decimal_value.quantize(
                decimal_step,
                rounding=ROUND_DOWN,
            )
        )

    @staticmethod
    def calculate_percentage_change(
        current: float,
        previous: float,
    ) -> float:

        if previous == 0:
            return 0.0

        return ((current - previous) / previous) * 100

    @staticmethod
    def calculate_position_size(
        capital: float,
        risk_percent: float,
        stop_distance: float,
    ) -> float:

        if stop_distance <= 0:
            return 0.0

        risk_amount = capital * risk_percent

        return risk_amount / stop_distance

    @staticmethod
    def dataframe_is_valid(dataframe: pd.DataFrame) -> bool:

        required_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        return all(
            column in dataframe.columns
            for column in required_columns
        )
