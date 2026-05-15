import importlib
import os
import pathlib
import sys

from app.logger import get_logger

logger = get_logger("strategy_loader")


class StrategyLoader:

    def __init__(self):
        self.strategies    = {}
        self.strategy_path = pathlib.Path("strategies/custom")

        # FIX 5: cache file mtimes — only reload when a file actually changes
        self._file_mtimes: dict[str, float] = {}

    def load_strategies(self) -> dict:
        """
        Load strategies from disk.

        FIX 5: Checks mtime before reimporting.
        If no file changed since last call, returns cached dict instantly.
        Hot-reload still works — edit a file and it reloads on next candle.
        """
        strategy_files = list(self.strategy_path.glob("*.py"))

        for file in strategy_files:
            if file.name.startswith("_"):
                continue

            module_name = f"strategies.custom.{file.stem}"

            try:
                current_mtime = os.path.getmtime(file)
                cached_mtime  = self._file_mtimes.get(str(file))

                # Skip if file unchanged and already loaded
                if cached_mtime == current_mtime and module_name in sys.modules:
                    continue

                # First load or file changed — (re)import
                if module_name in sys.modules:
                    module = importlib.reload(sys.modules[module_name])
                    logger.info("strategy_reloaded", file=file.name)
                else:
                    module = importlib.import_module(module_name)
                    logger.info("strategy_loaded", file=file.name)

                self._file_mtimes[str(file)] = current_mtime

                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)

                    if (
                        isinstance(attribute, type)
                        and hasattr(attribute, "generate_signal")
                        and attribute.__name__ != "BaseStrategy"
                    ):
                        strategy = attribute()
                        self.strategies[strategy.name] = strategy
                        logger.info("strategy_registered", strategy=strategy.name)

            except Exception as error:
                logger.error(
                    "strategy_load_error",
                    file=file.name,
                    error=str(error),
                )

        return self.strategies

    def get_strategy(self, strategy_name: str):
        return self.strategies.get(strategy_name)

    def enable_strategy(self, strategy_name: str):
        strategy = self.get_strategy(strategy_name)
        if strategy:
            strategy.enabled = True

    def disable_strategy(self, strategy_name: str):
        strategy = self.get_strategy(strategy_name)
        if strategy:
            strategy.enabled = False

    def list_strategies(self) -> list[str]:
        return list(self.strategies.keys())
