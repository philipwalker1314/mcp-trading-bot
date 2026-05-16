"""
StrategyConfig — runtime strategy stored in DB as JSON config.

Design decisions:
- entry_rules / exit_rules are a list of Rule dicts evaluated by the compiler
- indicators is a list of IndicatorConfig dicts passed to the indicator engine
- version is bumped on every save; old snapshots kept in strategy_versions
- enabled=False by default — must be explicitly activated
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    __table_args__ = (
        UniqueConstraint("name", name="uq_strategy_configs_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Execution ─────────────────────────────

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, default="1m")

    # e.g. ["BTC/USDT"] or ["BTC/USDT", "ETH/USDT"]
    symbols: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # ── Risk ──────────────────────────────────

    stop_loss_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.02)

    take_profit_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.04)

    trailing_stop_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Signal logic ──────────────────────────
    # entry_rules example:
    # [
    #   {"indicator": "ema_8", "op": "crosses_above", "target": "ema_13"},
    #   {"indicator": "rsi",   "op": "between",       "value_min": 40, "value_max": 65}
    # ]
    #
    # Supported ops: gt, lt, gte, lte, eq, between, crosses_above, crosses_below
    # All rules in the list are AND-ed together.
    # For OR logic, use separate strategies.

    entry_rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    exit_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── Indicators ────────────────────────────
    # [
    #   {"type": "ema", "period": 8,  "column": "ema_8"},
    #   {"type": "ema", "period": 13, "column": "ema_13"},
    #   {"type": "rsi", "period": 14, "column": "rsi"},
    #   {"type": "macd"},
    #   {"type": "atr",  "period": 14},
    #   {"type": "volatility", "period": 20}
    # ]

    indicators: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # ── Audit ─────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # ── Relationships ─────────────────────────

    versions: Mapped[list["StrategyVersion"]] = relationship(
        "StrategyVersion",
        back_populates="strategy",
        order_by="StrategyVersion.version.desc()",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "name":              self.name,
            "description":       self.description,
            "version":           self.version,
            "enabled":           self.enabled,
            "timeframe":         self.timeframe,
            "symbols":           self.symbols,
            "stop_loss_pct":     self.stop_loss_pct,
            "take_profit_pct":   self.take_profit_pct,
            "trailing_stop_pct": self.trailing_stop_pct,
            "entry_rules":       self.entry_rules,
            "exit_rules":        self.exit_rules,
            "indicators":        self.indicators,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
            "updated_at":        self.updated_at.isoformat() if self.updated_at else None,
            "created_by":        self.created_by,
        }

    def to_snapshot(self) -> dict:
        """Full config snapshot for version history."""
        return self.to_dict()


class StrategyVersion(Base):
    """Immutable append-only version history for strategy configs."""
    __tablename__ = "strategy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # FIX: ForeignKey declarado correctamente para que SQLAlchemy
    # resuelva el relationship con StrategyConfig sin ambigüedad.
    strategy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Full config snapshot at this version
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Relationship ──────────────────────────

    strategy: Mapped["StrategyConfig"] = relationship(
        "StrategyConfig",
        back_populates="versions",
    )
