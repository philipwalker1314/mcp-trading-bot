from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.models.trade_events import TradeEvent, TradeEventType
from app.models.trades import (
    CloseReason,
    OrderStatus,
    Position,
    Trade,
    TradeSide,
)
from app.trading.lifecycle.pnl_engine import PnLEngine

logger = get_logger("lifecycle")


class TradeLifecycleService:
    """
    The single authoritative service for all
    position and trade state transitions.

    Rules:
    - open_position()  → creates Position + Trade (fill)
    - close_position() → updates Position + logs event
    - No other service writes to positions directly
    - All transitions emit events via EventBus
    """

    def __init__(
        self,
        session_factory: async_sessionmaker,
        event_bus: EventBus,
    ):
        self._factory   = session_factory
        self._event_bus = event_bus
        self._pnl       = PnLEngine()

    # ─────────────────────────────────────────
    # Open
    # ─────────────────────────────────────────

    async def open_position(
        self,
        symbol:          str,
        side:            str,
        entry_price:     float,
        quantity:        float,
        strategy_name:   str,
        stop_loss:       float | None = None,
        take_profit:     float | None = None,
        trailing_stop_pct: float | None = None,
        exchange_order_id: str | None = None,
    ) -> Position:
        """
        Create a new Position and its initial Trade fill.
        Emits: Events.POSITION_OPENED
        """
        async with self._factory() as db:

            position = Position(
                symbol=symbol,
                side=TradeSide(side.upper()),
                status=OrderStatus.FILLED,
                strategy_name=strategy_name,
                avg_entry_price=entry_price,
                total_quantity=quantity,
                remaining_quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                trailing_stop_pct=trailing_stop_pct,
                trailing_stop_price=None,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                total_fees=0.0,
                exchange_position_id=exchange_order_id,
            )
            db.add(position)
            await db.flush()  # get position.id

            # Record the fill as a Trade
            fill = Trade(
                position_id=position.id,
                symbol=symbol,
                side=TradeSide(side.upper()),
                status=OrderStatus.FILLED,
                fill_price=entry_price,
                quantity=quantity,
                fees=PnLEngine.calc_fees(entry_price, quantity),
                exchange_order_id=exchange_order_id,
            )
            db.add(fill)
            position.total_fees += fill.fees

            # Audit trail
            await self._log_event(
                db=db,
                position_id=position.id,
                event_type=TradeEventType.POSITION_OPENED,
                price=entry_price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                metadata={
                    "strategy": strategy_name,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "trailing_stop_pct": trailing_stop_pct,
                },
            )

            await db.commit()
            await db.refresh(position)

        logger.info(
            "position_opened",
            position_id=position.id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
        )

        await self._event_bus.publish(
            Events.POSITION_OPENED,
            self._position_to_dict(position),
        )

        return position

    # ─────────────────────────────────────────
    # Close (full)
    # ─────────────────────────────────────────

    async def close_position(
        self,
        position_id: int,
        exit_price:  float,
        reason:      CloseReason,
    ) -> Position | None:
        """
        Close a position fully.
        Calculates realized PnL, updates status,
        records audit event, broadcasts.
        Emits: Events.POSITION_CLOSED
        """
        async with self._factory() as db:

            position = await db.get(Position, position_id)

            if not position:
                logger.warning("close_position_not_found", id=position_id)
                return None

            if position.status not in (
                OrderStatus.FILLED,
                OrderStatus.PARTIALLY_FILLED,
            ):
                logger.warning(
                    "close_position_invalid_status",
                    id=position_id,
                    status=position.status,
                )
                return None

            realized_pnl = PnLEngine.calc_realized_pnl(
                position, exit_price
            )
            exit_fees = PnLEngine.calc_fees(
                exit_price, position.remaining_quantity
            )

            position.status          = OrderStatus.CLOSED
            position.exit_price      = exit_price
            position.realized_pnl    = realized_pnl
            position.unrealized_pnl  = 0.0
            position.total_fees      += exit_fees
            position.remaining_quantity = 0.0
            position.close_reason    = reason
            position.closed_at       = datetime.utcnow()

            event_type = {
                CloseReason.STOP_LOSS:     TradeEventType.STOP_LOSS_HIT,
                CloseReason.TRAILING_STOP: TradeEventType.TRAILING_STOP_HIT,
                CloseReason.TAKE_PROFIT:   TradeEventType.TAKE_PROFIT_HIT,
                CloseReason.MANUAL:        TradeEventType.MANUAL_CLOSE,
                CloseReason.EMERGENCY:     TradeEventType.EMERGENCY_CLOSE,
                CloseReason.RECONCILIATION: TradeEventType.RECONCILIATION_CLOSE,
            }.get(reason, TradeEventType.MANUAL_CLOSE)

            await self._log_event(
                db=db,
                position_id=position.id,
                event_type=event_type,
                price=exit_price,
                unrealized_pnl=0.0,
                realized_pnl=realized_pnl,
                metadata={"close_reason": reason.value},
            )

            await db.commit()
            await db.refresh(position)

        logger.info(
            "position_closed",
            position_id=position_id,
            reason=reason.value,
            exit_price=exit_price,
            realized_pnl=realized_pnl,
        )

        await self._event_bus.publish(
            Events.POSITION_CLOSED,
            self._position_to_dict(position),
        )

        return position

    # ─────────────────────────────────────────
    # Partial close
    # ─────────────────────────────────────────

    async def partial_close(
        self,
        position_id:    int,
        exit_price:     float,
        exit_quantity:  float,
    ) -> Position | None:
        """
        Close part of a position (scale out).
        Updates remaining_quantity and cumulates
        realized PnL.
        """
        async with self._factory() as db:

            position = await db.get(Position, position_id)
            if not position or position.status != OrderStatus.FILLED:
                return None

            if exit_quantity >= position.remaining_quantity:
                # treat as full close
                return await self.close_position(
                    position_id, exit_price, CloseReason.PARTIAL
                )

            partial_pnl = PnLEngine.calc_realized_pnl(
                position, exit_price, exit_quantity
            )
            exit_fees = PnLEngine.calc_fees(exit_price, exit_quantity)

            position.realized_pnl       += partial_pnl
            position.total_fees         += exit_fees
            position.remaining_quantity -= exit_quantity
            position.status              = OrderStatus.PARTIALLY_FILLED

            await self._log_event(
                db=db,
                position_id=position.id,
                event_type=TradeEventType.POSITION_PARTIALLY_CLOSED,
                price=exit_price,
                unrealized_pnl=position.unrealized_pnl,
                realized_pnl=position.realized_pnl,
                metadata={
                    "exit_quantity": exit_quantity,
                    "remaining_quantity": position.remaining_quantity,
                    "partial_pnl": partial_pnl,
                },
            )

            await db.commit()
            await db.refresh(position)

        return position

    # ─────────────────────────────────────────
    # Realtime PnL update (called by monitor)
    # ─────────────────────────────────────────

    async def update_unrealized_pnl(
        self,
        position_id:   int,
        current_price: float,
    ):
        """
        Update mark-to-market PnL and track
        MFE / MAE (max favorable/adverse excursion).
        Called frequently — no event emitted to
        avoid flooding the bus. WebSocket gets
        price directly from market stream instead.
        """
        async with self._factory() as db:
            position = await db.get(Position, position_id)
            if not position:
                return

            upnl = PnLEngine.calc_unrealized_pnl(position, current_price)
            position.unrealized_pnl = upnl

            if upnl > position.max_favorable_excursion:
                position.max_favorable_excursion = upnl

            if upnl < position.max_adverse_excursion:
                position.max_adverse_excursion = upnl

            await db.commit()

    # ─────────────────────────────────────────
    # Trailing stop update
    # ─────────────────────────────────────────

    async def update_trailing_stop(
        self,
        position_id:   int,
        current_price: float,
    ) -> float | None:
        """
        Recalculate and persist trailing stop.
        Returns new stop price if updated, else None.
        Emits: Events.TRAILING_UPDATED if stop moved.
        """
        async with self._factory() as db:
            position = await db.get(Position, position_id)
            if not position:
                return None

            new_stop = PnLEngine.calc_trailing_stop(position, current_price)
            if new_stop is None:
                return None

            old_stop = position.trailing_stop_price

            if old_stop is not None and new_stop == old_stop:
                return None  # no change

            position.trailing_stop_price = new_stop

            await self._log_event(
                db=db,
                position_id=position.id,
                event_type=TradeEventType.STOP_LOSS_MOVED,
                price=current_price,
                unrealized_pnl=position.unrealized_pnl,
                realized_pnl=position.realized_pnl,
                metadata={
                    "old_stop": old_stop,
                    "new_stop": new_stop,
                },
            )

            await db.commit()

        await self._event_bus.publish(
            Events.TRAILING_UPDATED,
            {"position_id": position_id, "new_stop": new_stop},
        )

        return new_stop

    # ─────────────────────────────────────────
    # Emergency close all
    # ─────────────────────────────────────────

    async def emergency_close_all(
        self,
        current_prices: dict[str, float],
    ) -> list[Position]:
        """
        Close all open positions immediately.
        Uses last known price for each symbol.
        Emits: Events.EMERGENCY_STOP
        """
        open_positions = await self.get_open_positions()
        closed = []

        for position in open_positions:
            price = current_prices.get(
                position.symbol,
                position.avg_entry_price,  # fallback
            )
            result = await self.close_position(
                position.id, price, CloseReason.EMERGENCY
            )
            if result:
                closed.append(result)

        logger.critical(
            "emergency_close_all_executed",
            positions_closed=len(closed),
        )

        await self._event_bus.publish(
            Events.EMERGENCY_STOP,
            {"positions_closed": len(closed)},
        )

        return closed

    # ─────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────

    async def get_open_positions(self) -> list[Position]:
        async with self._factory() as db:
            result = await db.execute(
                select(Position).where(
                    Position.status.in_([
                        OrderStatus.FILLED,
                        OrderStatus.PARTIALLY_FILLED,
                    ])
                )
            )
            return list(result.scalars().all())

    async def get_position(self, position_id: int) -> Position | None:
        async with self._factory() as db:
            return await db.get(Position, position_id)

    # ─────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────

    @staticmethod
    async def _log_event(
        db:             AsyncSession,
        position_id:    int,
        event_type:     TradeEventType,
        price:          float,
        unrealized_pnl: float,
        realized_pnl:   float,
        metadata:       dict | None = None,
    ):
        event = TradeEvent(
            position_id=position_id,
            event_type=event_type,
            price_at_event=price,
            unrealized_pnl_at_event=unrealized_pnl,
            realized_pnl_at_event=realized_pnl,
            metadata=metadata,
        )
        db.add(event)

    @staticmethod
    def _position_to_dict(position: Position) -> dict:
        return {
            "id":               position.id,
            "symbol":           position.symbol,
            "side":             position.side.value,
            "status":           position.status.value,
            "avg_entry_price":  position.avg_entry_price,
            "exit_price":       position.exit_price,
            "remaining_qty":    position.remaining_quantity,
            "unrealized_pnl":   position.unrealized_pnl,
            "realized_pnl":     position.realized_pnl,
            "stop_loss":        position.stop_loss,
            "take_profit":      position.take_profit,
            "trailing_stop":    position.trailing_stop_price,
            "close_reason":     position.close_reason.value if position.close_reason else None,
            "strategy":         position.strategy_name,
            "opened_at":        position.opened_at.isoformat() if position.opened_at else None,
            "closed_at":        position.closed_at.isoformat() if position.closed_at else None,
        }
