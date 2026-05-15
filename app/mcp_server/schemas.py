from pydantic import BaseModel


class MarketDataRequest(BaseModel):

    symbol: str = "BTC/USDT"

    timeframe: str = "1m"

    limit: int = 100


class AnalyzeTradeRequest(BaseModel):

    symbol: str

    signal: str

    strategy_name: str


class ExecuteTradeRequest(BaseModel):

    symbol: str

    signal: str

    strategy_name: str
