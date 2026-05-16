"""
app/api/copilot.py — Phase 6: AI Copilot REST endpoint.

POST /copilot/chat
  Body: { message: str, conversation_history: [...] }
  Returns: { response: str, actions_taken: [...], data: any }

Works in both ENABLE_TRADING=true and ENABLE_TRADING=false modes.
Read-only queries always work. Action commands gracefully fail when
lifecycle service is unavailable.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.api.positions import api_response
from app.logger import get_logger

logger = get_logger("copilot_api")

copilot_router = APIRouter(prefix="/copilot", tags=["copilot"])


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class ConversationMessage(BaseModel):
    role:    str   # "user" | "assistant"
    content: str


class CopilotChatRequest(BaseModel):
    message:              str
    conversation_history: list[ConversationMessage] = []


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@copilot_router.post("/chat")
async def copilot_chat(
    body:    CopilotChatRequest,
    request: Request,
):
    """
    Main copilot chat endpoint.
    Delegates all logic to CopilotService.
    """
    copilot = getattr(request.app.state, "copilot", None)
    if copilot is None:
        return api_response(
            data={
                "response":      "Copilot service not available.",
                "actions_taken": [],
                "data":          None,
            }
        )

    # Pull live services from app.state (may be None if trading disabled)
    lifecycle    = getattr(request.app.state, "lifecycle",              None)
    trading_bot  = getattr(request.app.state, "trading_bot",            None)
    analytics    = getattr(request.app.state, "analytics",              None)
    strategy_svc = getattr(request.app.state, "strategy_config_service", None)

    result = await copilot.chat(
        message=body.message,
        conversation_history=[m.model_dump() for m in body.conversation_history],
        lifecycle=lifecycle,
        trading_bot=trading_bot,
        analytics=analytics,
        strategy_svc=strategy_svc,
    )

    logger.info(
        "copilot_chat",
        actions=len(result.get("actions_taken", [])),
    )

    return api_response(data=result)
