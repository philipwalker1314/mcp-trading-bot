"""
Strategy Config REST API — Phase 5.

Endpoints:
  GET    /strategies/               list all configs
  POST   /strategies/               create new config
  GET    /strategies/{id}           get single config
  PUT    /strategies/{id}           update config (bumps version)
  DELETE /strategies/{id}           delete config
  POST   /strategies/{id}/enable    enable strategy (hot-swap)
  POST   /strategies/{id}/disable   disable strategy (hot-swap)
  POST   /strategies/{id}/rollback  rollback to a previous version
  GET    /strategies/{id}/versions  version history
  POST   /strategies/validate       dry-run validate without saving

All responses follow the existing {data, meta} envelope.
All errors follow FastAPI HTTPException with detail string.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.positions import api_response
from app.database import get_db
from app.logger import get_logger
from app.trading.strategy_compiler import StrategyCompileError

logger = get_logger("strategy_api")

strategies_router = APIRouter(prefix="/strategies", tags=["strategies"])


# ─────────────────────────────────────────────
# Helper — get service from app.state
# ─────────────────────────────────────────────

def _get_service(request: Request):
    svc = getattr(request.app.state, "strategy_config_service", None)
    if svc is None:
        raise HTTPException(503, "Strategy config service not available")
    return svc


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class RuleSchema(BaseModel):
    indicator:  str
    op:         str
    target:     str | None = None
    value:      float | None = None
    value_min:  float | None = None
    value_max:  float | None = None


class IndicatorSchema(BaseModel):
    type:    str
    period:  int | None = None
    column:  str | None = None
    fast:    int | None = None
    slow:    int | None = None
    signal:  int | None = None
    std:     float | None = None
    k:       int | None = None
    d:       int | None = None


class StrategyCreateSchema(BaseModel):
    name:               str
    description:        str | None = None
    timeframe:          str = "1m"
    symbols:            list[str]
    stop_loss_pct:      float = 0.02
    take_profit_pct:    float = 0.04
    trailing_stop_pct:  float | None = None
    indicators:         list[dict]
    entry_rules:        list[dict]
    exit_rules:         list[dict] | None = None
    enabled:            bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("symbols")
    @classmethod
    def symbols_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("symbols must have at least one entry")
        return v

    @field_validator("entry_rules")
    @classmethod
    def rules_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("entry_rules must have at least one rule")
        return v


class StrategyUpdateSchema(BaseModel):
    name:               str | None = None
    description:        str | None = None
    timeframe:          str | None = None
    symbols:            list[str] | None = None
    stop_loss_pct:      float | None = None
    take_profit_pct:    float | None = None
    trailing_stop_pct:  float | None = None
    indicators:         list[dict] | None = None
    entry_rules:        list[dict] | None = None
    exit_rules:         list[dict] | None = None
    change_summary:     str | None = None


class RollbackSchema(BaseModel):
    target_version: int


class ValidateSchema(BaseModel):
    name:           str = "preview"
    timeframe:      str = "1m"
    symbols:        list[str] = ["BTC/USDT"]
    stop_loss_pct:  float = 0.02
    take_profit_pct: float = 0.04
    indicators:     list[dict] = []
    entry_rules:    list[dict] = []
    exit_rules:     list[dict] | None = None


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@strategies_router.get("/")
async def list_strategies(
    request: Request,
    enabled_only: bool = Query(False),
):
    """List all strategy configs."""
    svc = _get_service(request)
    configs = await svc.list_all(enabled_only=enabled_only)
    return api_response(
        data=[c.to_dict() for c in configs],
        meta={"count": len(configs), "enabled_only": enabled_only},
    )


@strategies_router.post("/")
async def create_strategy(
    request: Request,
    body: StrategyCreateSchema,
):
    """Create a new strategy config."""
    svc = _get_service(request)
    try:
        config = await svc.create(body.model_dump(exclude_none=False))
    except StrategyCompileError as e:
        raise HTTPException(422, detail=str(e))
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(409, f"Strategy name {body.name!r} already exists")
        raise HTTPException(500, str(e))

    return api_response(data=config.to_dict(), meta={"created": True})


@strategies_router.get("/{strategy_id}")
async def get_strategy(
    request: Request,
    strategy_id: int,
):
    svc    = _get_service(request)
    config = await svc.get(strategy_id)
    if not config:
        raise HTTPException(404, f"Strategy {strategy_id} not found")
    return api_response(data=config.to_dict())


@strategies_router.put("/{strategy_id}")
async def update_strategy(
    request: Request,
    strategy_id: int,
    body: StrategyUpdateSchema,
):
    """Update a strategy config. Bumps version, writes history snapshot."""
    svc = _get_service(request)
    update_data = body.model_dump(exclude_none=True)
    change_summary = update_data.pop("change_summary", None)

    if not update_data:
        raise HTTPException(400, "No fields to update")

    try:
        config = await svc.update(strategy_id, update_data, change_summary)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except StrategyCompileError as e:
        raise HTTPException(422, detail=str(e))

    return api_response(data=config.to_dict(), meta={"updated": True, "version": config.version})


@strategies_router.delete("/{strategy_id}")
async def delete_strategy(
    request: Request,
    strategy_id: int,
):
    svc     = _get_service(request)
    deleted = await svc.delete(strategy_id)
    if not deleted:
        raise HTTPException(404, f"Strategy {strategy_id} not found")
    return api_response(data={"deleted": True, "id": strategy_id})


@strategies_router.post("/{strategy_id}/enable")
async def enable_strategy(
    request: Request,
    strategy_id: int,
):
    """Enable a strategy for live trading (hot-swap, no restart needed)."""
    svc = _get_service(request)
    try:
        config = await svc.set_enabled(strategy_id, True)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return api_response(data=config.to_dict(), meta={"enabled": True})


@strategies_router.post("/{strategy_id}/disable")
async def disable_strategy(
    request: Request,
    strategy_id: int,
):
    """Disable a strategy (hot-swap, no restart needed)."""
    svc = _get_service(request)
    try:
        config = await svc.set_enabled(strategy_id, False)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return api_response(data=config.to_dict(), meta={"enabled": False})


@strategies_router.post("/{strategy_id}/rollback")
async def rollback_strategy(
    request: Request,
    strategy_id: int,
    body: RollbackSchema,
):
    """Rollback to a previous version snapshot."""
    svc = _get_service(request)
    try:
        config = await svc.rollback(strategy_id, body.target_version)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except StrategyCompileError as e:
        raise HTTPException(422, str(e))
    return api_response(
        data=config.to_dict(),
        meta={"rolled_back_to": body.target_version, "new_version": config.version},
    )


@strategies_router.get("/{strategy_id}/versions")
async def get_versions(
    request: Request,
    strategy_id: int,
):
    """Full version history for a strategy."""
    svc     = _get_service(request)
    config  = await svc.get(strategy_id)
    if not config:
        raise HTTPException(404, f"Strategy {strategy_id} not found")
    versions = await svc.get_versions(strategy_id)
    return api_response(
        data=[{
            "id":             v.id,
            "strategy_id":    v.strategy_id,
            "version":        v.version,
            "change_summary": v.change_summary,
            "created_at":     v.created_at.isoformat() if v.created_at else None,
            "snapshot":       v.snapshot,
        } for v in versions],
        meta={"count": len(versions)},
    )


@strategies_router.post("/validate")
async def validate_strategy(
    request: Request,
    body: ValidateSchema,
):
    """
    Dry-run validate a strategy config without saving.
    Returns {valid: bool, errors: list[str]}.
    """
    svc    = _get_service(request)
    result = svc.test_compile(body.model_dump())
    return api_response(data=result)
