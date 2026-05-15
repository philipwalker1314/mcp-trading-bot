"""
my_custom_strategy — versión optimizada.

Problema original:
  Generaba BUY o SELL en cada vela (nunca HOLD).
  → DeepSeek se llamaba cada minuto sin importar condiciones de mercado.

Fix aplicado:
  Agregados filtros de confluencia estrictos.
  La estrategia retorna HOLD la gran mayoría del tiempo.
  Solo señala cuando hay una alineación real: tendencia + momentum + cruce.
  DeepSeek se llama muchísimo menos frecuente.

Lógica de señal:
  BUY  — precio > EMA20 > EMA50 (tendencia alcista)
         + EMA20 cruzó arriba de EMA50 en la vela actual (evento, no estado)
         + RSI entre 40-65 (momentum sin sobrecompra)

  SELL — precio < EMA20 < EMA50 (tendencia bajista)
         + EMA20 cruzó abajo de EMA50 en la vela actual
         + RSI entre 35-60 (momentum sin sobreventam)

  HOLD — cualquier otra condición

El cruce de EMA es el filtro más restrictivo: solo ocurre una vez cada
muchas velas. Eso es exactamente cuándo queremos que el AI valide.
"""

from app.trading.strategy import BaseStrategy


class MyCustomStrategy(BaseStrategy):

    name        = "my_custom_strategy"
    description = "EMA crossover + RSI confluence — signals only on cross events"
    timeframe   = "1m"

    stop_loss_percent     = 0.02   # 2%
    take_profit_percent   = 0.04   # 4%
    trailing_stop_percent = 0.015  # 1.5%

    async def generate_signal(self, dataframe) -> str:

        # Need at least 52 candles for EMA50 to be stable
        if len(dataframe) < 52:
            return "HOLD"

        latest = dataframe.iloc[-1]
        prev   = dataframe.iloc[-2]

        close  = latest["close"]
        ema_20 = latest["ema_20"]
        ema_50 = latest["ema_50"]
        rsi    = latest["rsi"]

        # Skip if any indicator is NaN (startup period)
        if any(v != v for v in [ema_20, ema_50, rsi]):
            return "HOLD"

        # ── BUY: EMA20 crossed ABOVE EMA50 this candle ───────────────
        # Requires all three to align:
        #   1. Crossover happened on this exact candle (event, not state)
        #   2. Price is above both EMAs (trend confirmation)
        #   3. RSI in healthy zone — not overbought
        ema_crossed_up    = prev["ema_20"] <= prev["ema_50"] and ema_20 > ema_50
        bullish_structure = close > ema_20 > ema_50
        rsi_bullish_zone  = 40 < rsi < 65

        if ema_crossed_up and bullish_structure and rsi_bullish_zone:
            return "BUY"

        # ── SELL: EMA20 crossed BELOW EMA50 this candle ──────────────
        ema_crossed_down  = prev["ema_20"] >= prev["ema_50"] and ema_20 < ema_50
        bearish_structure = close < ema_20 < ema_50
        rsi_bearish_zone  = 35 < rsi < 60

        if ema_crossed_down and bearish_structure and rsi_bearish_zone:
            return "SELL"

        return "HOLD"
