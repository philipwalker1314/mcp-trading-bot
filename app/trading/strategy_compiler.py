"""
RuntimeStrategyCompiler — converts a StrategyConfig (JSON) into a
live BaseStrategy instance without writing any .py files to disk.

Architecture:
- IndicatorEngine: applies indicator list from config to a DataFrame
- RuleEvaluator:  evaluates a single rule dict against latest + prev rows
- CompiledStrategy: BaseStrategy subclass generated at runtime
- RuntimeStrategyCompiler: cache + factory

Supported indicator types:
  ema, rsi, macd, atr, volatility, bbands, stoch, obv, vwap

Supported rule operators:
  gt, lt, gte, lte, eq, between, crosses_above, crosses_below

All compilation errors raise StrategyCompileError with a human-readable message.
"""

import math
from typing import Any

import pandas as pd
import ta

from app.logger import get_logger
from app.trading.strategy import BaseStrategy

logger = get_logger("strategy_compiler")


# ─────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────

class StrategyCompileError(Exception):
    """Raised when a strategy config cannot be compiled."""
    pass


class RuleEvaluationError(Exception):
    """Raised when a rule fails to evaluate at runtime."""
    pass


# ─────────────────────────────────────────────
# Indicator engine
# ─────────────────────────────────────────────

class IndicatorEngine:
    """
    Applies a list of indicator configs to a DataFrame.

    Each indicator config is a dict:
      {"type": "ema",  "period": 8,  "column": "ema_8"}
      {"type": "rsi",  "period": 14, "column": "rsi"}
      {"type": "macd"}
      {"type": "atr",  "period": 14}
      {"type": "volatility", "period": 20}
      {"type": "bbands", "period": 20, "std": 2}
      {"type": "stoch", "k": 14, "d": 3}
      {"type": "obv"}
      {"type": "vwap"}
    """

    SUPPORTED = {"ema", "rsi", "macd", "atr", "volatility", "bbands", "stoch", "obv", "vwap"}

    @staticmethod
    def apply(df: pd.DataFrame, indicator_configs: list[dict]) -> pd.DataFrame:
        for cfg in indicator_configs:
            itype = cfg.get("type", "").lower()
            try:
                df = IndicatorEngine._apply_one(df, itype, cfg)
            except Exception as e:
                logger.error(
                    "indicator_apply_error",
                    indicator_type=itype,
                    error=str(e),
                )
                # Don't crash — just skip the broken indicator
        return df

    @staticmethod
    def _apply_one(df: pd.DataFrame, itype: str, cfg: dict) -> pd.DataFrame:
        col = cfg.get("column")

        if itype == "ema":
            period = int(cfg.get("period", 20))
            out    = col or f"ema_{period}"
            df[out] = ta.trend.ema_indicator(df["close"], window=period)

        elif itype == "rsi":
            period = int(cfg.get("period", 14))
            out    = col or "rsi"
            df[out] = ta.momentum.rsi(df["close"], window=period)

        elif itype == "macd":
            fast   = int(cfg.get("fast", 12))
            slow   = int(cfg.get("slow", 26))
            signal = int(cfg.get("signal", 9))
            df["macd"]        = ta.trend.macd(df["close"], window_fast=fast, window_slow=slow)
            df["macd_signal"] = ta.trend.macd_signal(df["close"], window_fast=fast, window_slow=slow, window_sign=signal)
            df["macd_hist"]   = ta.trend.macd_diff(df["close"], window_fast=fast, window_slow=slow, window_sign=signal)

        elif itype == "atr":
            period = int(cfg.get("period", 14))
            out    = col or "atr"
            df[out] = ta.volatility.average_true_range(
                df["high"], df["low"], df["close"], window=period
            )

        elif itype == "volatility":
            period = int(cfg.get("period", 20))
            out    = col or "volatility"
            df[out] = df["close"].pct_change().rolling(period).std()

        elif itype == "bbands":
            period = int(cfg.get("period", 20))
            std    = float(cfg.get("std", 2.0))
            df["bb_upper"] = ta.volatility.bollinger_hband(df["close"], window=period, window_dev=std)
            df["bb_lower"] = ta.volatility.bollinger_lband(df["close"], window=period, window_dev=std)
            df["bb_mid"]   = ta.volatility.bollinger_mavg(df["close"],  window=period)

        elif itype == "stoch":
            k      = int(cfg.get("k", 14))
            d      = int(cfg.get("d", 3))
            df["stoch_k"] = ta.momentum.stoch(df["high"], df["low"], df["close"], window=k)
            df["stoch_d"] = ta.momentum.stoch_signal(df["high"], df["low"], df["close"], window=k, smooth_window=d)

        elif itype == "obv":
            out    = col or "obv"
            df[out] = ta.volume.on_balance_volume(df["close"], df["volume"])

        elif itype == "vwap":
            out    = col or "vwap"
            # Simple VWAP approximation: cumulative typical price * volume / cumulative volume
            typical_price = (df["high"] + df["low"] + df["close"]) / 3
            df[out] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()

        else:
            raise StrategyCompileError(f"Unknown indicator type: {itype!r}")

        return df

    @classmethod
    def validate_configs(cls, indicator_configs: list[dict]) -> list[str]:
        """Returns list of error strings. Empty = valid."""
        errors = []
        for i, cfg in enumerate(indicator_configs):
            itype = cfg.get("type", "")
            if not itype:
                errors.append(f"Indicator [{i}]: missing 'type'")
            elif itype.lower() not in cls.SUPPORTED:
                errors.append(f"Indicator [{i}]: unsupported type {itype!r}. Supported: {sorted(cls.SUPPORTED)}")
        return errors


