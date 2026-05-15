"""
TradingBot — updated for Phase 2.

Key changes from Phase 1:
1. MarketDataEngine owns market data (not polling in bot)
2. StrategyEngine subscribes to CANDLE_CLOSED events
3. LifecycleService handles open/close (not executor directly)
4. PositionMonitor subscribes to MARKET_TICK events
5. Reconciliation runs on startup and periodically
6. Bot loop is now event-driven, not sleep-poll

The bot's job is orchestration:
  start engines → wire events → stay out of the way
"""

import asyncio

from app.config import settings
from app.database import AsyncSessionLocal
from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.services.binance_service import BinanceService
from app.trading.ai_filter import AIFilter
from app.trading.broker.reconciliation import BrokerReconciliationService
from app.trading.engines.market_data_engine import MarketDataEngine
from app.trading.lifecycle.position_monitor import (
    PositionMonitor,
    PositionMonitorFallback,
)
from app.trading.lifecycle.trade_lifecycle_service import TradeLifecycleService
from app.trading.risk_manager import RiskManager
from app.trading.strategy_loader import StrategyLoader
from app.websocket.manager import register_ws_handlers

logger = get_logger("trading_bot")

SYMBOLS = ["BTC/USDT"]


class TradingBot:

    def __init__(self):

        # ── Core infrastructure ──────────────
        self.event_bus = EventBus()
        self.binance = BinanceService()

        # ── Lifecycle (central hub) ──────────
        self.lifecycle = TradeLifecycleService(
            session_factory=AsyncSessionLocal,
            event_bus=self.event_bus,
        )

        # ── Market data ──────────────────────
        self.market_engine = MarketDataEngine(
            event_bus=self.event_bus,
            binance_service=self.binance,
            symbols=SYMBOLS,
            timeframe="1m",
        )

        # ── Position monitoring ───────────────
        self.position_monitor = PositionMonitor(
            lifecycle=self.lifecycle,
            event_bus=self.event_bus,
        )

        # Paper trading fallback (emits synthetic ticks)
        self.ticker_fallback = PositionMonitorFallback(
            event_bus=self.event_bus,
            market_data_service=self.market_engine,
            symbols=SYMBOLS,
            interval_seconds=10.0,
        )

        # ── Strategy ─────────────────────────
        self.strategy_loader = StrategyLoader()
        self.ai_filter = AIFilter()
        self.risk_manager = RiskManager()

        # ── Broker reconciliation ────────────
        self.reconciliation = BrokerReconciliationService(
            lifecycle=self.lifecycle,
            binance=self.binance,
        )

        self.running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        logger.info("trading_bot_starting")
        self.running = True

        # 1. Register WebSocket → EventBus bridge
        register_ws_handlers(self.event_bus)

        # 2. Register strategy engine on candle close
        self.event_bus.subscribe(
            Events.CANDLE_CLOSED,
            self._on_candle_closed,
        )

        # 3. Run startup reconciliation with timeout
        # so a bad API key doesn't block the bot from starting
        try:
            await asyncio.wait_for(self.reconciliation.run(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("reconciliation_startup_timeout_skipped")
        except Exception as e:
            logger.warning("reconciliation_startup_skipped", error=str(e))

        # 4. Start market data engine (WebSocket streams)
        self._tasks.append(
            asyncio.create_task(
                self.market_engine.start(),
                name="market_data_engine",
            )
        )

        # 5. Start position monitor
        await self.position_monitor.start()

        # 6. In paper trading mode, start fallback ticker
        if settings.PAPER_TRADING:
            self._tasks.append(
                asyncio.create_task(
                    self.ticker_fallback.start(),
                    name="ticker_fallback",
                )
            )

        # 7. Periodic reconciliation (every 60s)
        self._tasks.append(
            asyncio.create_task(
                self._reconciliation_loop(),
                name="reconciliation_loop",
            )
        )

        logger.info("trading_bot_started")

        # Keep bot alive — all work is event-driven
        while self.running:
            await asyncio.sleep(5)

    async def stop(self):
        logger.warning("trading_bot_stopping")
        self.running = False

        await self.market_engine.stop()
        await self.position_monitor.stop()
        await self.ticker_fallback.stop()

        for task in self._tasks:
            task.cancel()

        logger.info("trading_bot_stopped")

    # ─────────────────────────────────────────
    # Strategy execution on candle close
    # ─────────────────────────────────────────

    async def _on_candle_closed(self, event):
        """
        Called when a candle closes on any symbol.
        Runs all enabled strategies on that symbol.
        """
        payload = event.payload
        symbol = payload.get("symbol")

        if not symbol:
            return

        if not self.market_engine.is_ready(symbol):
            return

        dataframe = self.market_engine.get_candles_df(symbol)
        if dataframe is None:
            return

        strategies = self.strategy_loader.load_strategies()

        for strategy_name, strategy in strategies.items():
            if not strategy.enabled:
                continue

            try:
                signal = await strategy.generate_signal(dataframe)

                if signal == "HOLD":
                    continue

                logger.info(
                    "strategy_signal",
                    strategy=strategy_name,
                    symbol=symbol,
                    signal=signal,
                )

                # AI validation
                ai_signal = await self.ai_filter.confirm_trade(
                    signal=signal,
                    dataframe=dataframe,
                    strategy_name=strategy_name,
                )

                if ai_signal == "HOLD":
                    logger.info(
                        "ai_filtered_signal",
                        strategy=strategy_name,
                        original=signal,
                    )
                    continue

                # Risk validation
                approved = await self.risk_manager.validate_trade(
                    symbol=symbol,
                    signal=signal,
                    strategy=strategy,
                )

                if not approved:
                    continue

                # Open position through lifecycle service
                current_price = self.market_engine.get_latest_price(symbol)
                if not current_price:
                    continue

                stop_pct = getattr(strategy, "stop_loss_percent", 0.02)
                target_pct = getattr(strategy, "take_profit_percent", 0.04)
                trail_pct = getattr(strategy, "trailing_stop_percent", None)

                if signal == "BUY":
                    stop_loss = current_price * (1 - stop_pct)
                    take_profit = current_price * (1 + target_pct)
                else:
                    stop_loss = current_price * (1 + stop_pct)
                    take_profit = current_price * (1 - target_pct)

                position = await self.lifecycle.open_position(
                    symbol=symbol,
                    side=signal,
                    entry_price=current_price,
                    quantity=0.001,
                    strategy_name=strategy_name,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    trailing_stop_pct=trail_pct,
                )

                await self.risk_manager.register_trade()

                logger.info(
                    "position_opened",
                    position_id=position.id,
                    symbol=symbol,
                    signal=signal,
                    entry=current_price,
                )

            except Exception as e:
                logger.error(
                    "strategy_execution_error",
                    strategy=strategy_name,
                    error=str(e),
                )

    # ─────────────────────────────────────────
    # Periodic reconciliation loop
    # ─────────────────────────────────────────

    async def _reconciliation_loop(self):
        while self.running:
            try:
                await asyncio.sleep(60)
                await self.reconciliation.run()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("reconciliation_loop_error", error=str(e))
