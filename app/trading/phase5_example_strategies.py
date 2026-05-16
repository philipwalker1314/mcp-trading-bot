"""
phase5_example_strategies.py

Example strategy configs to POST to /strategies/ for testing.
These can be used as seeds or as reference for the frontend form.

Usage:
  POST http://localhost:8000/strategies/
  Content-Type: application/json
  Body: one of the dicts below
"""

# ─────────────────────────────────────────────
# Example 1 — EMA 8/13 crossover (mirrors existing my_custom_strategy.py)
# ─────────────────────────────────────────────

EMA_CROSSOVER = {
    "name": "ema_crossover_db",
    "description": "EMA 8/13 crossover + RSI confluence — compiled from DB",
    "timeframe": "1m",
    "symbols": ["BTC/USDT"],
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "trailing_stop_pct": 0.015,
    "indicators": [
        {"type": "ema", "period": 8,  "column": "ema_8"},
        {"type": "ema", "period": 13, "column": "ema_13"},
        {"type": "rsi", "period": 14},
    ],
    "entry_rules": [
        {"indicator": "ema_8", "op": "crosses_above", "target": "ema_13"},
        {"indicator": "rsi",   "op": "between", "value_min": 40, "value_max": 65},
        {"indicator": "close", "op": "gt", "target": "ema_8"},
    ],
    "exit_rules": [
        {"indicator": "ema_8", "op": "crosses_below", "target": "ema_13"},
    ],
    "enabled": False,
}

# ─────────────────────────────────────────────
# Example 2 — RSI oversold bounce
# ─────────────────────────────────────────────

RSI_OVERSOLD = {
    "name": "rsi_oversold_bounce",
    "description": "Buy when RSI oversold, EMA trend confirms",
    "timeframe": "1m",
    "symbols": ["BTC/USDT"],
    "stop_loss_pct": 0.015,
    "take_profit_pct": 0.03,
    "trailing_stop_pct": None,
    "indicators": [
        {"type": "ema",  "period": 20, "column": "ema_20"},
        {"type": "ema",  "period": 50, "column": "ema_50"},
        {"type": "rsi",  "period": 14},
        {"type": "atr",  "period": 14},
    ],
    "entry_rules": [
        {"indicator": "rsi",    "op": "lt",  "value": 35},
        {"indicator": "ema_20", "op": "gt",  "target": "ema_50"},
        {"indicator": "close",  "op": "gt",  "target": "ema_50"},
    ],
    "exit_rules": [
        {"indicator": "rsi", "op": "gt", "value": 65},
    ],
    "enabled": False,
}

# ─────────────────────────────────────────────
# Example 3 — Bollinger Band squeeze breakout
# ─────────────────────────────────────────────

BBANDS_BREAKOUT = {
    "name": "bbands_breakout",
    "description": "Price closes above upper BB with RSI momentum",
    "timeframe": "1m",
    "symbols": ["BTC/USDT"],
    "stop_loss_pct": 0.025,
    "take_profit_pct": 0.05,
    "trailing_stop_pct": 0.02,
    "indicators": [
        {"type": "bbands", "period": 20, "std": 2.0},
        {"type": "rsi",    "period": 14},
        {"type": "atr",    "period": 14},
    ],
    "entry_rules": [
        {"indicator": "close", "op": "gt",      "target": "bb_upper"},
        {"indicator": "rsi",   "op": "between",  "value_min": 55, "value_max": 75},
    ],
    "exit_rules": [
        {"indicator": "close", "op": "lt", "target": "bb_mid"},
    ],
    "enabled": False,
}

# ─────────────────────────────────────────────
# Example 4 — MACD crossover
# ─────────────────────────────────────────────

MACD_CROSS = {
    "name": "macd_cross",
    "description": "MACD line crosses above signal line, RSI not overbought",
    "timeframe": "5m",
    "symbols": ["BTC/USDT"],
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "trailing_stop_pct": None,
    "indicators": [
        {"type": "macd"},
        {"type": "rsi", "period": 14},
    ],
    "entry_rules": [
        {"indicator": "macd", "op": "crosses_above", "target": "macd_signal"},
        {"indicator": "rsi",  "op": "lt", "value": 70},
    ],
    "exit_rules": [
        {"indicator": "macd", "op": "crosses_below", "target": "macd_signal"},
    ],
    "enabled": False,
}

ALL_EXAMPLES = [EMA_CROSSOVER, RSI_OVERSOLD, BBANDS_BREAKOUT, MACD_CROSS]