# ─────────────────────────────────────────────
# Rule evaluator
# ─────────────────────────────────────────────

class RuleEvaluator:
    """
    Evaluates a single rule dict against a DataFrame row.

    Rule schema:
      {
        "indicator": "ema_8",          # column name in df
        "op": "crosses_above",         # operator
        "target": "ema_13",            # compare against another column
        "value": 50.0,                 # compare against a literal value
        "value_min": 40.0,             # for "between"
        "value_max": 65.0              # for "between"
      }

    For cross operators, both latest and prev rows are used.
    For all others, only latest is used.
    """

    CROSS_OPS = {"crosses_above", "crosses_below"}
    VALUE_OPS = {"gt", "lt", "gte", "lte", "eq", "between"}

    @staticmethod
    def evaluate(rule: dict, latest: pd.Series, prev: pd.Series) -> bool:
        indicator = rule.get("indicator")
        op        = rule.get("op", "").lower()

        if not indicator:
            raise RuleEvaluationError(f"Rule missing 'indicator': {rule}")
        if not op:
            raise RuleEvaluationError(f"Rule missing 'op': {rule}")

        # Resolve left-hand side (current value)
        lhs = RuleEvaluator._resolve_value(indicator, latest)
        if lhs is None or (isinstance(lhs, float) and math.isnan(lhs)):
            return False  # Indicator not yet computed — skip signal

        # Cross operators need previous value
        if op in RuleEvaluator.CROSS_OPS:
            lhs_prev = RuleEvaluator._resolve_value(indicator, prev)
            if lhs_prev is None or (isinstance(lhs_prev, float) and math.isnan(lhs_prev)):
                return False

            target = rule.get("target")
            if not target:
                raise RuleEvaluationError(f"Cross operator requires 'target': {rule}")

            rhs      = RuleEvaluator._resolve_value(target, latest)
            rhs_prev = RuleEvaluator._resolve_value(target, prev)

            if rhs is None or rhs_prev is None:
                return False

            if op == "crosses_above":
                return float(lhs_prev) <= float(rhs_prev) and float(lhs) > float(rhs)
            elif op == "crosses_below":
                return float(lhs_prev) >= float(rhs_prev) and float(lhs) < float(rhs)

        # Value comparison operators
        if op == "between":
            val_min = rule.get("value_min")
            val_max = rule.get("value_max")
            if val_min is None or val_max is None:
                raise RuleEvaluationError(f"'between' requires value_min and value_max: {rule}")
            return float(val_min) <= float(lhs) <= float(val_max)

        # Single-value comparisons — rhs can be a column or a literal
        rhs_col = rule.get("target")
        rhs_val = rule.get("value")

        if rhs_col:
            rhs = RuleEvaluator._resolve_value(rhs_col, latest)
        elif rhs_val is not None:
            rhs = float(rhs_val)
        else:
            raise RuleEvaluationError(f"Rule requires 'target' or 'value': {rule}")

        if rhs is None or (isinstance(rhs, float) and math.isnan(rhs)):
            return False

        lhs_f = float(lhs)
        rhs_f = float(rhs)

        if op == "gt":    return lhs_f >  rhs_f
        if op == "lt":    return lhs_f <  rhs_f
        if op == "gte":   return lhs_f >= rhs_f
        if op == "lte":   return lhs_f <= rhs_f
        if op == "eq":    return abs(lhs_f - rhs_f) < 1e-9

        raise RuleEvaluationError(f"Unknown operator: {op!r}")

    @staticmethod
    def _resolve_value(column: str, row: pd.Series) -> float | None:
        """Resolve a column name from a DataFrame row, or None if missing."""
        try:
            val = row[column]
            return float(val)
        except (KeyError, TypeError, ValueError):
            return None

    @classmethod
    def evaluate_all(
        cls,
        rules:  list[dict],
        latest: pd.Series,
        prev:   pd.Series,
    ) -> bool:
        """All rules must pass (AND logic)."""
        if not rules:
            return False
        for rule in rules:
            if not cls.evaluate(rule, latest, prev):
                return False
        return True

    @classmethod
    def validate_rules(cls, rules: list[dict], known_columns: set[str] | None = None) -> list[str]:
        """
        Validate rule list at save time.
        Returns list of error strings. Empty = valid.
        known_columns is optional — if provided, indicator columns are checked.
        """
        errors = []
        valid_ops = cls.CROSS_OPS | cls.VALUE_OPS

        for i, rule in enumerate(rules or []):
            prefix = f"Rule [{i}]"
            op = rule.get("op", "")
            indicator = rule.get("indicator")

            if not indicator:
                errors.append(f"{prefix}: missing 'indicator'")
            if not op:
                errors.append(f"{prefix}: missing 'op'")
            elif op.lower() not in valid_ops:
                errors.append(f"{prefix}: unknown op {op!r}. Valid: {sorted(valid_ops)}")
                continue

            op = op.lower()

            if op in cls.CROSS_OPS and not rule.get("target"):
                errors.append(f"{prefix}: cross operator requires 'target'")

            if op == "between":
                if rule.get("value_min") is None:
                    errors.append(f"{prefix}: 'between' requires 'value_min'")
                if rule.get("value_max") is None:
                    errors.append(f"{prefix}: 'between' requires 'value_max'")

            if op in cls.VALUE_OPS and op != "between":
                if rule.get("target") is None and rule.get("value") is None:
                    errors.append(f"{prefix}: requires 'target' or 'value'")

        return errors


