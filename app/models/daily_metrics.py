"""
DailyMetric — aggregated performance per trading day.

Populated by the MetricsService on each
trade close and at end-of-day rollup.
"""

from datetime import date, datetime

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database import Base


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    __table_args__ = (
        UniqueConstraint("date", name="uq_daily_metrics_date"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )

    date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
    )

    # ── Volume ────────────────────────────────

    total_trades: Mapped[int] = mapped_column(
        Integer, default=0,
    )

    winning_trades: Mapped[int] = mapped_column(
        Integer, default=0,
    )

    losing_trades: Mapped[int] = mapped_column(
        Integer, default=0,
    )

    # ── PnL ───────────────────────────────────

    realized_pnl: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    gross_profit: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    gross_loss: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    total_fees: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # ── Risk metrics ──────────────────────────

    max_drawdown: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    max_position_size: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # ── Derived metrics (computed on update) ──

    win_rate: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    profit_factor: Mapped[float] = mapped_column(
        Float, default=0.0,  # gross_profit / abs(gross_loss)
    )

    avg_win: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    avg_loss: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    avg_trade_duration_sec: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # ── Timestamp ─────────────────────────────

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
