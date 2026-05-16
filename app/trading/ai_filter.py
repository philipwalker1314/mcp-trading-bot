from app.config import settings
from app.logger import get_logger
from app.services.nvidia_service import NvidiaService

logger = get_logger("ai_filter")


class AIFilter:

    def __init__(self):
        self.nvidia_service = NvidiaService()

    async def confirm_trade(
        self,
        signal: str,
        dataframe,
        strategy_name: str,
    ) -> str:

        # Mock mode — bypass AI entirely, echo the signal back
        if not settings.AI_TRADING_ENABLED:
            logger.info(
                "ai_mock_mode_signal_echoed",
                signal=signal,
                strategy=strategy_name,
            )
            return signal

        latest = dataframe.iloc[-1]

        prompt = f"""
        Trading Signal Analysis

        Strategy: {strategy_name}
        Signal: {signal}
        Price: {latest['close']}
        RSI: {latest.get('rsi', 'N/A')}
        MACD: {latest.get('macd', 'N/A')}
        ATR: {latest.get('atr', 'N/A')}
        Volatility: {latest.get('volatility', 'N/A')}

        Respond ONLY with: BUY, SELL, or HOLD
        """

        logger.info(
            "sending_trade_for_ai_analysis",
            strategy=strategy_name,
        )

        response = await self.nvidia_service.analyze_trade(prompt)

        logger.info(
            "ai_trade_analysis_complete",
            response=response,
        )

        return response