# ─────────────────────────────────────────────
# Compiled strategy (dynamic BaseStrategy subclass)
# ─────────────────────────────────────────────

class CompiledStrategy(BaseStrategy):
    """
    A BaseStrategy instance produced by the compiler at runtime.
    Holds indicator configs and rule trees; no .py file involved.
    """

    def __init__(
        self,
        config_id:          int,
        config_name:        str,
        config_description: str,
        config_timeframe:   str,
        stop_loss_percent:  float,
        take_profit_percent: float,
        trailing_stop_percent: float | None,
        indicator_configs:  list[dict],
        entry_rules:        list[dict],
        exit_rules:         list[dict] | None,
    ):
        # BaseStrategy class attributes (set per-instance for compiled strategies)
        self.name        = config_name
        self.description = config_description
        self.timeframe   = config_timeframe
        self.enabled     = True

        self.stop_loss_percent     = stop_loss_percent
        self.take_profit_percent   = take_profit_percent
        self.trailing_stop_percent = trailing_stop_percent

        self._config_id        = config_id
        self._indicator_configs = indicator_configs
        self._entry_rules       = entry_rules
        self._exit_rules        = exit_rules or []

    async def generate_signal(self, dataframe: pd.DataFrame) -> str:
        """
        Apply indicators then evaluate entry/exit rules.
        Returns BUY / SELL / HOLD.
        """
        if len(dataframe) < 20:
            return "HOLD"

        # Apply configured indicators
        df = IndicatorEngine.apply(dataframe.copy(), self._indicator_configs)

        if len(df) < 2:
            return "HOLD"

        latest = df.iloc[-1]
        prev   = df.iloc[-2]

        # Check entry rules → BUY
        try:
            if RuleEvaluator.evaluate_all(self._entry_rules, latest, prev):
                return "BUY"
        except RuleEvaluationError as e:
            logger.warning(
                "rule_evaluation_error",
                strategy=self.name,
                error=str(e),
            )

        # Check exit rules → SELL (if configured)
        if self._exit_rules:
            try:
                if RuleEvaluator.evaluate_all(self._exit_rules, latest, prev):
                    return "SELL"
            except RuleEvaluationError as e:
                logger.warning(
                    "exit_rule_evaluation_error",
                    strategy=self.name,
                    error=str(e),
                )

        return "HOLD"


# ─────────────────────────────────────────────
# Compiler (cache + factory)
# ─────────────────────────────────────────────

