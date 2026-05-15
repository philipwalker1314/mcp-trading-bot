from datetime import datetime

import pandas as pd

from app.logger import get_logger
from app.services.binance_service import (
    BinanceService,
)
from app.trading.indicators import Indicators

logger = get_logger("market_data")


class MarketDataService:

    def __init__(self):

        self.binance_service = (
            BinanceService()
        )

    async def get_market_dataframe(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 500,
    ) -> pd.DataFrame:

        logger.info(
            "fetching_market_dataframe",
            symbol=symbol,
            timeframe=timeframe,
        )

        candles = (
            await self.binance_service
            .fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
            )
        )

        dataframe = pd.DataFrame(
            candles,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            unit="ms",
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        dataframe[numeric_columns] = (
            dataframe[numeric_columns]
            .astype(float)
        )

        dataframe = (
            Indicators.apply_all(
                dataframe
            )
        )

        logger.info(
            "market_dataframe_ready",
            rows=len(dataframe),
            latest_close=float(
                dataframe.iloc[-1]["close"]
            ),
        )

        return dataframe

    async def get_latest_price(
        self,
        symbol: str,
    ) -> float:

        ticker = (
            await self.binance_service
            .fetch_ticker(symbol)
        )

        return float(ticker["last"])

    async def get_market_snapshot(
        self,
        symbol: str,
    ) -> dict:

        dataframe = (
            await self.get_market_dataframe(
                symbol=symbol,
                timeframe="1m",
                limit=100,
            )
        )

        latest = dataframe.iloc[-1]

        return {
            "symbol": symbol,
            "timestamp": str(
                datetime.utcnow()
            ),
            "price": float(
                latest["close"]
            ),
            "rsi": float(
                latest.get("rsi", 0)
            ),
            "macd": float(
                latest.get("macd", 0)
            ),
            "atr": float(
                latest.get("atr", 0)
            ),
            "volatility": float(
                latest.get(
                    "volatility",
                    0,
                )
            ),
        }
