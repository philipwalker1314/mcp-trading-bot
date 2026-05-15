import importlib
import pathlib
import sys

from app.logger import get_logger

logger = get_logger("strategy_loader")


class StrategyLoader:

    def __init__(self):

        self.strategies = {}

        self.strategy_path = pathlib.Path(
            "strategies/custom"
        )

    def load_strategies(self):

        logger.info("loading_strategies")

        self.strategies.clear()

        strategy_files = self.strategy_path.glob("*.py")

        for file in strategy_files:

            if file.name.startswith("_"):
                continue

            module_name = (
                f"strategies.custom.{file.stem}"
            )

            try:

                if module_name in sys.modules:
                    module = importlib.reload(
                        sys.modules[module_name]
                    )
                else:
                    module = importlib.import_module(
                        module_name
                    )

                for attribute_name in dir(module):

                    attribute = getattr(
                        module,
                        attribute_name,
                    )

                    if (
    isinstance(attribute, type)
    and hasattr(
        attribute,
        "generate_signal",
    )
    and attribute.__name__
    != "BaseStrategy"
):

                        strategy = attribute()

                        self.strategies[
                            strategy.name
                        ] = strategy

                        logger.info(
                            "strategy_loaded",
                            strategy=strategy.name,
                        )

            except Exception as error:

                logger.error(
                    "strategy_load_error",
                    file=file.name,
                    error=str(error),
                )

        return self.strategies

    def get_strategy(
        self,
        strategy_name: str,
    ):

        return self.strategies.get(strategy_name)

    def enable_strategy(
        self,
        strategy_name: str,
    ):

        strategy = self.get_strategy(
            strategy_name
        )

        if strategy:
            strategy.enabled = True

    def disable_strategy(
        self,
        strategy_name: str,
    ):

        strategy = self.get_strategy(
            strategy_name
        )

        if strategy:
            strategy.enabled = False

    def list_strategies(self):

        return list(self.strategies.keys())
