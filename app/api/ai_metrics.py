"""
app/api/ai_metrics.py — Phase 7: AI filter metrics endpoint.

GET  /ai-metrics          → session token usage + call stats
POST /ai-metrics/reset    → reset session counters
"""

from fastapi import APIRouter

from app.api.positions import api_response
from app.trading.ai_token_tracker import ai_token_tracker

ai_metrics_router = APIRouter(prefix="/ai-metrics", tags=["ai-metrics"])


@ai_metrics_router.get("/")
async def get_ai_metrics():
    """Current session AI filter usage stats."""
    return api_response(data=ai_token_tracker.to_dict())


@ai_metrics_router.post("/reset")
async def reset_ai_metrics():
    """Reset session counters."""
    ai_token_tracker.reset()
    return api_response(data={"reset": True})
