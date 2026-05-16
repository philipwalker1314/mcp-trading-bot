"""
StrategyConfig — runtime strategy stored in DB as JSON config.

Phase 7 additions:
  ai_validation_required  — if False, skip AI entirely for this strategy
  confidence_threshold    — signal strength above this → skip AI (0.0–1.0)
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

    symbols: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # ── Risk ──────────────────────────────────

    stop_loss_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.02)

    take_profit_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.04)

    trailing_stop_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Signal logic ──────────────────────────

    entry_rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    exit_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)

    indicators: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # ── Phase 7: Selective AI Filter ──────────
    # ai_validation_required=False  → skip AI for all signals from this strategy
    # confidence_threshold          → skip AI when signal_strength >= threshold
    #                                 0.75 = only call AI for weak/uncertain signals

    ai_validation_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    confidence_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.75
    )

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
            "id":                       self.id,
            "name":                     self.name,
            "description":              self.description,
            "version":                  self.version,
            "enabled":                  self.enabled,
            "timeframe":                self.timeframe,
            "symbols":                  self.symbols,
            "stop_loss_pct":            self.stop_loss_pct,
            "take_profit_pct":          self.take_profit_pct,
            "trailing_stop_pct":        self.trailing_stop_pct,
            "entry_rules":              self.entry_rules,
            "exit_rules":               self.exit_rules,
            "indicators":               self.indicators,
            "ai_validation_required":   self.ai_validation_required,
            "confidence_threshold":     self.confidence_threshold,
            "created_at":               self.created_at.isoformat() if self.created_at else None,
            "updated_at":               self.updated_at.isoformat() if self.updated_at else None,
            "created_by":               self.created_by,
        }

    def to_snapshot(self) -> dict:
        """Full config snapshot for version history."""
        return self.to_dict()


class StrategyVersion(Base):
    """Immutable append-only version history for strategy configs."""
    __tablename__ = "strategy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    strategy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False)

    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    strategy: Mapped["StrategyConfig"] = relationship(
        "StrategyConfig",
        back_populates="versions",
    )
