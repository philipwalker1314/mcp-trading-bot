"""
StrategyConfigService — CRUD for strategy_configs + version history.

Responsibilities:
- Create / read / update / delete strategy configs
- Bump version and write to strategy_versions on every save
- Invalidate compiler cache on any write
- Load all enabled strategies into the compiler (used by TradingBot)
- Provide list of compiled strategies ready for the strategy engine
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.logger import get_logger
from app.models.strategy_config import StrategyConfig, StrategyVersion
from app.trading.strategy_compiler import (
    CompiledStrategy,
    RuntimeStrategyCompiler,
    StrategyCompileError,
    compiler as _default_compiler,
)

logger = get_logger("strategy_config_service")


class StrategyConfigService:
    """
    Single authoritative service for strategy config CRUD and compilation.
    Uses the module-level RuntimeStrategyCompiler singleton.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker,
        strategy_compiler: RuntimeStrategyCompiler | None = None,
    ):
        self._factory  = session_factory
        self._compiler = strategy_compiler or _default_compiler

    # ─────────────────────────────────────────
    # Create
    # ─────────────────────────────────────────

    async def create(
        self,
        data: dict,
        created_by: str | None = None,
    ) -> StrategyConfig:
        """
        Validate + create a new strategy config.
        Raises StrategyCompileError on validation failure.
        """
        errors = self._compiler.validate(data)
        if errors:
            raise StrategyCompileError("; ".join(errors))

        async with self._factory() as db:
            config = StrategyConfig(
                name=data["name"].strip(),
                description=data.get("description"),
                version=1,
                enabled=data.get("enabled", False),
                timeframe=data.get("timeframe", "1m"),
                symbols=data.get("symbols", []),
                stop_loss_pct=float(data.get("stop_loss_pct", 0.02)),
                take_profit_pct=float(data.get("take_profit_pct", 0.04)),
                trailing_stop_pct=data.get("trailing_stop_pct"),
                entry_rules=data.get("entry_rules", []),
                exit_rules=data.get("exit_rules"),
                indicators=data.get("indicators", []),
                created_by=created_by,
            )
            db.add(config)
            await db.flush()

            # Write initial version snapshot
            snapshot = config.to_snapshot()
            version_row = StrategyVersion(
                strategy_id=config.id,
                version=1,
                snapshot=snapshot,
                change_summary="Initial version",
            )
            db.add(version_row)

            await db.commit()
            await db.refresh(config)

        logger.info(
            "strategy_config_created",
            name=config.name,
            id=config.id,
        )
        return config

    # ─────────────────────────────────────────
    # Read
    # ─────────────────────────────────────────

    async def get(self, config_id: int) -> StrategyConfig | None:
        async with self._factory() as db:
            return await db.get(StrategyConfig, config_id)

    async def get_by_name(self, name: str) -> StrategyConfig | None:
        async with self._factory() as db:
            result = await db.execute(
                select(StrategyConfig).where(StrategyConfig.name == name)
            )
            return result.scalar_one_or_none()

    async def list_all(self, enabled_only: bool = False) -> list[StrategyConfig]:
        async with self._factory() as db:
            query = select(StrategyConfig).order_by(StrategyConfig.created_at.desc())
            if enabled_only:
                query = query.where(StrategyConfig.enabled == True)  # noqa: E712
            result = await db.execute(query)
            return list(result.scalars().all())

    async def get_versions(self, config_id: int) -> list[StrategyVersion]:
        async with self._factory() as db:
            result = await db.execute(
                select(StrategyVersion)
                .where(StrategyVersion.strategy_id == config_id)
                .order_by(StrategyVersion.version.desc())
            )
            return list(result.scalars().all())

    async def get_version(self, config_id: int, version: int) -> StrategyVersion | None:
        async with self._factory() as db:
            result = await db.execute(
                select(StrategyVersion).where(
                    StrategyVersion.strategy_id == config_id,
                    StrategyVersion.version == version,
                )
            )
            return result.scalar_one_or_none()

    # ─────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────

    async def update(
        self,
        config_id: int,
        data: dict,
        change_summary: str | None = None,
    ) -> StrategyConfig:
        """
        Update a strategy config. Bumps version, writes snapshot to history.
        Invalidates compiler cache for this config_id.
        Raises StrategyCompileError on validation failure.
        """
        async with self._factory() as db:
            config = await db.get(StrategyConfig, config_id)
            if not config:
                raise ValueError(f"Strategy config {config_id} not found")

            # Merge new data
            merged = {
                "id":               config.id,
                "name":             data.get("name", config.name),
                "description":      data.get("description", config.description),
                "timeframe":        data.get("timeframe", config.timeframe),
                "symbols":          data.get("symbols", config.symbols),
                "stop_loss_pct":    data.get("stop_loss_pct", config.stop_loss_pct),
                "take_profit_pct":  data.get("take_profit_pct", config.take_profit_pct),
                "trailing_stop_pct": data.get("trailing_stop_pct", config.trailing_stop_pct),
                "entry_rules":      data.get("entry_rules", config.entry_rules),
                "exit_rules":       data.get("exit_rules", config.exit_rules),
                "indicators":       data.get("indicators", config.indicators),
                "version":          config.version + 1,
            }

            errors = self._compiler.validate(merged)
            if errors:
                raise StrategyCompileError("; ".join(errors))

            # Apply changes
            config.name             = merged["name"].strip()
            config.description      = merged["description"]
            config.timeframe        = merged["timeframe"]
            config.symbols          = merged["symbols"]
            config.stop_loss_pct    = float(merged["stop_loss_pct"])
            config.take_profit_pct  = float(merged["take_profit_pct"])
            config.trailing_stop_pct = merged["trailing_stop_pct"]
            config.entry_rules      = merged["entry_rules"]
            config.exit_rules       = merged["exit_rules"]
            config.indicators       = merged["indicators"]
            config.version          = merged["version"]
            config.updated_at       = datetime.utcnow()

            # Version snapshot
            snapshot = config.to_snapshot()
            version_row = StrategyVersion(
                strategy_id=config.id,
                version=config.version,
                snapshot=snapshot,
                change_summary=change_summary or f"Updated to v{config.version}",
            )
            db.add(version_row)

            await db.commit()
            await db.refresh(config)

        # Invalidate compiler cache
        self._compiler.invalidate(config_id)

        logger.info(
            "strategy_config_updated",
            id=config_id,
            name=config.name,
            version=config.version,
        )
        return config

    # ─────────────────────────────────────────
    # Enable / disable (no version bump)
    # ─────────────────────────────────────────

    async def set_enabled(self, config_id: int, enabled: bool) -> StrategyConfig:
        async with self._factory() as db:
            config = await db.get(StrategyConfig, config_id)
            if not config:
                raise ValueError(f"Strategy config {config_id} not found")

            config.enabled    = enabled
            config.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(config)

        action = "enabled" if enabled else "disabled"
        logger.info("strategy_config_toggled", id=config_id, action=action)
        return config

    # ─────────────────────────────────────────
    # Delete
    # ─────────────────────────────────────────

    async def delete(self, config_id: int) -> bool:
        async with self._factory() as db:
            config = await db.get(StrategyConfig, config_id)
            if not config:
                return False

            # Delete version history first (FK)
            versions_result = await db.execute(
                select(StrategyVersion).where(StrategyVersion.strategy_id == config_id)
            )
            for v in versions_result.scalars().all():
                await db.delete(v)

            await db.delete(config)
            await db.commit()

        self._compiler.invalidate(config_id)
        logger.info("strategy_config_deleted", id=config_id)
        return True

    # ─────────────────────────────────────────
    # Rollback to a previous version
    # ─────────────────────────────────────────

    async def rollback(self, config_id: int, target_version: int) -> StrategyConfig:
        """
        Restore config to a previous version snapshot.
        Bumps version (new head = old snapshot + 1).
        """
        version_row = await self.get_version(config_id, target_version)
        if not version_row:
            raise ValueError(f"Version {target_version} not found for strategy {config_id}")

        snapshot = dict(version_row.snapshot)
        snapshot.pop("id", None)
        snapshot.pop("created_at", None)
        snapshot.pop("updated_at", None)

        return await self.update(
            config_id,
            snapshot,
            change_summary=f"Rollback to v{target_version}",
        )

    # ─────────────────────────────────────────
    # Compile all enabled strategies
    # ─────────────────────────────────────────

    async def get_compiled_strategies(self) -> dict[str, CompiledStrategy]:
        """
        Load and compile all enabled strategy configs.
        Called by TradingBot on startup and on demand.
        Returns {strategy_name: CompiledStrategy}
        """
        enabled = await self.list_all(enabled_only=True)
        result: dict[str, CompiledStrategy] = {}

        for config in enabled:
            try:
                compiled = self._compiler.compile(config.to_dict())
                result[config.name] = compiled
            except StrategyCompileError as e:
                logger.error(
                    "strategy_compile_failed",
                    name=config.name,
                    id=config.id,
                    error=str(e),
                )

        logger.info(
            "compiled_strategies_loaded",
            count=len(result),
            names=list(result.keys()),
        )
        return result

    # ─────────────────────────────────────────
    # Test compile (no persistence)
    # ─────────────────────────────────────────

    def test_compile(self, config_dict: dict) -> dict:
        """
        Validate + dry-run compile without saving.
        Returns {"valid": bool, "errors": list[str]}
        """
        errors = self._compiler.validate(config_dict)
        if errors:
            return {"valid": False, "errors": errors}

        # Try actually instantiating it
        try:
            self._compiler.compile({**config_dict, "id": -1, "version": 0})
            return {"valid": True, "errors": []}
        except StrategyCompileError as e:
            return {"valid": False, "errors": [str(e)]}
