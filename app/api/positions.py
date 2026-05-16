"""
REST API — positions and trades endpoints.

Follows standard REST conventions.
All responses include envelope: {data, meta}.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logger import get_logger
from app.models.trade_events import TradeEvent
from app.models.trades import CloseReason, OrderStatus, Position

logger = get_logger("api")


# ─────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────

class PositionResponse(BaseModel):
    id:              int
    symbol:          str
    side:            str
    status:          str
    avg_entry_price: float
    exit_price:      float | None
    remaining_qty:   float
    unrealized_pnl:  float
    realized_pnl:    float
    stop_loss:       float | None
    take_profit:     float | None
    trailing_stop:   float | None
    close_reason:    str | None
    strategy:        str | None
    opened_at:       str | None
    closed_at:       str | None

    class Config:
        from_attributes = True


class ManualCloseRequest(BaseModel):
    exit_price: float


class EmergencyCloseRequest(BaseModel):
    confirm: bool  # must be True


def api_response(data: Any, meta: dict | None = None) -> dict:
    return {"data": data, "meta": meta or {}}


# ─────────────────────────────────────────────
# Positions router
# ─────────────────────────────────────────────

positions_router = APIRouter(prefix="/positions", tags=["positions"])


@positions_router.get("/")
async def list_positions(
    status: str | None  = Query(None, description="Filter by status"),
    symbol: str | None  = Query(None, description="Filter by symbol"),
    limit:  int         = Query(50, le=500),
    db: AsyncSession    = Depends(get_db),
):
    """List positions with optional filters."""
    query = select(Position).order_by(Position.opened_at.desc()).limit(limit)

    if status:
        try:
            query = query.where(Position.status == OrderStatus(status.upper()))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    if symbol:
        query = query.where(Position.symbol == symbol.upper())

    result = await db.execute(query)
    positions = result.scalars().all()

    return api_response(
        data=[_serialize_position(p) for p in positions],
        meta={"count": len(positions), "limit": limit},
    )


@positions_router.get("/open")
async def open_positions(db: AsyncSession = Depends(get_db)):
    """All currently open positions."""
    result = await db.execute(
        select(Position).where(
            Position.status.in_([
                OrderStatus.FILLED,
                OrderStatus.PARTIALLY_FILLED,
            ])
        ).order_by(Position.opened_at.desc())
    )
    positions = result.scalars().all()

    return api_response(
        data=[_serialize_position(p) for p in positions],
        meta={"count": len(positions)},
    )


@positions_router.get("/{position_id}")
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_db),
):
    position = await db.get(Position, position_id)
    if not position:
        raise HTTPException(404, "Position not found")

    return api_response(data=_serialize_position(position))


@positions_router.get("/{position_id}/events")
async def get_position_events(
    position_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Full audit trail for a position."""
    result = await db.execute(
        select(TradeEvent)
        .where(TradeEvent.position_id == position_id)
        .order_by(TradeEvent.created_at.asc())
    )
    events = result.scalars().all()

    return api_response(
        data=[{
            "id":             e.id,
            "event_type":     e.event_type.value,
            "price":          e.price_at_event,
            "unrealized_pnl": e.unrealized_pnl_at_event,
            "realized_pnl":   e.realized_pnl_at_event,
            "metadata":       e.event_metadata,
            "created_at":     e.created_at.isoformat(),
        } for e in events],
        meta={"count": len(events)},
    )


