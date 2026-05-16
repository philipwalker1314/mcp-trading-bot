"""
AnalyticsService — Phase 4 Analytics Engine.

Responsabilidades:
- Agregar métricas diarias de posiciones cerradas
- Calcular equity curve (curva de capital)
- Sharpe ratio anualizado
- Max drawdown desde equity curve
- Métricas de rendimiento del AI filter
- Estadísticas de duración de trades
"""

import math
from app.models.trade_events import TradeEvent  # noqa: F401 — fuerza registro del modelo
from app.models.trades import CloseReason, OrderStatus, Position
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.logger import get_logger
from app.models.daily_metrics import DailyMetric
from app.models.signals import Signal, SignalSource, SignalType
from app.models.trades import CloseReason, OrderStatus, Position

logger = get_logger("analytics_service")


class AnalyticsService:
    """
    Servicio de analytics puro — sin side effects fuera de DB.
    Todos los métodos son async y usan sesiones propias.
    """

    def __init__(self, session_factory: async_sessionmaker):
        self._factory = session_factory

    # ─────────────────────────────────────────
    # Rollup diario
    # ─────────────────────────────────────────

    async def run_daily_rollup(self, target_date: date) -> DailyMetric:
        """
        Agrega todas las posiciones cerradas en target_date
        y escribe (o actualiza) la fila en daily_metrics.

        Idempotente — se puede llamar múltiples veces para la misma fecha.
        """
        logger.info("rollup_starting", date=str(target_date))

        async with self._factory() as db:
            # Posiciones cerradas en el día target
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt   = datetime.combine(target_date, datetime.max.time())

            result = await db.execute(
                select(Position).where(
                    Position.status == OrderStatus.CLOSED,
                    Position.closed_at >= start_dt,
                    Position.closed_at <= end_dt,
                )
            )
            positions = result.scalars().all()

            if not positions:
                logger.info("rollup_no_trades", date=str(target_date))
                metric = await self._upsert_metric(db, target_date, self._zero_metric(target_date))
                await db.commit()
                return metric

            # Calcular stats desde PnLEngine
            pnls          = [p.realized_pnl for p in positions]
            wins          = [p for p in pnls if p > 0]
            losses        = [p for p in pnls if p <= 0]
            gross_profit  = sum(wins)
            gross_loss    = sum(losses)
            total_fees    = sum(p.total_fees for p in positions)

            win_rate = len(wins) / len(pnls) if pnls else 0.0
            profit_factor = (
                gross_profit / abs(gross_loss)
                if gross_loss != 0
                else float("inf") if gross_profit > 0 else 0.0
            )

            # Duración media en segundos
            durations = []
            for p in positions:
                if p.opened_at and p.closed_at:
                    delta = (p.closed_at - p.opened_at).total_seconds()
                    durations.append(delta)

            avg_duration = sum(durations) / len(durations) if durations else 0.0

            # Max drawdown intra-día (peak-to-trough de PnL acumulado)
            max_drawdown = self._calc_intraday_drawdown(pnls)

            # Max tamaño de posición del día
            max_pos_size = max(
                (p.avg_entry_price * p.total_quantity for p in positions),
                default=0.0,
            )

            data = {
                "date":                   target_date,
                "total_trades":           len(pnls),
                "winning_trades":         len(wins),
                "losing_trades":          len(losses),
                "realized_pnl":           sum(pnls),
                "gross_profit":           gross_profit,
                "gross_loss":             gross_loss,
                "total_fees":             total_fees,
                "max_drawdown":           max_drawdown,
                "max_position_size":      max_pos_size,
                "win_rate":               win_rate,
                "profit_factor":          profit_factor if profit_factor != float("inf") else 999.0,
                "avg_win":                sum(wins) / len(wins) if wins else 0.0,
                "avg_loss":               sum(losses) / len(losses) if losses else 0.0,
                "avg_trade_duration_sec": avg_duration,
            }

            metric = await self._upsert_metric(db, target_date, data)
            await db.commit()
            await db.refresh(metric)

        logger.info(
            "rollup_complete",
            date=str(target_date),
            total_trades=len(pnls),
            realized_pnl=round(sum(pnls), 4),
        )
        return metric

    # ─────────────────────────────────────────
    # Equity curve
    # ─────────────────────────────────────────

    async def get_equity_curve(self, days: int = 30) -> list[dict]:
        """
        Devuelve serie diaria de PnL acumulado para graficar.
        Formato: [{date, daily_pnl, cumulative_pnl}, ...]
        """
        since = date.today() - timedelta(days=days)

        async with self._factory() as db:
            result = await db.execute(
                select(DailyMetric)
                .where(DailyMetric.date >= since)
                .order_by(DailyMetric.date.asc())
            )
            metrics = result.scalars().all()

        cumulative = 0.0
        curve = []
        for m in metrics:
            cumulative += m.realized_pnl
            curve.append({
                "date":           str(m.date),
                "daily_pnl":      round(m.realized_pnl, 4),
                "cumulative_pnl": round(cumulative, 4),
                "total_trades":   m.total_trades,
                "win_rate":       round(m.win_rate, 4),
            })

        return curve

    # ─────────────────────────────────────────
    # Sharpe ratio
    # ─────────────────────────────────────────

    async def get_sharpe_ratio(self, days: int = 30) -> dict:
        """
        Sharpe ratio anualizado.
        Asume 252 días de trading, tasa libre de riesgo = 0.
        """
        since = date.today() - timedelta(days=days)

        async with self._factory() as db:
            result = await db.execute(
                select(DailyMetric.realized_pnl)
                .where(DailyMetric.date >= since)
                .order_by(DailyMetric.date.asc())
            )
            daily_pnls = [row[0] for row in result.fetchall()]

        if len(daily_pnls) < 2:
            return {"sharpe_ratio": 0.0, "days_used": len(daily_pnls), "insufficient_data": True}

        mean_pnl = sum(daily_pnls) / len(daily_pnls)
        variance = sum((x - mean_pnl) ** 2 for x in daily_pnls) / (len(daily_pnls) - 1)
        std_dev  = math.sqrt(variance) if variance > 0 else 0.0

        if std_dev == 0:
            return {"sharpe_ratio": 0.0, "days_used": len(daily_pnls), "insufficient_data": False}

        sharpe = (mean_pnl / std_dev) * math.sqrt(252)

        return {
            "sharpe_ratio":     round(sharpe, 4),
            "days_used":        len(daily_pnls),
            "mean_daily_pnl":   round(mean_pnl, 4),
            "std_daily_pnl":    round(std_dev, 4),
            "insufficient_data": False,
        }

    # ─────────────────────────────────────────
    # Max drawdown
    # ─────────────────────────────────────────

    async def get_max_drawdown(self, days: int = 30) -> dict:
        """
        Max drawdown peak-to-trough sobre la equity curve acumulada.
        """
        curve = await self.get_equity_curve(days=days)

        if not curve:
            return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0, "days_used": 0}

        cumulative_values = [c["cumulative_pnl"] for c in curve]
        max_dd, max_dd_pct = self._calc_max_drawdown(cumulative_values)

        return {
            "max_drawdown":     round(max_dd, 4),
            "max_drawdown_pct": round(max_dd_pct, 4),
            "days_used":        len(curve),
        }

    # ─────────────────────────────────────────
    # AI performance metrics
    # ─────────────────────────────────────────

    async def get_ai_performance_metrics(self) -> dict:
        """
        Compara rendimiento de trades validados por AI vs todos los trades.
        Usa la tabla signals para identificar cuáles pasaron el AI filter.
        """
        async with self._factory() as db:
            # Todos los trades cerrados
            result = await db.execute(
                select(Position).where(Position.status == OrderStatus.CLOSED)
            )
            all_positions = result.scalars().all()

            # Señales del AI filter (source = AI_FILTER)
            ai_result = await db.execute(
                select(Signal).where(
                    Signal.source == SignalSource.AI_FILTER,
                    Signal.signal.in_([SignalType.BUY, SignalType.SELL]),
                )
            )
            ai_signals = ai_result.scalars().all()

        if not all_positions:
            return {
                "total_trades":      0,
                "ai_validated":      len(ai_signals),
                "overall_win_rate":  0.0,
                "ai_signal_count":   len(ai_signals),
                "avg_ai_confidence": 0.0,
            }

        all_pnls = [p.realized_pnl for p in all_positions]
        overall_win_rate = len([p for p in all_pnls if p > 0]) / len(all_pnls)

        avg_confidence = (
            sum(s.confidence for s in ai_signals) / len(ai_signals)
            if ai_signals else 0.0
        )

        return {
            "total_trades":      len(all_positions),
            "ai_validated":      len(ai_signals),
            "overall_win_rate":  round(overall_win_rate, 4),
            "ai_signal_count":   len(ai_signals),
            "avg_ai_confidence": round(avg_confidence, 4),
            "total_realized_pnl": round(sum(all_pnls), 4),
        }

    # ─────────────────────────────────────────
    # Trade duration stats
    # ─────────────────────────────────────────

    async def get_trade_duration_stats(self) -> dict:
        """
        Estadísticas de duración de trades cerrados.
        """
        async with self._factory() as db:
            result = await db.execute(
                select(Position).where(
                    Position.status == OrderStatus.CLOSED,
                    Position.opened_at.isnot(None),
                    Position.closed_at.isnot(None),
                )
            )
            positions = result.scalars().all()

        if not positions:
            return {
                "total_closed": 0,
                "avg_duration_sec": 0.0,
                "avg_duration_human": "—",
                "min_duration_sec": 0.0,
                "max_duration_sec": 0.0,
                "by_close_reason": {},
            }

        durations = [
            (p.closed_at - p.opened_at).total_seconds()
            for p in positions
        ]

        # Por close reason
        by_reason: dict[str, list[float]] = {}
        for p in positions:
            reason = p.close_reason.value if p.close_reason else "UNKNOWN"
            dur = (p.closed_at - p.opened_at).total_seconds()
            by_reason.setdefault(reason, []).append(dur)

        reason_stats = {
            reason: {
                "count": len(durs),
                "avg_sec": round(sum(durs) / len(durs), 1),
            }
            for reason, durs in by_reason.items()
        }

        avg_sec = sum(durations) / len(durations)

        return {
            "total_closed":       len(positions),
            "avg_duration_sec":   round(avg_sec, 1),
            "avg_duration_human": self._fmt_duration(avg_sec),
            "min_duration_sec":   round(min(durations), 1),
            "max_duration_sec":   round(max(durations), 1),
            "by_close_reason":    reason_stats,
        }

    # ─────────────────────────────────────────
    # Catchup — rellena días faltantes
    # ─────────────────────────────────────────

    async def catchup_missing_days(self, days: int = 30) -> int:
        """
        Al arrancar, rellena cualquier día sin rollup.
        Devuelve el número de días procesados.
        """
        since = date.today() - timedelta(days=days)
        processed = 0

        async with self._factory() as db:
            result = await db.execute(
                select(DailyMetric.date).where(DailyMetric.date >= since)
            )
            existing_dates = {row[0] for row in result.fetchall()}

        current = since
        while current < date.today():
            if current not in existing_dates:
                try:
                    await self.run_daily_rollup(current)
                    processed += 1
                except Exception as e:
                    logger.error("catchup_rollup_error", date=str(current), error=str(e))
            current += timedelta(days=1)

        logger.info("catchup_complete", days_processed=processed)
        return processed

    # ─────────────────────────────────────────
    # Internos
    # ─────────────────────────────────────────

    @staticmethod
    def _calc_max_drawdown(values: list[float]) -> tuple[float, float]:
        """Peak-to-trough max drawdown absoluto y porcentual."""
        if not values:
            return 0.0, 0.0

        peak     = values[0]
        max_dd   = 0.0
        max_dd_pct = 0.0

        for v in values:
            if v > peak:
                peak = v
            dd = peak - v
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = (dd / peak * 100) if peak != 0 else 0.0

        return max_dd, max_dd_pct

    @staticmethod
    def _calc_intraday_drawdown(pnls: list[float]) -> float:
        """Drawdown máximo sobre serie de PnL acumulado intra-día."""
        if not pnls:
            return 0.0
        running = 0.0
        peak    = 0.0
        max_dd  = 0.0
        for p in pnls:
            running += p
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

    @staticmethod
    def _zero_metric(target_date: date) -> dict:
        return {
            "date": target_date,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "realized_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "total_fees": 0.0,
            "max_drawdown": 0.0,
            "max_position_size": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "avg_trade_duration_sec": 0.0,
        }

    async def _upsert_metric(
        self,
        db: AsyncSession,
        target_date: date,
        data: dict,
    ) -> DailyMetric:
        """Crea o actualiza la fila de DailyMetric para target_date."""
        result = await db.execute(
            select(DailyMetric).where(DailyMetric.date == target_date)
        )
        metric = result.scalar_one_or_none()

        if metric is None:
            metric = DailyMetric(**data)
            db.add(metric)
        else:
            for k, v in data.items():
                if k != "date":
                    setattr(metric, k, v)
            metric.updated_at = datetime.utcnow()

        return metric
