from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database import Base


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    side: Mapped[TradeSide] = mapped_column(
        SqlEnum(TradeSide),
        nullable=False,
    )

    status: Mapped[TradeStatus] = mapped_column(
        SqlEnum(TradeStatus),
        default=TradeStatus.OPEN,
        nullable=False,
    )

    entry_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    exit_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    stop_loss: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    take_profit: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    pnl: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    fees: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    strategy_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    exchange_order_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
