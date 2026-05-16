"""
app/trading/ai_token_tracker.py — Phase 7: Token usage tracking.

Tracks AI filter calls and estimated token usage per session.
In-memory only — resets on restart. Exposed via /ai-metrics endpoint
so the frontend can display token budget consumption.

Counters:
  total_calls        — total AI filter calls this session
  calls_skipped      — strong signals that bypassed AI
  calls_made         — signals that went through AI
  estimated_tokens   — rough estimate (150 tokens per call)
  buy_signals        — BUY decisions by AI
  sell_signals       — SELL decisions by AI
  hold_signals       — HOLD (filtered out) by AI
"""

from datetime import datetime
from threading import Lock

from app.logger import get_logger

logger = get_logger("ai_token_tracker")

TOKENS_PER_CALL = 150  # conservative estimate for deepseek-chat


class AITokenTracker:
    """
    Thread-safe (asyncio-safe) in-memory tracker.
    Single instance shared across the trading bot session.
    """

    def __init__(self):
        self._lock = Lock()
        self._reset()

    def _reset(self):
        self.session_start    = datetime.utcnow()
        self.total_calls      = 0      # strategy signals generated
        self.calls_skipped    = 0      # strong signals — AI skipped
        self.calls_made       = 0      # AI actually called
        self.estimated_tokens = 0      # tokens used this session
        self.buy_signals      = 0      # AI returned BUY
        self.sell_signals     = 0      # AI returned SELL
        self.hold_signals     = 0      # AI returned HOLD
        self.last_call_at     = None
        self.last_signal_strength: float | None = None
        self.recent_calls: list[dict] = []  # last 20 calls

    def record_signal(
        self,
        symbol:   str,
        signal:   str,
        strength: float,
        skipped:  bool,
        ai_result: str | None = None,
    ):
        with self._lock:
            self.total_calls += 1
            self.last_signal_strength = strength

            if skipped:
                self.calls_skipped += 1
                status = "SKIP"
            else:
                self.calls_made       += 1
                self.estimated_tokens += TOKENS_PER_CALL
                self.last_call_at     = datetime.utcnow()
                status = "AI"

                if ai_result == "BUY":
                    self.buy_signals += 1
                elif ai_result == "SELL":
                    self.sell_signals += 1
                elif ai_result == "HOLD":
                    self.hold_signals += 1

            # Keep rolling window of last 20 calls
            record = {
                "ts":       datetime.utcnow().isoformat(),
                "symbol":   symbol,
                "signal":   signal,
                "strength": round(strength, 3),
                "status":   status,
                "ai_result": ai_result,
            }
            self.recent_calls.append(record)
            if len(self.recent_calls) > 20:
                self.recent_calls = self.recent_calls[-20:]

        logger.debug(
            "token_tracker_record",
            symbol=symbol,
            signal=signal,
            strength=strength,
            skipped=skipped,
            ai_result=ai_result,
        )

    def to_dict(self) -> dict:
        with self._lock:
            skip_rate = (
                round(self.calls_skipped / self.total_calls, 4)
                if self.total_calls > 0 else 0.0
            )
            ai_rate = (
                round(self.calls_made / self.total_calls, 4)
                if self.total_calls > 0 else 0.0
            )
            ai_hold_rate = (
                round(self.hold_signals / self.calls_made, 4)
                if self.calls_made > 0 else 0.0
            )

            return {
                "session_start":        self.session_start.isoformat(),
                "session_duration_min": round(
                    (datetime.utcnow() - self.session_start).total_seconds() / 60, 1
                ),
                "total_signals":        self.total_calls,
                "calls_skipped":        self.calls_skipped,
                "calls_made":           self.calls_made,
                "skip_rate":            skip_rate,
                "ai_call_rate":         ai_rate,
                "estimated_tokens":     self.estimated_tokens,
                "estimated_cost_usd":   round(self.estimated_tokens * 0.00000014, 6),  # ~$0.14/1M tokens
                "ai_buy_signals":       self.buy_signals,
                "ai_sell_signals":      self.sell_signals,
                "ai_hold_signals":      self.hold_signals,
                "ai_hold_rate":         ai_hold_rate,
                "last_call_at":         self.last_call_at.isoformat() if self.last_call_at else None,
                "last_signal_strength": self.last_signal_strength,
                "recent_calls":         list(self.recent_calls),
            }

    def reset(self):
        with self._lock:
            self._reset()
        logger.info("ai_token_tracker_reset")


# Module-level singleton shared with trading_bot
ai_token_tracker = AITokenTracker()
