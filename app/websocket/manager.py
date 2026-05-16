"""
WebSocket layer — realtime push to frontend.

Architecture:
  EventBus → ws_handlers → ConnectionManager → clients

ConnectionManager is a singleton.
Multiple endpoints share it.

Endpoints:
  /ws/positions  → position updates, PnL, SL/TP triggers
  /ws/market     → price ticks for subscribed symbols
  /ws/system     → system events (emergency stop, errors)
"""

import asyncio
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.events.event_bus import EventBus, Events
from app.logger import get_logger
from app.trading.lifecycle.trade_lifecycle_service import TradeLifecycleService

logger = get_logger("websocket")


# ─────────────────────────────────────────────
# Connection Manager
# ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, channel: str):
        await ws.accept()
        self._connections[channel].add(ws)
        logger.info("ws_client_connected", channel=channel, total=len(self._connections[channel]))

    def disconnect(self, ws: WebSocket, channel: str):
        self._connections[channel].discard(ws)
        logger.info("ws_client_disconnected", channel=channel, total=len(self._connections[channel]))

    async def broadcast(self, channel: str, data: dict):
        dead = []
        for ws in list(self._connections.get(channel, [])):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append((ws, channel))
        for ws, ch in dead:
            self.disconnect(ws, ch)

    async def broadcast_all(self, data: dict):
        for channel in list(self._connections.keys()):
            await self.broadcast(channel, data)

    def active_count(self, channel: str = None) -> int:
        if channel:
            return len(self._connections.get(channel, []))
        return sum(len(s) for s in self._connections.values())


ws_manager = ConnectionManager()


# ─────────────────────────────────────────────
# Event → WebSocket bridge
# ─────────────────────────────────────────────

async def on_position_opened(event):
    await ws_manager.broadcast("positions", {"event": "position.opened", "payload": event.payload})

async def on_position_closed(event):
    await ws_manager.broadcast("positions", {"event": "position.closed", "payload": event.payload})

async def on_position_updated(event):
    await ws_manager.broadcast("positions", {"event": "position.updated", "payload": event.payload})

async def on_market_tick(event):
    await ws_manager.broadcast("market", {"event": "market.tick", "payload": event.payload})

async def on_stop_loss_hit(event):
    await ws_manager.broadcast("positions", {"event": "position.stop_loss_hit", "payload": event.payload})
    await ws_manager.broadcast("system",    {"event": "position.stop_loss_hit", "payload": event.payload})

async def on_take_profit_hit(event):
    await ws_manager.broadcast("positions", {"event": "position.take_profit_hit", "payload": event.payload})

async def on_emergency_stop(event):
    await ws_manager.broadcast_all({"event": "risk.emergency_stop", "payload": event.payload})


def register_ws_handlers(event_bus: EventBus):
    event_bus.subscribe(Events.POSITION_OPENED,  on_position_opened)
    event_bus.subscribe(Events.POSITION_CLOSED,  on_position_closed)
    event_bus.subscribe(Events.POSITION_UPDATED, on_position_updated)
    event_bus.subscribe(Events.MARKET_TICK,       on_market_tick)
    event_bus.subscribe(Events.STOP_LOSS_HIT,     on_stop_loss_hit)
    event_bus.subscribe(Events.TAKE_PROFIT_HIT,   on_take_profit_hit)
    event_bus.subscribe(Events.EMERGENCY_STOP,    on_emergency_stop)
    logger.info("ws_handlers_registered")


# ─────────────────────────────────────────────
# FastAPI WebSocket Router
# ─────────────────────────────────────────────

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/positions")
async def positions_ws(websocket: WebSocket):
    await ws_manager.connect(websocket, "positions")
    try:
        lifecycle: TradeLifecycleService | None = getattr(
            websocket.app.state, "lifecycle", None
        )
        if lifecycle:
            try:
                positions = await lifecycle.get_open_positions()
                await websocket.send_json({
                    "event": "snapshot",
                    "payload": [TradeLifecycleService._position_to_dict(p) for p in positions],
                })
            except Exception as e:
                logger.error("ws_snapshot_error", error=str(e))
                await websocket.send_json({"event": "snapshot", "payload": []})
        else:
            await websocket.send_json({"event": "snapshot", "payload": []})

        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"event": "ping"})
            except Exception:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("ws_positions_error", error=str(e))
    finally:
        ws_manager.disconnect(websocket, "positions")


@router.websocket("/ws/market")
async def market_ws(websocket: WebSocket):
    await ws_manager.connect(websocket, "market")
    try:
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"event": "ping"})
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("ws_market_error", error=str(e))
    finally:
        ws_manager.disconnect(websocket, "market")


@router.websocket("/ws/system")
async def system_ws(websocket: WebSocket):
    await ws_manager.connect(websocket, "system")
    try:
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"event": "ping"})
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("ws_system_error", error=str(e))
    finally:
        ws_manager.disconnect(websocket, "system")
