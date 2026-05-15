from app.logger import get_logger

logger = get_logger("strategy_engine")


class StrategyEngine:

    def __init__(
        self,
        strategy_loader,
        ai_filter,
        risk_manager,
        executor,
    ):

        self.strategy_loader = strategy_loader

        self.ai_filter = ai_filter

        self.risk_manager = risk_manager

        self.executor = executor

    async def process_market_data(
        self,
        dataframe,
        symbol: str,
    ):

        strategies = (
            self.strategy_loader
            .load_strategies()
        )

        for strategy_name, strategy in (
            strategies.items()
        ):

            if not strategy.enabled:
                continue

            logger.info(
                "running_strategy",
                strategy=strategy_name,
            )

            signal = (
                await strategy.generate_signal(
                    dataframe
                )
            )

            logger.info(
                "strategy_signal_generated",
                strategy=strategy_name,
                signal=signal,
            )

            if signal == "HOLD":
                continue

            ai_confirmation = (
                await self.ai_filter.confirm_trade(
                    signal=signal,
                    dataframe=dataframe,
                    strategy_name=strategy_name,
                )
            )

            logger.info(
                "ai_confirmation_received",
                strategy=strategy_name,
                ai_confirmation=ai_confirmation,
            )

            if ai_confirmation == "HOLD":
                continue

            approved = (
                await self.risk_manager
                .validate_trade(
                    symbol=symbol,
                    signal=signal,
                    strategy=strategy,
                )
            )

            if not approved:

                logger.warning(
                    "trade_rejected_by_risk_manager",
                    strategy=strategy_name,
                )

                continue

            await self.executor.execute_trade(
                symbol=symbol,
                signal=signal,
                strategy=strategy,
            )
