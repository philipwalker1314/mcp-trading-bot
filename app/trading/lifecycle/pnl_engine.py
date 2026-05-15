from dataclasses import dataclass
from app.models.trades import Position, TradeSide


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────

@dataclass
class PnLResult:
    unrealized_pnl: float
    realized_pnl:   float
    net_pnl:        float          # realized - fees
    fees:           float
    return_pct:     float          # % return on notional
    notional_value: float          # position size in quote currency


@dataclass
class DailyStats:
    total_trades:   int
    winning_trades: int
    losing_trades:  int
    win_rate:       float
    profit_factor:  float
    avg_win:        float
    avg_loss:       float
    realized_pnl:   float
    gross_profit:   float
    gross_loss:     float


# ─────────────────────────────────────────────
# PnLEngine
# ─────────────────────────────────────────────

class PnLEngine:
    """
    Stateless calculation engine.
    All methods are pure functions — no DB,
    no async, no side effects.
    """

    # Standard maker/taker fees — override
    # per broker in production
    DEFAULT_FEE_RATE = 0.001  # 0.1% per side

    @staticmethod
    def calc_unrealized_pnl(
        position: Position,
        current_price: float,
    ) -> float:
        """
        Calculate mark-to-market PnL for an
        open position.
        """
        multiplier = (
            1.0 if position.side == TradeSide.BUY
            else -1.0
        )
        return (
            (current_price - position.avg_entry_price)
            * position.remaining_quantity
            * multiplier
        )

    @staticmethod
    def calc_realized_pnl(
        position: Position,
        exit_price: float,
        exit_quantity: float | None = None,
    ) -> float:
        """
        Calculate PnL for a full or partial close.
        If exit_quantity is None, uses remaining_quantity.
        """
        qty = exit_quantity or position.remaining_quantity
        multiplier = (
            1.0 if position.side == TradeSide.BUY
            else -1.0
        )
        return (
            (exit_price - position.avg_entry_price)
            * qty
            * multiplier
        )

    @staticmethod
    def calc_fees(
        price: float,
        quantity: float,
        fee_rate: float = DEFAULT_FEE_RATE,
    ) -> float:
        """Fee on one side of a trade."""
        return price * quantity * fee_rate

    @staticmethod
    def calc_trailing_stop(
        position: Position,
        current_price: float,
    ) -> float | None:
        """
        Compute where the trailing stop should be.
        Returns the new stop price, or None if
        the position has no trailing stop configured.

        For BUY: stop rises as price rises.
        For SELL: stop falls as price falls.
        """
        if not position.trailing_stop_pct:
            return None

        pct = position.trailing_stop_pct

        if position.side == TradeSide.BUY:
            new_stop = current_price * (1 - pct)
            # Only move trailing stop upward
            current = position.trailing_stop_price or 0.0
            return max(new_stop, current)

        else:  # SELL
            new_stop = current_price * (1 + pct)
            # Only move trailing stop downward
            current = position.trailing_stop_price or float("inf")
            return min(new_stop, current)

    @staticmethod
    def is_stop_loss_hit(
        position: Position,
        current_price: float,
    ) -> bool:
        """
        Check if current price has crossed the
        stop loss level.
        Uses trailing_stop_price if set (trailing takes
        priority), otherwise falls back to stop_loss.
        """
        sl = position.trailing_stop_price or position.stop_loss
        if sl is None:
            return False

        if position.side == TradeSide.BUY:
            return current_price <= sl
        else:
            return current_price >= sl

    @staticmethod
    def is_take_profit_hit(
        position: Position,
        current_price: float,
    ) -> bool:
        """
        Check if current price has crossed the
        take profit level.
        """
        if position.take_profit is None:
            return False

        if position.side == TradeSide.BUY:
            return current_price >= position.take_profit
        else:
            return current_price <= position.take_profit

    @staticmethod
    def calc_position_size(
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        """
        Risk-based position sizing.

        Answers: "How many units can I buy such that
        if SL is hit, I lose exactly risk_pct of capital?"

        position_size = risk_amount / (entry - stop_loss)
        """
        if stop_loss <= 0 or entry_price <= stop_loss:
            return 0.0

        risk_amount   = capital * risk_pct
        stop_distance = abs(entry_price - stop_loss)

        return risk_amount / stop_distance

    @staticmethod
    def calc_return_pct(
        entry_price: float,
        exit_price: float,
        side: TradeSide,
    ) -> float:
        """Percentage return on notional."""
        if entry_price <= 0:
            return 0.0

        raw_return = (exit_price - entry_price) / entry_price
        return raw_return if side == TradeSide.BUY else -raw_return

    @classmethod
    def full_pnl_result(
        cls,
        position: Position,
        current_price: float,
    ) -> PnLResult:
        """
        Complete PnL snapshot for a position.
        Used for dashboards and API responses.
        """
        unrealized = cls.calc_unrealized_pnl(position, current_price)
        notional   = current_price * position.remaining_quantity
        fees       = position.total_fees
        return_pct = cls.calc_return_pct(
            position.avg_entry_price,
            current_price,
            position.side,
        )

        return PnLResult(
            unrealized_pnl=unrealized,
            realized_pnl=position.realized_pnl,
            net_pnl=position.realized_pnl + unrealized - fees,
            fees=fees,
            return_pct=return_pct,
            notional_value=notional,
        )

    @staticmethod
    def calc_daily_stats(
        closed_pnls: list[float],
    ) -> DailyStats:
        """
        Compute daily performance stats from a
        list of realized PnL values for closed trades.
        """
        if not closed_pnls:
            return DailyStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        wins   = [p for p in closed_pnls if p > 0]
        losses = [p for p in closed_pnls if p <= 0]

        gross_profit = sum(wins)
        gross_loss   = sum(losses)

        win_rate = len(wins) / len(closed_pnls) if closed_pnls else 0.0

        profit_factor = (
            gross_profit / abs(gross_loss)
            if gross_loss != 0
            else float("inf")
        )

        return DailyStats(
            total_trades=len(closed_pnls),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=sum(wins) / len(wins) if wins else 0.0,
            avg_loss=sum(losses) / len(losses) if losses else 0.0,
            realized_pnl=sum(closed_pnls),
            gross_profit=gross_profit,
            gross_loss=gross_loss,
        )

