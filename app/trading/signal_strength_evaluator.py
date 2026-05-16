"""
app/trading/signal_strength_evaluator.py — Phase 7: Selective AI Filter.

Evaluates signal quality to decide whether AI validation is needed.
Returns a score 0.0–1.0. Above strategy.confidence_threshold → skip AI.
Below → call AI for validation.

Score components:
  +0.30  EMA 8/13 crossover event (primary momentum signal)
  +0.15  EMA 20/50 trend alignment (macro trend confirmation)
  +0.15  RSI in confluence zone (not overbought/oversold)
  +0.15  MACD above signal line (momentum confirmation)
  +0.10  Low volatility (better execution, tighter spread)
  +0.10  Price above key EMA (structure confirmation)
  +0.05  RSI not at extremes (quality filter)

Base: 0.0 — signal must earn its score.
"""

import math

import pandas as pd

from app.logger import get_logger

logger = get_logger("signal_strength_evaluator")


class SignalStrengthEvaluator:
    """
    Stateless evaluator — no async, no DB, pure DataFrame math.
    Called once per signal before the AI filter decision.
    """

    @staticmethod
    def evaluate(dataframe: pd.DataFrame, signal: str) -> float:
        """
        Evaluate signal strength from the latest candle data.

        Args:
            dataframe: DataFrame with indicators applied (from MarketDataEngine)
            signal: "BUY" or "SELL"

        Returns:
            float in [0.0, 1.0] — higher = stronger signal, less AI needed
        """
        if len(dataframe) < 3:
            return 0.0

        try:
            latest = dataframe.iloc[-1]
            prev   = dataframe.iloc[-2]
            return SignalStrengthEvaluator._score(latest, prev, signal)
        except Exception as e:
            logger.warning("signal_strength_eval_error", error=str(e))
            return 0.0

    @staticmethod
    def _score(latest: pd.Series, prev: pd.Series, signal: str) -> float:
        score = 0.0
        is_buy = signal.upper() == "BUY"

        def _get(series: pd.Series, key: str) -> float | None:
            try:
                v = series[key]
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    return None
                return float(v)
            except (KeyError, TypeError):
                return None

        # ── EMA 8/13 crossover event (+0.30) ─────────────────────────
        ema8_now  = _get(latest, "ema_8")
        ema13_now = _get(latest, "ema_13")
        ema8_prev = _get(prev,   "ema_8")
        ema13_prev = _get(prev,  "ema_13")

        if all(v is not None for v in [ema8_now, ema13_now, ema8_prev, ema13_prev]):
            if is_buy and ema8_prev <= ema13_prev and ema8_now > ema13_now:
                score += 0.30
            elif not is_buy and ema8_prev >= ema13_prev and ema8_now < ema13_now:
                score += 0.30

        # ── EMA 20/50 macro trend alignment (+0.15) ───────────────────
        ema20 = _get(latest, "ema_20")
        ema50 = _get(latest, "ema_50")
        close = _get(latest, "close")

        if ema20 is not None and ema50 is not None:
            if is_buy and ema20 > ema50:
                score += 0.15
            elif not is_buy and ema20 < ema50:
                score += 0.15

        # ── RSI confluence zone (+0.15) ───────────────────────────────
        rsi = _get(latest, "rsi")
        if rsi is not None:
            if is_buy and 40 <= rsi <= 65:
                score += 0.15
            elif not is_buy and 35 <= rsi <= 60:
                score += 0.15

        # ── MACD momentum confirmation (+0.15) ────────────────────────
        macd        = _get(latest, "macd")
        macd_signal = _get(latest, "macd_signal")
        if macd is not None and macd_signal is not None:
            if is_buy and macd > macd_signal:
                score += 0.15
            elif not is_buy and macd < macd_signal:
                score += 0.15

        # ── Low volatility (+0.10) ────────────────────────────────────
        volatility = _get(latest, "volatility")
        if volatility is not None and volatility < 0.015:
            score += 0.10

        # ── Price above/below key EMA structure (+0.10) ───────────────
        if close is not None and ema8_now is not None:
            if is_buy and close > ema8_now:
                score += 0.10
            elif not is_buy and close < ema8_now:
                score += 0.10

        # ── RSI not at extremes (+0.05) ───────────────────────────────
        if rsi is not None and 25 < rsi < 75:
            score += 0.05

        final_score = round(min(score, 1.0), 4)

        logger.debug(
            "signal_strength_evaluated",
            signal=signal,
            score=final_score,
        )

        return final_score
