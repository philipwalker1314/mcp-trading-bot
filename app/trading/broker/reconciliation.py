from datetime import datetime

from app.config import settings
from app.logger import get_logger
from app.models.trades import CloseReason, Position
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
        FIX 4: Skip entirely when PAPER_TRADING=true.
        There is no real exchange position to reconcile against,
        so every previous run was a no-op that still hit the DB
        and Binance API every 60 seconds.
        """
        if settings.PAPER_TRADING:
            logger.debug("reconciliation_skipped_paper_trading")
            return {
                "force_closed":    [],
                "qty_adjusted":    [],
                "orphan_imported": [],
                "errors":          [],
                "skipped":         True,
            }

        logger.info("reconciliation_started")

        actions = {
            "force_closed":    [],
            "qty_adjusted":    [],
            "orphan_imported": [],
            "errors":          [],
            "skipped":         False,
        }

        try:
            exchange_positions = await self._fetch_exchange_positions()
            local_positions    = await self.lifecycle.get_open_positions()

            await self._reconcile(local_positions, exchange_positions, actions)

        except Exception as e:
            logger.error("reconciliation_error", error=str(e))
            actions["errors"].append(str(e))

        logger.info(
            "reconciliation_completed",
            force_closed=len(actions["force_closed"]),
            qty_adjusted=len(actions["qty_adjusted"]),
        )

        return actions

    async def _reconcile(
        self,
        local:    list[Position],
        exchange: dict[str, dict],
        actions:  dict,
    ):
        exchange_symbols = set(exchange.keys())
        local_symbols    = {p.symbol for p in local}
        ghost_symbols    = local_symbols - exchange_symbols

        for position in local:
            if position.symbol in ghost_symbols:
                logger.warning(
                    "ghost_position_detected",
                    symbol=position.symbol,
                    position_id=position.id,
                )

                close_price = (
                    exchange.get(position.symbol, {})
                    .get("price", position.avg_entry_price)
                )

                await self.lifecycle.close_position(
                    position.id,
                    close_price,
                    CloseReason.RECONCILIATION,
                )
                await self._stamp_reconciled(position.id)

                actions["force_closed"].append({
                    "position_id": position.id,
                    "symbol":      position.symbol,
                    "reason":      "not_on_exchange",
                })

            else:
                ex_qty    = exchange.get(position.symbol, {}).get("qty", 0)
                local_qty = position.remaining_quantity

                if abs(ex_qty - local_qty) > 0.000001:
                    logger.warning(
                        "quantity_mismatch",
                        symbol=position.symbol,
                        local_qty=local_qty,
                        exchange_qty=ex_qty,
                    )
                    actions["qty_adjusted"].append({
                        "position_id":  position.id,
                        "symbol":       position.symbol,
                        "local_qty":    local_qty,
                        "exchange_qty": ex_qty,
                    })

                await self._stamp_reconciled(position.id)

    async def _fetch_exchange_positions(self) -> dict[str, dict]:
        try:
            balance   = await self.binance.fetch_balance()
            positions = {}

            for item in balance.get("info", {}).get("balances", []):
                asset = item.get("asset", "")
                free  = float(item.get("free", 0))
                if free > 0:
                    positions[asset] = {"qty": free, "price": 0.0}

            return positions

        except Exception as e:
            logger.error("fetch_exchange_positions_error", error=str(e))
            return {}

    async def _stamp_reconciled(self, position_id: int):
        from app.database import AsyncSessionLocal
        from sqlalchemy import update

        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Position)
                .where(Position.id == position_id)
                .values(last_reconciled_at=datetime.utcnow())
            )
            await db.commit()
