from app.logger import get_logger
from app.trading.ai_filter import (
    AIFilter,
)
from app.trading.executor import Executor
from app.trading.market_data import (
    MarketDataService,
)
from app.trading.portfolio import (
    Portfolio,
)
from app.trading.risk_manager import (
    RiskManager,
)
from app.trading.strategy_loader import (
    StrategyLoader,
)

logger = get_logger("mcp_tools")

market_service = MarketDataService()

risk_manager = RiskManager()

executor = Executor()

portfolio = Portfolio()

strategy_loader = StrategyLoader()

ai_filter = AIFilter()


def register_tools(mcp):

    @mcp.tool()
    async def get_market_data(
        symbol: str = "BTC/USDT",
    ):

        return (
            await market_service
            .get_market_snapshot(
                symbol
            )
        )

    @mcp.tool()
    async def list_strategies():

        strategy_loader.load_strategies()

        return (
            strategy_loader
            .list_strategies()
        )

    @mcp.tool()
    async def enable_strategy(
        strategy_name: str,
    ):

        strategy_loader.enable_strategy(
            strategy_name
        )

        return {
            "status": "enabled",
            "strategy": strategy_name,
        }

    @mcp.tool()
    async def disable_strategy(
        strategy_name: str,
    ):

        strategy_loader.disable_strategy(
            strategy_name
        )

        return {
            "status": "disabled",
            "strategy": strategy_name,
        }

    @mcp.tool()
    async def risk_status():

        return {
            "daily_drawdown": (
                risk_manager.daily_drawdown
            ),
            "open_positions": (
                risk_manager.open_positions
            ),
            "emergency_mode": (
                risk_manager.emergency_mode
            ),
        }

    @mcp.tool()
    async def emergency_stop():

        await (
            risk_manager
            .activate_emergency_stop()
        )

        return {
            "status": (
                "emergency_stop_activated"
            )
        }

    @mcp.tool()
    async def portfolio_status():

        return (
            portfolio.get_positions()
        )

    @mcp.tool()
    async def analyze_trade(
        symbol: str,
        signal: str,
        strategy_name: str,
    ):

        dataframe = (
            await market_service
            .get_market_dataframe(
                symbol=symbol,
            )
        )

        return (
            await ai_filter.confirm_trade(
                signal=signal,
                dataframe=dataframe,
                strategy_name=(
                    strategy_name
                ),
            )
        )

    @mcp.tool()
    async def execute_trade(
        symbol: str,
        signal: str,
        strategy_name: str,
    ):

        strategies = (
            strategy_loader
            .load_strategies()
        )

        strategy = strategies.get(
            strategy_name
        )

        if not strategy:

            return {
                "error": (
                    "strategy_not_found"
                )
            }

        approved = (
            await risk_manager
            .validate_trade(
                symbol=symbol,
                signal=signal,
                strategy=strategy,
            )
        )

        if not approved:

            return {
                "error": (
                    "trade_rejected"
                )
            }

        return (
            await executor.execute_trade(
                symbol=symbol,
                signal=signal,
                strategy=strategy,
            )
        )
