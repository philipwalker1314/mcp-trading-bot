
import asyncio
import json
from collections import deque
from datetime import datetime

import websockets
import pandas as pd

from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.services.binance_service import BinanceService
from app.trading.indicators import Indicators

logger = get_logger("market_data_engine")


# ─────────────────────────────────────────────
# Tick data structure
# ─────────────────────────────────────────────

class Tick:
    __slots__ = ("symbol", "price", "volume", "timestamp")

    def __init__(
        self,
        symbol:    str,
        price:     float,
        volume:    float,
        timestamp: datetime,
    ):
        self.symbol    = symbol
        self.price     = price
        self.volume    = volume
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "symbol":    self.symbol,
            "price":     self.price,
            "volume":    self.volume,
            "timestamp": self.timestamp.isoformat(),
        }


# ─────────────────────────────────────────────
# MarketDataEngine
# ─────────────────────────────────────────────

class MarketDataEngine:
    """
    Single engine managing all market data.

    One WebSocket stream per symbol.
    Candles are cached in memory (deque, 500 max).
    Latest price is always available in-memory.
    """

    WS_BASE = "wss://stream.binance.com:9443/ws"
    CANDLE_CACHE_SIZE = 500

    def __init__(
        self,
        event_bus: EventBus,
        binance_service: BinanceService,
        symbols: list[str],
        timeframe: str = "1m",
    ):
        self.event_bus  = event_bus
        self.binance    = binance_service
        self.symbols    = symbols
        self.timeframe  = timeframe
        self.running    = False

        # In-memory state
        self._latest_prices: dict[str, float]       = {}
        self._candle_cache:  dict[str, deque]        = {}
        self._ws_tasks:      dict[str, asyncio.Task] = {}

        for symbol in symbols:
            self._candle_cache[symbol] = deque(maxlen=self.CANDLE_CACHE_SIZE)

    # ─────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────

    async def start(self):
        """
        1. Pre-load historical candles for all symbols
        2. Start WebSocket streams
        """
        self.running = True
        logger.info("market_data_engine_starting", symbols=self.symbols)

        # Pre-load candle history
        await asyncio.gather(*[
            self._preload_candles(symbol)
            for symbol in self.symbols
        ])

        # Start WS streams
        for symbol in self.symbols:
            task = asyncio.create_task(
                self._stream_symbol(symbol),
                name=f"ws_{symbol}",
            )
            self._ws_tasks[symbol] = task

        logger.info(
            "market_data_engine_started",
            symbols=self.symbols,
        )

    async def stop(self):
        self.running = False
        for task in self._ws_tasks.values():
            task.cancel()
        logger.warning("market_data_engine_stopped")

    # ─────────────────────────────────────────
    # WebSocket stream per symbol
    # ─────────────────────────────────────────

    async def _stream_symbol(self, symbol: str):
        """
        Maintains a persistent WebSocket connection
        with exponential backoff on failure.
        """
        backoff = 1.0
        ws_symbol = symbol.replace("/", "").lower()
        url = f"{self.WS_BASE}/{ws_symbol}@kline_{self.timeframe}"

        while self.running:
            try:
                logger.info(
                    "ws_connecting",
                    symbol=symbol,
                    url=url,
                )
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    backoff = 1.0  # reset on successful connect
                    logger.info("ws_connected", symbol=symbol)

                    async for raw in ws:
                        if not self.running:
                            return
                        await self._handle_kline_message(symbol, raw)

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(
                    "ws_stream_error",
                    symbol=symbol,
                    error=str(e),
                    reconnect_in=backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)  # cap at 60s

    async def _handle_kline_message(
        self,
        symbol: str,
        raw:    str,
    ):
        """
        Process a Binance kline WebSocket message.
        Publishes MARKET_TICK on every update.
        Publishes CANDLE_CLOSED when candle completes.
        """
        try:
            payload = json.loads(raw)
            kline   = payload.get("k", {})

            price  = float(kline.get("c", 0))
            volume = float(kline.get("v", 0))
            closed = kline.get("x", False)  # is candle closed?

            # Update latest price cache
            self._latest_prices[symbol] = price

            # Emit tick for PositionMonitor and other subscribers
            await self.event_bus.publish(
                Events.MARKET_TICK,
                {
                    "symbol": symbol,
                    "price":  price,
                    "volume": volume,
                },
                source="market_data_engine",
            )

            # On candle close, update cache + emit
            if closed:
                candle = {
                    "timestamp": datetime.fromtimestamp(kline["t"] / 1000),
                    "open":      float(kline["o"]),
                    "high":      float(kline["h"]),
                    "low":       float(kline["l"]),
                    "close":     price,
                    "volume":    volume,
                }
                self._candle_cache[symbol].append(candle)

                await self.event_bus.publish(
                    Events.CANDLE_CLOSED,
                    {"symbol": symbol, "candle": candle},
                    source="market_data_engine",
                )

        except Exception as e:
            logger.error(
                "kline_message_error",
                symbol=symbol,
                error=str(e),
            )

    # ─────────────────────────────────────────
    # REST pre-load
    # ─────────────────────────────────────────

    async def _preload_candles(self, symbol: str):
        """
        Fetch recent OHLCV history on startup
        to seed the in-memory candle cache.
        """
        try:
            candles = await self.binance.fetch_ohlcv(
                symbol=symbol,
                timeframe=self.timeframe,
                limit=self.CANDLE_CACHE_SIZE,
            )
            for c in candles:
                self._candle_cache[symbol].append({
                    "timestamp": datetime.fromtimestamp(c[0] / 1000),
                    "open":      float(c[1]),
                    "high":      float(c[2]),
                    "low":       float(c[3]),
                    "close":     float(c[4]),
                    "volume":    float(c[5]),
                })

            if candles:
                self._latest_prices[symbol] = float(candles[-1][4])

            logger.info(
                "candles_preloaded",
                symbol=symbol,
                count=len(candles),
            )
        except Exception as e:
            logger.error(
                "candle_preload_error",
                symbol=symbol,
                error=str(e),
            )

    # ─────────────────────────────────────────
    # Public API (called by strategy engine etc.)
    # ─────────────────────────────────────────

    def get_latest_price(self, symbol: str) -> float | None:
        """
        Synchronous in-memory lookup.
        No network call. Zero latency.
        """
        return self._latest_prices.get(symbol)

    def get_candles_df(self, symbol: str) -> pd.DataFrame | None:
        """
        Return cached candles as a DataFrame
        with all indicators applied.
        """
        cache = self._candle_cache.get(symbol)
        if not cache or len(cache) < 60:
            return None

        df = pd.DataFrame(list(cache))
        df = Indicators.apply_all(df)
        return df

    def is_ready(self, symbol: str) -> bool:
        """
        True if we have enough data to run
        strategies on this symbol.
        """
        return (
            symbol in self._latest_prices
            and len(self._candle_cache.get(symbol, [])) >= 60
        )
