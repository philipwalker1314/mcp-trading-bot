import asyncio
from collections import defaultdict

from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.models.trades import CloseReason, OrderStatus, Position, TradeSide
from app.trading.lifecycle.pnl_engine import PnLEngine
from app.trading.lifecycle.trade_lifecycle_service import TradeLifecycleService

logger = get_logger("position_monitor")


class PositionMonitor:
    """
    Monitors open positions and enforces
    SL / TP / trailing stop rules.

    Two operational modes:
    1. Event-driven (production):
       Subscribes to market.tick events from EventBus.
       Called instantly on each price update.

    2. Ticker fallback (paper trading / testnet):
       Polls latest price at configurable interval.
       Use PositionMonitorFallback for this.
    """

    def __init__(
        self,
        lifecycle: TradeLifecycleService,
        event_bus: EventBus,
    ):
        self.lifecycle  = lifecycle
        self.event_bus  = event_bus
        self.running    = False

        self._position_cache: dict[str, list[int]] = defaultdict(list)

    async def start(self):
        self.running = True

        self.event_bus.subscribe(
            Events.MARKET_TICK,
            self._on_market_tick,
        )

        self.event_bus.subscribe(
            Events.POSITION_OPENED,
            self._on_position_opened,
        )
        self.event_bus.subscribe(
            Events.POSITION_CLOSED,
            self._on_position_closed,
        )

        await self._rebuild_cache()

        logger.info("position_monitor_started", mode="event_driven")

    async def stop(self):
        self.running = False
        logger.warning("position_monitor_stopped")

    async def _on_market_tick(self, event):
        if not self.running:
            return

        payload = event.payload
        symbol  = payload.get("symbol")
        price   = float(payload.get("price", 0))

        if not symbol or not price:
            return

        position_ids = self._position_cache.get(symbol, [])
        if not position_ids:
            return

        for position_id in list(position_ids):
            await self._process_tick(position_id, symbol, price)

    async def _process_tick(
        self,
        position_id: int,
        symbol: str,
        price: float,
    ):
        position = await self.lifecycle.get_position(position_id)

        if not position or position.status not in (
            OrderStatus.FILLED,
            OrderStatus.PARTIALLY_FILLED,
        ):
            self._remove_from_cache(symbol, position_id)
            return

        await self.lifecycle.update_unrealized_pnl(position_id, price)

        if position.trailing_stop_pct:
            await self.lifecycle.update_trailing_stop(position_id, price)
            position = await self.lifecycle.get_position(position_id)

        if PnLEngine.is_stop_loss_hit(position, price):
            logger.warning(
                "stop_loss_triggered",
                position_id=position_id,
                price=price,
                sl=position.trailing_stop_price or position.stop_loss,
            )
            reason = (
                CloseReason.TRAILING_STOP
                if position.trailing_stop_price
                else CloseReason.STOP_LOSS
            )
            await self.lifecycle.close_position(position_id, price, reason)
            self._remove_from_cache(symbol, position_id)

            await self.event_bus.publish(
                Events.STOP_LOSS_HIT,
                {"position_id": position_id, "price": price, "reason": reason.value},
            )
            return

        if PnLEngine.is_take_profit_hit(position, price):
            logger.info(
                "take_profit_triggered",
                position_id=position_id,
                price=price,
                tp=position.take_profit,
            )
            await self.lifecycle.close_position(
                position_id, price, CloseReason.TAKE_PROFIT
            )
            self._remove_from_cache(symbol, position_id)

            await self.event_bus.publish(
                Events.TAKE_PROFIT_HIT,
                {"position_id": position_id, "price": price},
            )

    async def _rebuild_cache(self):
        self._position_cache.clear()
        positions = await self.lifecycle.get_open_positions()
        for p in positions:
            self._position_cache[p.symbol].append(p.id)

        logger.info(
            "position_cache_rebuilt",
            total_positions=len(positions),
            symbols=list(self._position_cache.keys()),
        )

    async def _on_position_opened(self, event):
        payload = event.payload
        symbol  = payload.get("symbol")
        pos_id  = payload.get("id")
        if symbol and pos_id:
            self._position_cache[symbol].append(int(pos_id))

    async def _on_position_closed(self, event):
        payload = event.payload
        symbol  = payload.get("symbol")
        pos_id  = payload.get("id")
        if symbol and pos_id:
            self._remove_from_cache(symbol, int(pos_id))

    def _remove_from_cache(self, symbol: str, position_id: int):
        if symbol in self._position_cache:
            try:
                self._position_cache[symbol].remove(position_id)
            except ValueError:
                pass


# ─────────────────────────────────────────────
# Fallback: polling for paper trading / testnet
# ─────────────────────────────────────────────

class PositionMonitorFallback:
    """
    Lightweight polling fallback for environments
    without WebSocket market streams (paper trading,
    testnet, development).

    FIX: get_latest_price() on MarketDataEngine is SYNCHRONOUS
    (in-memory dict lookup, no network call).
    Do NOT use await on it.
    """

    def __init__(
        self,
        event_bus: EventBus,
        market_data_service,
        symbols: list[str],
        interval_seconds: float = 2.0,
    ):
        self.event_bus    = event_bus
        self.market       = market_data_service
        self.symbols      = symbols
        self.interval     = interval_seconds
        self.running      = False

    async def start(self):
        self.running = True
        logger.info(
            "position_monitor_fallback_started",
            symbols=self.symbols,
            interval=self.interval,
        )

        while self.running:
            try:
                for symbol in self.symbols:
                    # FIX: get_latest_price is synchronous — no await
                    price = self.market.get_latest_price(symbol)

                    if price is None:
                        # Engine not ready yet — skip this tick
                        continue

                    await self.event_bus.publish(
                        Events.MARKET_TICK,
                        {"symbol": symbol, "price": price},
                        source="ticker_fallback",
                    )

                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("ticker_fallback_error", error=str(e))
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