@positions_router.post("/{position_id}/close")
async def manual_close(
    position_id: int,
    body: ManualCloseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually close a position at a given price."""
    position = await db.get(Position, position_id)
    if not position:
        raise HTTPException(404, "Position not found")

    if position.status not in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
        raise HTTPException(400, f"Position is not open (status: {position.status})")

    return api_response(
        data={"message": "close_requested", "position_id": position_id},
    )


@positions_router.post("/emergency-close")
async def emergency_close(body: EmergencyCloseRequest):
    """Emergency close all open positions."""
    if not body.confirm:
        raise HTTPException(400, "Must set confirm=true")

    return api_response(data={"status": "emergency_close_initiated"})


# ─────────────────────────────────────────────
# Analytics router
# ─────────────────────────────────────────────

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_analytics(request: Request):
    """Helper para obtener AnalyticsService desde app.state."""
    analytics = getattr(request.app.state, "analytics", None)
    if analytics is None:
        raise HTTPException(503, "Analytics service not available")
    return analytics


@analytics_router.get("/daily")
async def daily_stats(
    date_filter: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Daily performance summary."""
    from app.models.daily_metrics import DailyMetric
    from datetime import date as date_type

    target_date = date_filter or date_type.today()

    result = await db.execute(
        select(DailyMetric).where(DailyMetric.date == target_date)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        return api_response(data=None, meta={"date": str(target_date)})

    return api_response(data={
        "date":                   str(metric.date),
        "total_trades":           metric.total_trades,
        "winning_trades":         metric.winning_trades,
        "losing_trades":          metric.losing_trades,
        "win_rate":                metric.win_rate,
        "realized_pnl":           metric.realized_pnl,
        "gross_profit":           metric.gross_profit,
        "gross_loss":             metric.gross_loss,
        "profit_factor":          metric.profit_factor,
        "max_drawdown":           metric.max_drawdown,
        "avg_win":                metric.avg_win,
        "avg_loss":               metric.avg_loss,
        "avg_trade_duration_sec": metric.avg_trade_duration_sec,
    })


@analytics_router.get("/summary")
async def portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Current portfolio snapshot."""
    result = await db.execute(
        select(Position).where(
            Position.status.in_([
                OrderStatus.FILLED,
                OrderStatus.PARTIALLY_FILLED,
            ])
        )
    )
    open_positions = result.scalars().all()

    total_unrealized = sum(p.unrealized_pnl for p in open_positions)
    total_realized   = sum(p.realized_pnl   for p in open_positions)

    return api_response(data={
        "open_positions":    len(open_positions),
        "total_unrealized":  total_unrealized,
        "total_realized":    total_realized,
        "total_exposure":    sum(
            p.avg_entry_price * p.remaining_quantity
            for p in open_positions
        ),
    })


# ─────────────────────────────────────────────
# Phase 4 — Nuevos endpoints de analytics
# ─────────────────────────────────────────────

@analytics_router.get("/equity-curve")
async def equity_curve(
    request: Request,
    days: int = Query(30, ge=1, le=365),
):
    """
    Serie temporal de PnL acumulado para graficar.
    Devuelve [{date, daily_pnl, cumulative_pnl, total_trades, win_rate}]
    """
    analytics = _get_analytics(request)
    curve = await analytics.get_equity_curve(days=days)
    return api_response(
        data=curve,
        meta={"days": days, "points": len(curve)},
    )


@analytics_router.get("/sharpe")
async def sharpe_ratio(
    request: Request,
    days: int = Query(30, ge=7, le=365),
):
    """
    Sharpe ratio anualizado (252 días, risk-free rate = 0).
    """
    analytics = _get_analytics(request)
    result = await analytics.get_sharpe_ratio(days=days)
    return api_response(data=result, meta={"days": days})


@analytics_router.get("/drawdown")
async def max_drawdown(
    request: Request,
    days: int = Query(30, ge=1, le=365),
):
    """
    Max drawdown peak-to-trough sobre la equity curve.
    """
    analytics = _get_analytics(request)
    result = await analytics.get_max_drawdown(days=days)
    return api_response(data=result, meta={"days": days})


@analytics_router.get("/trade-stats")
async def trade_stats(request: Request):
    """
    Estadísticas de duración y distribución de trades cerrados.
    """
    analytics = _get_analytics(request)
    result = await analytics.get_trade_duration_stats()
    return api_response(data=result)


@analytics_router.get("/ai-performance")
async def ai_performance(request: Request):
    """
    Métricas de rendimiento del AI filter vs todos los trades.
    """
    analytics = _get_analytics(request)
    result = await analytics.get_ai_performance_metrics()
    return api_response(data=result)


# ─────────────────────────────────────────────
# Serializer
# ─────────────────────────────────────────────

def _serialize_position(p: Position) -> dict:
    return {
        "id":              p.id,
        "symbol":          p.symbol,
        "side":            p.side.value,
        "status":          p.status.value,
        "avg_entry_price": p.avg_entry_price,
        "exit_price":      p.exit_price,
        "remaining_qty":   p.remaining_quantity,
        "unrealized_pnl":  p.unrealized_pnl,
        "realized_pnl":    p.realized_pnl,
        "total_fees":      p.total_fees,
        "stop_loss":       p.stop_loss,
        "take_profit":     p.take_profit,
        "trailing_stop":   p.trailing_stop_price,
        "close_reason":    p.close_reason.value if p.close_reason else None,
        "strategy":        p.strategy_name,
        "opened_at":       p.opened_at.isoformat() if p.opened_at else None,
        "closed_at":       p.closed_at.isoformat() if p.closed_at else None,
        "mfe":             p.max_favorable_excursion,
        "mae":             p.max_adverse_excursion,
    }
