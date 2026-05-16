import asyncio

from openai import OpenAI

from app.config import settings
from app.logger import get_logger
from app.utils.retries import async_retry

logger = get_logger("deepseek_service")


class NvidiaService:

    VALID_RESPONSES = ["BUY", "SELL", "HOLD"]

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30.0,
        )

    @async_retry()
    async def analyze_trade(self, prompt: str) -> str:

        logger.info("sending_prompt_to_ai")

        try:
            final_prompt = f"""
You are a trading validator.

You MUST answer with ONLY ONE WORD.

Allowed responses:
BUY
SELL
HOLD

Do not explain.
Do not use markdown.
Do not add punctuation.
Do not add reasoning.

Trade setup:
{prompt}
"""

            logger.info(
                "ai_request_details",
                model=settings.DEEPSEEK_MODEL,
                base_url=settings.DEEPSEEK_BASE_URL,
            )

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict trading validator.",
                    },
                    {
                        "role": "user",
                        "content": final_prompt,
                    },
                ],
                temperature=0,
                top_p=0.1,
                max_tokens=20,
            )

            # Log exactly what model the API actually used
            actual_model = getattr(response, "model", "unknown")
            usage = getattr(response, "usage", None)

            logger.info(
                "ai_response_received",
                requested_model=settings.DEEPSEEK_MODEL,
                actual_model=actual_model,
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
            )

            message = response.choices[0].message
            raw_content = getattr(message, "content", None)

            if not raw_content:
                logger.warning("empty_ai_response")
                return "HOLD"

            content = str(raw_content).strip().upper()

            if content not in self.VALID_RESPONSES:
                logger.warning("invalid_ai_response", response=content)
                return "HOLD"

            logger.info("ai_response_validated", response=content)
            return content

        except Exception as e:
            logger.error("ai_request_failed", error=str(e))
            return "HOLD"
