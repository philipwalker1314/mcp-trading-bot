"""
Trade model — production-grade state machine.

Key design decisions:
- Trade = individual execution event (fill)
- Position = aggregated state across fills
- These are separate concepts
- Full order state machine (not just OPEN/CLOSED)
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class TradeSide(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """
    Full order state machine.
    OPEN/CLOSED alone is not sufficient for
    real trading — partial fills, network
    failures and broker rejects all require
    intermediate states.
    """
    PENDING          = "PENDING"
    SUBMITTED        = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED           = "FILLED"    # position is now OPEN
    CLOSING          = "CLOSING"
    CLOSED           = "CLOSED"
    CANCELLED        = "CANCELLED"
    REJECTED         = "REJECTED"
    ERROR            = "ERROR"


class CloseReason(str, Enum):
    STOP_LOSS     = "STOP_LOSS"
    TAKE_PROFIT   = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    MANUAL        = "MANUAL"
    EMERGENCY     = "EMERGENCY"
    PARTIAL       = "PARTIAL"
    RECONCILIATION = "RECONCILIATION"  # broker sync forced close


# ─────────────────────────────────────────────
# Position
# Aggregated state across one or more fills.
# positions
#   └── trades (fills)
#       └── trade_events
# ─────────────────────────────────────────────

class Position(Base):
    """
    Represents the aggregated market exposure
    for a symbol. A position can have multiple
    trade fills and partial exits beneath it.

    This is the entity that has SL/TP/trailing.
    Individual fills do not.
    """
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
    )

    side: Mapped[TradeSide] = mapped_column(
        SqlEnum(TradeSide), nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    strategy_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )

    # ── Price levels ──────────────────────────

    avg_entry_price: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    exit_price: Mapped[float | None] = mapped_column(
        Float, nullable=True,
    )

    total_quantity: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    remaining_quantity: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    # ── Risk levels (live, updated by monitor) ─

    stop_loss: Mapped[float | None] = mapped_column(
        Float, nullable=True,
    )

    take_profit: Mapped[float | None] = mapped_column(
        Float, nullable=True,
    )

    trailing_stop_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True,  # e.g. 0.015 = 1.5%
    )

    trailing_stop_price: Mapped[float | None] = mapped_column(
        Float, nullable=True,  # current calculated trailing level
    )

    # ── PnL ───────────────────────────────────

    unrealized_pnl: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    realized_pnl: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    total_fees: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # ── Excursion tracking ────────────────────
    # MFE/MAE are used for analytics and
    # eventual AI performance feedback.

    max_favorable_excursion: Mapped[float] = mapped_column(
        Float, default=0.0,  # best unrealized pnl reached
    )

    max_adverse_excursion: Mapped[float] = mapped_column(
        Float, default=0.0,  # worst unrealized pnl reached
    )

    # ── Close metadata ────────────────────────

    close_reason: Mapped[CloseReason | None] = mapped_column(
        SqlEnum(CloseReason), nullable=True,
    )

    # ── Broker reconciliation ─────────────────

    exchange_position_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True,
    )

    last_reconciled_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )

    # ── Timestamps ────────────────────────────

    opened_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ── Relationships ─────────────────────────

    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="position",
        lazy="selectin",
    )

    events: Mapped[list["TradeEvent"]] = relationship(
        "TradeEvent",
        back_populates="position",
        lazy="selectin",
    )


# ─────────────────────────────────────────────
# Trade
# Individual execution fill beneath a Position.
# ─────────────────────────────────────────────

class Trade(Base):
    """
    Represents a single execution fill.
    Multiple trades can belong to one Position
    (scaling in/out, partial fills).
    """
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )

    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id"),
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
    )

    side: Mapped[TradeSide] = mapped_column(
        SqlEnum(TradeSide), nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    fill_price: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    quantity: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    fees: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # Broker-side identifiers for reconciliation
    exchange_order_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True,
    )

    exchange_trade_id: Mapped[str | None] = mapped_column(
        String(120), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ── Relationships ─────────────────────────

    position: Mapped["Position"] = relationship(
        "Position", back_populates="trades",
    )
