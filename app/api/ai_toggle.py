"""
app/api/ai_toggle.py — Toggle AI trading on/off at runtime.

POST /ai-trading/toggle   → flip AI_TRADING_ENABLED in memory
GET  /ai-trading/status   → current state

No restart needed. The AIFilter reads settings.AI_TRADING_ENABLED
on every call, so this takes effect immediately on the next signal.
"""

from fastapi import APIRouter

from app.api.positions import api_response
from app.config import settings
from app.logger import get_logger

logger = get_logger("ai_toggle")

ai_toggle_router = APIRouter(prefix="/ai-trading", tags=["ai-trading"])


@ai_toggle_router.get("/status")
async def get_ai_status():
    return api_response(data={
        "ai_trading_enabled": settings.AI_TRADING_ENABLED,
        "mode": "LIVE_AI" if settings.AI_TRADING_ENABLED else "MOCK (signal echoed)",
    })


@ai_toggle_router.post("/toggle")
async def toggle_ai_trading():
    settings.AI_TRADING_ENABLED = not settings.AI_TRADING_ENABLED
    state = settings.AI_TRADING_ENABLED

    logger.warning(
        "ai_trading_toggled",
        enabled=state,
    )

    return api_response(data={
        "ai_trading_enabled": state,
        "mode": "LIVE_AI" if state else "MOCK (signal echoed)",
        "message": f"AI trading {'enabled' if state else 'disabled'} — takes effect on next signal",
    })


@ai_toggle_router.post("/enable")
async def enable_ai():
    settings.AI_TRADING_ENABLED = True
    logger.warning("ai_trading_enabled_via_api")
    return api_response(data={"ai_trading_enabled": True})


@ai_toggle_router.post("/disable")
async def disable_ai():
    settings.AI_TRADING_ENABLED = False
    logger.warning("ai_trading_disabled_via_api")
    return api_response(data={"ai_trading_enabled": False})
