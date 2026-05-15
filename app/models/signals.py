from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database import Base


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalSource(str, Enum):
    STRATEGY = "STRATEGY"
    AI_FILTER = "AI_FILTER"
    MANUAL = "MANUAL"


class Signal(Base):
    __tablename__ = "signals"

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

    strategy_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    signal: Mapped[SignalType] = mapped_column(
        SqlEnum(SignalType),
        nullable=False,
    )

    source: Mapped[SignalSource] = mapped_column(
        SqlEnum(SignalSource),
        default=SignalSource.STRATEGY,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    indicators: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ai_reasoning: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