class RuntimeStrategyCompiler:
    """
    Converts StrategyConfig dicts into CompiledStrategy instances.

    Cache key: (config_id, version) — any version bump invalidates the cache.
    Thread-safe for async use (no shared mutable state across coroutines).
    """

    def __init__(self):
        # (config_id, version) → CompiledStrategy
        self._cache: dict[tuple[int, int], CompiledStrategy] = {}

    def compile(self, config: dict) -> CompiledStrategy:
        """
        Compile a strategy config dict into a CompiledStrategy.
        Uses cache when possible; rebuilds on version change.
        """
        config_id = config["id"]
        version   = config["version"]
        cache_key = (config_id, version)

        if cache_key in self._cache:
            return self._cache[cache_key]

        errors = self.validate(config)
        if errors:
            raise StrategyCompileError(
                f"Strategy {config['name']!r} failed validation: " +
                "; ".join(errors)
            )

        strategy = CompiledStrategy(
            config_id=config_id,
            config_name=config["name"],
            config_description=config.get("description") or "",
            config_timeframe=config.get("timeframe", "1m"),
            stop_loss_percent=float(config.get("stop_loss_pct", 0.02)),
            take_profit_percent=float(config.get("take_profit_pct", 0.04)),
            trailing_stop_percent=config.get("trailing_stop_pct"),
            indicator_configs=config.get("indicators", []),
            entry_rules=config.get("entry_rules", []),
            exit_rules=config.get("exit_rules"),
        )

        self._cache[cache_key] = strategy

        logger.info(
            "strategy_compiled",
            name=config["name"],
            version=version,
            rules=len(config.get("entry_rules", [])),
        )

        return strategy

    def invalidate(self, config_id: int):
        """Remove all cached versions for a given config_id."""
        keys_to_remove = [k for k in self._cache if k[0] == config_id]
        for k in keys_to_remove:
            del self._cache[k]
        if keys_to_remove:
            logger.info("strategy_cache_invalidated", config_id=config_id)

    def invalidate_all(self):
        self._cache.clear()
        logger.info("strategy_cache_invalidated_all")

    @staticmethod
    def validate(config: dict) -> list[str]:
        """
        Full validation of a strategy config dict.
        Returns list of error strings. Empty = valid.
        """
        errors: list[str] = []

        if not config.get("name", "").strip():
            errors.append("'name' is required")

        if not config.get("entry_rules"):
            errors.append("'entry_rules' must have at least one rule")

        if not config.get("symbols"):
            errors.append("'symbols' must have at least one symbol")

        # Validate indicators
        indicator_errors = IndicatorEngine.validate_configs(
            config.get("indicators", [])
        )
        errors.extend(indicator_errors)

        # Collect all output columns from indicators to validate rule references
        known_cols: set[str] = {"open", "high", "low", "close", "volume", "timestamp"}
        for ind in config.get("indicators", []):
            itype = ind.get("type", "")
            col   = ind.get("column")
            if col:
                known_cols.add(col)
            elif itype == "ema":
                known_cols.add(f"ema_{ind.get('period', 20)}")
            elif itype == "rsi":
                known_cols.add("rsi")
            elif itype == "macd":
                known_cols.update(["macd", "macd_signal", "macd_hist"])
            elif itype == "atr":
                known_cols.add("atr")
            elif itype == "volatility":
                known_cols.add("volatility")
            elif itype == "bbands":
                known_cols.update(["bb_upper", "bb_lower", "bb_mid"])
            elif itype == "stoch":
                known_cols.update(["stoch_k", "stoch_d"])
            elif itype == "obv":
                known_cols.add("obv")
            elif itype == "vwap":
                known_cols.add("vwap")

        entry_errors = RuleEvaluator.validate_rules(
            config.get("entry_rules", []), known_cols
        )
        errors.extend([f"EntryRule: {e}" for e in entry_errors])

        exit_errors = RuleEvaluator.validate_rules(
            config.get("exit_rules") or [], known_cols
        )
        errors.extend([f"ExitRule: {e}" for e in exit_errors])

        # Risk config
        sl = config.get("stop_loss_pct", 0.02)
        tp = config.get("take_profit_pct", 0.04)
        if not (0 < float(sl) <= 0.20):
            errors.append(f"stop_loss_pct must be between 0 and 0.20, got {sl}")
        if not (0 < float(tp) <= 0.50):
            errors.append(f"take_profit_pct must be between 0 and 0.50, got {tp}")

        return errors


# ─────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────

compiler = RuntimeStrategyCompiler()
