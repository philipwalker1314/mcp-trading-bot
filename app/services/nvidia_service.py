import asyncio

from openai import OpenAI

from app.config import settings
from app.logger import get_logger
from app.utils.retries import async_retry

logger = get_logger("nvidia_service")


class NvidiaService:

    VALID_RESPONSES = [
        "BUY",
        "SELL",
        "HOLD",
    ]

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
        )

    @async_retry()
    async def analyze_trade(
        self,
        prompt: str,
    ) -> str:

        logger.info("sending_prompt_to_nvidia")

        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=settings.NVIDIA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional "
                        "trading risk analyst. "
                        "You NEVER execute trades. "
                        "Only answer BUY, SELL or HOLD."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=10,
        )

        content = (
            response
            .choices[0]
            .message.content
            .strip()
            .upper()
        )

        logger.info(
            "nvidia_response_received",
            response=content,
        )

        if content not in self.VALID_RESPONSES:

            logger.warning(
                "invalid_ai_response",
                response=content,
            )

            return "HOLD"

        return content
