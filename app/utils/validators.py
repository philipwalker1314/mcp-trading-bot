from app.config import settings


class TradeValidator:

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        return "/" in symbol

    @staticmethod
    def validate_order_size(quantity: float) -> bool:
        return quantity > 0

    @staticmethod
    def validate_risk_limit(risk: float) -> bool:

        return (
            risk > 0
            and risk <= settings.MAX_RISK_PER_TRADE
        )

    @staticmethod
    def validate_stop_loss(
        entry_price: float,
        stop_loss: float,
    ) -> bool:

        return stop_loss > 0 and stop_loss != entry_price

    @staticmethod
    def validate_take_profit(
        entry_price: float,
        take_profit: float,
    ) -> bool:

        return take_profit > 0 and take_profit != entry_price
