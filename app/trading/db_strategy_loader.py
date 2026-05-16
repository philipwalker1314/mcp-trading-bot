"""
DBStrategyLoader — extends StrategyLoader to merge file-based strategies
with compiled DB strategies.

Drop-in replacement for StrategyLoader in TradingBot.

Priority: DB strategies take precedence over file strategies by name.
File strategies are still hot-reloaded as before.
DB strategies are reloaded from DB on every candle (async, cheap — uses compiler cache).

Usage in TradingBot (replace self.strategy_loader with self.db_strategy_loader):
  self.db_strategy_loader = DBStrategyLoader(
      session_factory=AsyncSessionLocal,
      compiler=compiler,
  )
  strategies = await self.db_strategy_loader.load_strategies_async()
"""

from app.database import AsyncSessionLocal
from app.logger import get_logger
from app.services.strategy_config_service import StrategyConfigService
from app.trading.strategy_compiler import RuntimeStrategyCompiler, compiler
from app.trading.strategy_loader import StrategyLoader

logger = get_logger("db_strategy_loader")


class DBStrategyLoader(StrategyLoader):
    """
    Async-aware strategy loader that merges:
    1. File-based strategies from strategies/custom/ (hot-reload, mtime cache)
    2. DB-based compiled strategies from strategy_configs table

    DB strategies are compiled at runtime via RuntimeStrategyCompiler.
    File strategies are kept for backward compatibility.
    DB strategies override file strategies with the same name.
    """

    def __init__(
        self,
        session_factory=None,
        strategy_compiler: RuntimeStrategyCompiler | None = None,
    ):
        super().__init__()  # inherits mtime cache + file loading
        self._svc = StrategyConfigService(
            session_factory=session_factory or AsyncSessionLocal,
            strategy_compiler=strategy_compiler or compiler,
        )

    async def load_strategies_async(self) -> dict:
        """
        Async version: loads both file and DB strategies.
        File strategies are loaded synchronously (mtime cache).
        DB strategies are fetched async and compiled.

        Returns merged dict {strategy_name: strategy_instance}
        """
        # 1. Load file-based strategies (sync, mtime cached)
        file_strategies = self.load_strategies()

        # 2. Load and compile DB strategies
        try:
            db_strategies = await self._svc.get_compiled_strategies()
        except Exception as e:
            logger.error("db_strategy_load_error", error=str(e))
            db_strategies = {}

        # 3. Merge — DB takes precedence over file strategies
        merged = {**file_strategies, **db_strategies}

        if db_strategies:
            logger.debug(
                "strategies_merged",
                file_count=len(file_strategies),
                db_count=len(db_strategies),
                total=len(merged),
            )

        return merged

    async def reload_db_strategies(self) -> dict:
        """Force reload of DB strategies only (compiler cache invalidated externally)."""
        try:
            return await self._svc.get_compiled_strategies()
        except Exception as e:
            logger.error("db_strategy_reload_error", error=str(e))
            return {}
