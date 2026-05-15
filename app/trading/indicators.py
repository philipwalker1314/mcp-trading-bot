import pandas as pd
import ta


class Indicators:

    @staticmethod
    def add_ema(
        dataframe: pd.DataFrame,
        period: int,
        column_name: str,
    ) -> pd.DataFrame:

        dataframe[column_name] = (
            ta.trend.ema_indicator(
                dataframe["close"],
                window=period,
            )
        )

        return dataframe

    @staticmethod
    def add_rsi(
        dataframe: pd.DataFrame,
        period: int = 14,
    ) -> pd.DataFrame:

        dataframe["rsi"] = (
            ta.momentum.rsi(
                dataframe["close"],
                window=period,
            )
        )

        return dataframe

    @staticmethod
    def add_macd(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        dataframe["macd"] = (
            ta.trend.macd(
                dataframe["close"],
            )
        )

        dataframe["macd_signal"] = (
            ta.trend.macd_signal(
                dataframe["close"],
            )
        )

        return dataframe

    @staticmethod
    def add_atr(
        dataframe: pd.DataFrame,
        period: int = 14,
    ) -> pd.DataFrame:

        dataframe["atr"] = (
            ta.volatility.average_true_range(
                dataframe["high"],
                dataframe["low"],
                dataframe["close"],
                window=period,
            )
        )

        return dataframe

    @staticmethod
    def add_volatility(
        dataframe: pd.DataFrame,
        period: int = 20,
    ) -> pd.DataFrame:

        dataframe["volatility"] = (
            dataframe["close"]
            .pct_change()
            .rolling(period)
            .std()
        )

        return dataframe

    @staticmethod
    def apply_all(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        dataframe = (
            Indicators.add_ema(
                dataframe,
                20,
                "ema_20",
            )
        )

        dataframe = (
            Indicators.add_ema(
                dataframe,
                50,
                "ema_50",
            )
        )

        dataframe = (
            Indicators.add_rsi(
                dataframe
            )
        )

        dataframe = (
            Indicators.add_macd(
                dataframe
            )
        )

        dataframe = (
            Indicators.add_atr(
                dataframe
            )
        )

        dataframe = (
            Indicators.add_volatility(
                dataframe
            )
        )

        return dataframe
