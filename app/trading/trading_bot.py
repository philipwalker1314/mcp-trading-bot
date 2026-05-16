"""
TradingBot — Phase 7: Selective AI Filter.

Phase 7 changes vs Phase 6:
  - Imports SignalStrengthEvaluator + AITokenTracker
  - _on_candle_closed: evaluates signal strength before AI call
  - Strong signals (strength >= strategy.confidence_threshold) → skip AI
  - Weak signals → call AI as before
  - All calls logged to AITokenTracker for /ai-metrics endpoint

Previous phases preserved:
  Fix 1: risk manager checks per-symbol
  Fix 2: trailing stop audit log throttled
  Fix 3: _on_position_closed syncs risk_manager._open_symbols
  Fix 4: reconciliation skipped in paper trading
  Fix 5: strategy_loader uses mtime cache
  Phase 5: DBStrategyLoader (file + DB strategies merged)
  Phase 6: CopilotService

Key execution order (unchanged from Phase 5/6):
  strategy → risk → [strength eval] → AI (if needed) → open
"""

import asyncio

from app.config import settings
from app.database import AsyncSessionLocal
from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.services.binance_service import BinanceService
from app.trading.ai_filter import AIFilter
from app.trading.ai_token_tracker import ai_token_tracker
from app.trading.broker.reconciliation import BrokerReconciliationService
from app.trading.db_strategy_loader import DBStrategyLoader
from app.trading.engines.market_data_engine import MarketDataEngine
from app.trading.lifecycle.position_monitor import (
    PositionMonitor,
    PositionMonitorFallback,
)
from app.trading.lifecycle.trade_lifecycle_service import TradeLifecycleService
from app.trading.risk_manager import RiskManager
from app.trading.signal_strength_evaluator import SignalStrengthEvaluator
from app.websocket.manager import register_ws_handlers

logger = get_logger("trading_bot")

SYMBOLS = ["BTC/USDT"]


class TradingBot:

    def __init__(self):

        # ── Core infrastructure ──────────────
        self.event_bus = EventBus()
        self.binance   = BinanceService()

        # ── Lifecycle ────────────────────────
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

        self.ticker_fallback = PositionMonitorFallback(
            event_bus=self.event_bus,
            market_data_service=self.market_engine,
            symbols=SYMBOLS,
            interval_seconds=10.0,
        )

        # ── Strategy ─────────────────────────
        self.db_strategy_loader = DBStrategyLoader(
            session_factory=AsyncSessionLocal,
        )
        self.ai_filter    = AIFilter()
        self.risk_manager = RiskManager()

        # ── Phase 7: Signal strength evaluator ─
        self.signal_evaluator = SignalStrengthEvaluator()

        # ── Broker reconciliation ────────────
        self.reconciliation = BrokerReconciliationService(
            lifecycle=self.lifecycle,
            binance=self.binance,
        )

        self.running  = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        logger.info("trading_bot_starting")
        self.running = True

        register_ws_handlers(self.event_bus)

        self.event_bus.subscribe(Events.CANDLE_CLOSED,   self._on_candle_closed)
        self.event_bus.subscribe(Events.POSITION_CLOSED, self._on_position_closed)

        try:
            await asyncio.wait_for(self.reconciliation.run(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("reconciliation_startup_timeout_skipped")
        except Exception as e:
            logger.warning("reconciliation_startup_skipped", error=str(e))

        self._tasks.append(
            asyncio.create_task(self.market_engine.start(), name="market_data_engine")
        )

        await self.position_monitor.start()

        if settings.PAPER_TRADING:
            self._tasks.append(
                asyncio.create_task(self.ticker_fallback.start(), name="ticker_fallback")
            )

        self._tasks.append(
            asyncio.create_task(self._reconciliation_loop(), name="reconciliation_loop")
        )

        logger.info("trading_bot_started")

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
    # FIX 3: keep risk_manager in sync on all closes
    # ─────────────────────────────────────────

    async def _on_position_closed(self, event):
        symbol = event.payload.get("symbol")
        await self.risk_manager.close_trade(symbol=symbol)
        logger.debug("risk_manager_synced_on_close", symbol=symbol)

    # ─────────────────────────────────────────
    # Strategy execution — Phase 7 selective AI
    # ─────────────────────────────────────────

    async def _on_candle_closed(self, event):
        payload = event.payload
        symbol  = payload.get("symbol")

        if not symbol:
            return

        if not self.market_engine.is_ready(symbol):
            return

        dataframe = self.market_engine.get_candles_df(symbol)
        if dataframe is None:
            return

        strategies = await self.db_strategy_loader.load_strategies_async()

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

                # ── Risk check (cheap, in-memory) ─────────────────────
                approved = await self.risk_manager.validate_trade(
                    symbol=symbol,
                    signal=signal,
                    strategy=strategy,
                )

                if not approved:
                    logger.info(
                        "signal_pre_rejected_by_risk",
                        strategy=strategy_name,
                        symbol=symbol,
                        signal=signal,
                    )
                    continue

                # ── Phase 7: Signal strength evaluation ───────────────
                # Read per-strategy AI config (with safe fallbacks for
                # file-based strategies that don't have these attributes).
                ai_required   = getattr(strategy, "ai_validation_required",  True)
                threshold     = getattr(strategy, "confidence_threshold",     0.75)

                strength = SignalStrengthEvaluator.evaluate(dataframe, signal)

                # Decision tree:
                #   1. ai_validation_required=False → always skip AI
                #   2. strength >= threshold        → strong signal, skip AI
                #   3. otherwise                    → call AI
                skip_ai = (not ai_required) or (strength >= threshold)

                if skip_ai:
                    logger.info(
                        "ai_filter_skipped",
                        strategy=strategy_name,
                        symbol=symbol,
                        signal=signal,
                        strength=strength,
                        threshold=threshold,
                        ai_required=ai_required,
                    )
                    ai_token_tracker.record_signal(
                        symbol=symbol,
                        signal=signal,
                        strength=strength,
                        skipped=True,
                        ai_result=None,
                    )
                    ai_signal = signal  # trust the strategy directly

                else:
                    logger.info(
                        "ai_filter_calling",
                        strategy=strategy_name,
                        symbol=symbol,
                        signal=signal,
                        strength=strength,
                        threshold=threshold,
                    )
                    ai_signal = await self.ai_filter.confirm_trade(
                        signal=signal,
                        dataframe=dataframe,
                        strategy_name=strategy_name,
                    )
                    ai_token_tracker.record_signal(
                        symbol=symbol,
                        signal=signal,
                        strength=strength,
                        skipped=False,
                        ai_result=ai_signal,
                    )

                if ai_signal == "HOLD":
                    logger.info(
                        "ai_filtered_signal",
                        strategy=strategy_name,
                        original=signal,
                    )
                    continue

                # ── Open position ─────────────────────────────────────
                current_price = self.market_engine.get_latest_price(symbol)
                if not current_price:
                    continue

                stop_pct   = getattr(strategy, "stop_loss_percent",    0.02)
                target_pct = getattr(strategy, "take_profit_percent",   0.04)
                trail_pct  = getattr(strategy, "trailing_stop_percent", None)

                if signal == "BUY":
                    stop_loss   = current_price * (1 - stop_pct)
                    take_profit = current_price * (1 + target_pct)
                else:
                    stop_loss   = current_price * (1 + stop_pct)
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

                await self.risk_manager.register_trade(symbol=symbol)

                logger.info(
                    "position_opened",
                    position_id=position.id,
                    symbol=symbol,
                    signal=signal,
                    entry=current_price,
                    strength=strength,
                    ai_skipped=skip_ai,
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
