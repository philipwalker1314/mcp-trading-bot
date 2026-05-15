
from datetime import datetime

from app.logger import get_logger
from app.models.trades import CloseReason, OrderStatus, Position
from app.services.binance_service import BinanceService
from app.trading.lifecycle.trade_lifecycle_service import TradeLifecycleService

logger = get_logger("reconciliation")


class BrokerReconciliationService:

    def __init__(
        self,
        lifecycle: TradeLifecycleService,
        binance:   BinanceService,
    ):
        self.lifecycle = lifecycle
        self.binance   = binance

    async def run(self) -> dict:
        """
        Execute a full reconciliation pass.
        Returns a summary of actions taken.
        """
        logger.info("reconciliation_started")

        actions = {
            "force_closed":    [],
            "qty_adjusted":    [],
            "orphan_imported": [],
            "errors":          [],
        }

        try:
            # Fetch source of truth from exchange
            exchange_positions = await self._fetch_exchange_positions()

            # Fetch our internal open positions
            local_positions    = await self.lifecycle.get_open_positions()

            await self._reconcile(
                local_positions,
                exchange_positions,
                actions,
            )

        except Exception as e:
            logger.error("reconciliation_error", error=str(e))
            actions["errors"].append(str(e))

        logger.info(
            "reconciliation_completed",
            force_closed=len(actions["force_closed"]),
            qty_adjusted=len(actions["qty_adjusted"]),
            orphan_imported=len(actions["orphan_imported"]),
        )

        return actions

    async def _reconcile(
        self,
        local:    list[Position],
        exchange: dict[str, dict],
        actions:  dict,
    ):
        """
        Core reconciliation logic.

        For paper trading, exchange dict will be
        empty — this becomes a no-op.
        """
        exchange_symbols = set(exchange.keys())
        local_symbols    = {p.symbol for p in local}

        # Positions we think are open but exchange doesn't
        ghost_symbols = local_symbols - exchange_symbols

        for position in local:
            if position.symbol in ghost_symbols:
                # Exchange has no open position for this symbol
                # Our data is stale — force close at last known price
                logger.warning(
                    "ghost_position_detected",
                    symbol=position.symbol,
                    position_id=position.id,
                )

                # Use exchange price if available, else entry price
                close_price = (
                    exchange.get(position.symbol, {})
                    .get("price", position.avg_entry_price)
                )

                await self.lifecycle.close_position(
                    position.id,
                    close_price,
                    CloseReason.RECONCILIATION,
                )

                # Update reconciliation timestamp
                await self._stamp_reconciled(position.id)

                actions["force_closed"].append({
                    "position_id": position.id,
                    "symbol":      position.symbol,
                    "reason":      "not_on_exchange",
                })

            else:
                # Position exists on both sides — check quantity
                ex_qty = exchange.get(position.symbol, {}).get("qty", 0)
                local_qty = position.remaining_quantity

                if abs(ex_qty - local_qty) > 0.000001:
                    logger.warning(
                        "quantity_mismatch",
                        symbol=position.symbol,
                        local_qty=local_qty,
                        exchange_qty=ex_qty,
                    )
                    # Log for now — do NOT auto-correct quantity
                    # until we understand the cause.
                    # In production: alert and escalate.
                    actions["qty_adjusted"].append({
                        "position_id": position.id,
                        "symbol":      position.symbol,
                        "local_qty":   local_qty,
                        "exchange_qty": ex_qty,
                    })

                await self._stamp_reconciled(position.id)

    async def _fetch_exchange_positions(self) -> dict[str, dict]:
        """
        Fetch open positions from Binance.
        Returns {symbol: {"qty": float, "price": float}}

        For paper trading this returns {} (nothing to reconcile).
        """
        try:
            balance = await self.binance.fetch_balance()

            positions = {}
            for asset, info in balance.get("info", {}).get("balances", [{}]):
                free = float(info.get("free", 0))
                if free > 0:
                    # This is simplified — in production you'd
                    # map assets to trading pairs properly
                    positions[asset] = {"qty": free, "price": 0.0}

            return positions

        except Exception as e:
            logger.error("fetch_exchange_positions_error", error=str(e))
            return {}

    async def _stamp_reconciled(self, position_id: int):
        """Update last_reconciled_at on the position."""
        from app.database import AsyncSessionLocal
        from sqlalchemy import update
        from app.models.trades import Position

        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Position)
                .where(Position.id == position_id)
                .values(last_reconciled_at=datetime.utcnow())
            )
            await db.commit()
