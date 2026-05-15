"""
TradeEvent — complete audit trail.

Every significant state change in a position's
lifecycle is recorded here. This enables:
- debugging
- analytics
- AI training data
- backtesting reconstruction
- compliance / audit
- replay mode
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base


class TradeEventType(str, Enum):
    # Position lifecycle
    POSITION_OPENED      = "POSITION_OPENED"
    POSITION_CLOSED      = "POSITION_CLOSED"
    POSITION_PARTIALLY_CLOSED = "POSITION_PARTIALLY_CLOSED"

    # Fill events
    FILL_RECEIVED        = "FILL_RECEIVED"
    PARTIAL_FILL         = "PARTIAL_FILL"

    # Risk level changes
    STOP_LOSS_SET        = "STOP_LOSS_SET"
    STOP_LOSS_MOVED      = "STOP_LOSS_MOVED"    # trailing update
    TAKE_PROFIT_SET      = "TAKE_PROFIT_SET"

    # Trigger events
    STOP_LOSS_HIT        = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT      = "TAKE_PROFIT_HIT"
    TRAILING_STOP_HIT    = "TRAILING_STOP_HIT"

    # PnL
    PNL_SNAPSHOT         = "PNL_SNAPSHOT"       # periodic snapshot

    # Operational
    MANUAL_CLOSE         = "MANUAL_CLOSE"
    EMERGENCY_CLOSE      = "EMERGENCY_CLOSE"
    RECONCILIATION_CLOSE = "RECONCILIATION_CLOSE"
    ERROR                = "ERROR"


class TradeEvent(Base):
    __tablename__ = "trade_events"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )

    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[TradeEventType] = mapped_column(
        SqlEnum(TradeEventType),
        nullable=False,
    )

    price_at_event: Mapped[float] = mapped_column(
        Float, nullable=False,
    )

    unrealized_pnl_at_event: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    realized_pnl_at_event: Mapped[float] = mapped_column(
        Float, default=0.0,
    )

    # Flexible metadata — stores whatever is
    # relevant to the specific event type.
    # E.g. for SL_MOVED: {"old_sl": 100, "new_sl": 102}
    event_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
    )

    # ── Relationships ─────────────────────────

    position: Mapped["Position"] = relationship(
        "Position", back_populates="events",
    )
