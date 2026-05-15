import asyncio
import json

import websockets

from app.logger import get_logger

logger = get_logger("websocket_service")


class BinanceWebSocketService:

    BASE_URL = (
        "wss://stream.binance.com:9443/ws"
    )

    def __init__(
        self,
        symbol: str = "btcusdt",
        timeframe: str = "1m",
    ):

        self.symbol = symbol.lower()
        self.timeframe = timeframe

        self.ws_url = (
            f"{self.BASE_URL}/"
            f"{self.symbol}@kline_{self.timeframe}"
        )

        self.running = False

    async def connect(self):

        self.running = True

        while self.running:

            try:
                logger.info(
                    "connecting_websocket",
                    url=self.ws_url,
                )

                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as websocket:

                    logger.info(
                        "websocket_connected",
                        symbol=self.symbol,
                    )

                    async for message in websocket:

                        payload = json.loads(message)

                        await self.process_message(payload)

            except Exception as error:

                logger.error(
                    "websocket_connection_error",
                    error=str(error),
                )

                await asyncio.sleep(5)

    async def process_message(self, payload: dict):

        candle = payload.get("k", {})

        logger.info(
            "market_update",
            symbol=self.symbol,
            close=candle.get("c"),
        )

    async def stop(self):

        logger.warning("stopping_websocket")

        self.running = False
