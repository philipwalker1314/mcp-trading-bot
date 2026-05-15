from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    metric_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    symbol: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    strategy_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
