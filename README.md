# MCP Trading Bot

Trading infrastructure with:

- FastAPI
- Async execution engine
- Binance integration
- DeepSeek AI validation
- PostgreSQL
- Redis
- Docker
- Strategy engine
- Risk management
- Paper trading
- Realtime architecture foundations

---

## Project Vision

This project is evolving into:

> **Autonomous AI Trading Operating System**

The long-term goal is to build a complete AI-native trading platform capable of:

- Autonomous trading with full lifecycle management
- Conversational strategy management via AI Copilot
- AI-assisted execution
- Multi-broker connectivity
- MetaTrader integration
- Realtime portfolio analytics
- Visual strategy building
- AI copilot trading
- Event-driven execution
- WebSocket realtime architecture

This is **NOT** intended to become:
*"just another trading bot"*

The target architecture is:
**AI Trading Operating System**

---

## Installation & Setup

### 1. Clone Repository

```bash
git clone <your-repository-url>
cd mcp-trading-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Docker Commands

**Build Containers**

```bash
docker-compose build
```

**Start Infrastructure**

```bash
docker-compose up -d
```

**Stop Infrastructure**

```bash
docker-compose down
```

**Full Clean Restart (after code changes)**

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

**View Running Containers**

```bash
docker ps
```

**View Logs**

```bash
docker-compose logs -f app
```

---

## Database Setup

**Export Python Path**

```bash
export PYTHONPATH=$(pwd)
```

**Create Alembic Migration**

```bash
alembic revision --autogenerate -m "initial_tables"
```

**Apply Migrations**

```bash
alembic upgrade head
```

---

## Environment Variables

Create a `.env` file:

```env
# =====================================================
# APP
# =====================================================
APP_NAME=MCP Trading Bot
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
ENABLE_TRADING=false

API_HOST=0.0.0.0
API_PORT=8000

# =====================================================
# DATABASE
# =====================================================
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=trading

DATABASE_URL=postgresql+asyncpg://user:password@db:5432/trading

# =====================================================
# REDIS
# =====================================================
REDIS_HOST=redis
REDIS_PORT=6379

REDIS_URL=redis://redis:6379

# =====================================================
# BINANCE
# =====================================================
BINANCE_API_KEY=YOUR_KEY
BINANCE_SECRET_KEY=YOUR_SECRET

BINANCE_TESTNET=true
PAPER_TRADING=true

# =====================================================
# AI
# =====================================================
DEEPSEEK_API_KEY=YOUR_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

AI_TRADING_ENABLED=true

# =====================================================
# RISK
# =====================================================
MAX_RISK_PER_TRADE=0.01
MAX_DAILY_DRAWDOWN=0.05
MAX_OPEN_POSITIONS=3

# =====================================================
# LOGGING
# =====================================================
LOG_LEVEL=INFO
```

> **DEEPSEEK_MODEL** — use `deepseek-v4-flash` (fast, cheap, no thinking mode).
> Do NOT use `deepseek-v4-pro` (expensive, uses thinking tokens).
> `deepseek-chat` is a valid alias but gets deprecated 2026/07/24.

> **ENABLE_TRADING** — `false` by default so infrastructure boots safely without
> executing trades. Set to `true` to activate the trading bot.

> **DEBUG** — keep `false` in production. When `true`, SQLAlchemy logs every SQL
> query which generates significant noise. SQL echo is hardcoded to `False`
> regardless of this flag.

---

## Application URLs

- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Status:** http://localhost:8000/status
- **Frontend:** http://localhost:3000

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | App info |
| GET | `/health` | Health check |
| GET | `/status` | Trading status + open positions count |
| GET | `/positions/` | List all positions (filterable) |
| GET | `/positions/open` | Open positions only |
| GET | `/positions/{id}` | Single position detail |
| GET | `/positions/{id}/events` | Full audit trail |
| POST | `/positions/{id}/close` | Manual close at given price |
| POST | `/positions/emergency-close` | Emergency close all open positions |
| GET | `/analytics/daily` | Daily performance stats |
| GET | `/analytics/summary` | Portfolio snapshot |
| WS | `/ws/positions` | Realtime position updates |
| WS | `/ws/market` | Realtime price ticks |
| WS | `/ws/system` | System events and emergency alerts |

---

## Current Status

### Phase 1 ✅ — Core Bot (Complete)

Basic async trading pipeline fully operational:

- Connects to Binance
- Fetches live OHLCV market data
- Calculates indicators (EMA, RSI, MACD, ATR, Volatility)
- Runs trading strategies
- Sends signals to DeepSeek AI for validation
- Runs risk validation
- Executes paper trades
- Runs fully async inside Docker infrastructure

```
Binance Market Data
↓
Indicators
↓
Strategy Engine
↓
AI Validation Layer (DeepSeek)
↓
Risk Manager
↓
Execution Engine
↓
Paper Trading
```

### Phase 2 ✅ — Trade Lifecycle & Persistence (Complete)

Production-grade lifecycle and persistence layer now implemented:

- **TradeLifecycleService** — open / close / partial exits with full DB persistence
- **PositionMonitor** — event-driven SL/TP/trailing stop enforcement
- **PnLEngine** — unrealized PnL, realized PnL, MFE/MAE tracking
- **EventBus** — in-process pub/sub + Redis Streams for durable events
- **WebSocket layer** — `/ws/positions`, `/ws/market`, `/ws/system`
- **REST API** — positions, analytics, manual and emergency close
- **MarketDataEngine** — WebSocket candle streaming with in-memory cache
- **Broker reconciliation** — ghost position detection and force-close
- **Full audit trail** — every state change recorded in `trade_events`

```
Binance WebSocket (live candles)
↓
MarketDataEngine (in-memory candle cache + indicators)
↓
CANDLE_CLOSED event → StrategyEngine
↓
Risk Manager (in-memory check — symbol guard + global limits)
↓
AI Validation (DeepSeek deepseek-v4-flash, thinking disabled)
↓
TradeLifecycleService → open_position()
↓
PostgreSQL (positions + trades + trade_events)
↓
PositionMonitor (subscribes to MARKET_TICK events)
↓
SL / TP / Trailing Stop enforcement
↓
TradeLifecycleService → close_position()
↓
EventBus → POSITION_CLOSED → risk_manager.close_trade(symbol)
↓
WebSocket broadcast → Frontend
```

**Database schema:**

```
positions       — aggregated market exposure per symbol
trades          — individual execution fills
trade_events    — complete audit trail (every state change)
daily_metrics   — aggregated daily performance (rollup job pending)
signals         — strategy signal history
metrics         — general metrics store
```

**Bugs fixed post-launch:**

| File | Bug | Fix |
|------|-----|-----|
| `broker/reconciliation.py` | `too many values to unpack` on Binance balance loop | Iterate `balances` as list of dicts, not tuples |
| `trading/trading_bot.py` | `NoneType has no attribute get_latest_price` | Pass `market_engine` directly to fallback in `__init__`, not in `start()` |
| `lifecycle/position_monitor.py` | `object float can't be used in await expression` | `get_latest_price()` is synchronous — removed incorrect `await` |
| `database.py` | SQL echo flooding logs | Hardcoded `echo=False` regardless of DEBUG flag |
| `lifecycle/trade_lifecycle_service.py` | DB write on every price tick | PnL now tracked in-memory; DB flush only every 60 seconds |
| `trading_bot.py` | Fallback polling too aggressive | `interval_seconds` increased from 2s to 10s |
| `trading/risk_manager.py` | Duplicate positions per symbol — risk manager only checked global position count, not per-symbol | Added `_open_symbols: set[str]`; `validate_trade()` rejects if symbol already open |
| `trading/lifecycle/trade_lifecycle_service.py` | `trade_events` flooded with trailing stop entries — one row per cent of price movement | Audit log throttled: only writes `STOP_LOSS_MOVED` event if stop moved ≥ 0.1% |
| `trading/trading_bot.py` | Risk manager `_open_symbols` never cleared on automatic SL/TP close — bot stops opening positions after first auto-close | Subscribe to `POSITION_CLOSED` event; call `risk_manager.close_trade(symbol)` on every close |
| `trading/broker/reconciliation.py` | Reconciliation ran full DB + Binance API cycle every 60s in paper trading — always a no-op | Early return in `run()` when `PAPER_TRADING=true` |
| `trading/strategy_loader.py` | `load_strategies()` called `importlib.reload()` on every candle close regardless of file changes | Cache file `mtime`; skip reload if file unchanged. Hot-reload still works |

---

### Phase 3 ✅ — Frontend Dashboard (Complete)

Production-grade trading dashboard built with Next.js 14, connected to the backend via WebSockets and REST API.

**Stack:**

- Next.js 14 App Router + TypeScript
- Zustand — global state management
- TradingView Lightweight Charts — live candlestick chart
- JetBrains Mono + IBM Plex Mono — terminal aesthetic
- Tailwind CSS — utility styling

**Features:**

- **StatusBar** — live BTC/USDT price, WebSocket status (POS/MKT/SYS), bot running indicator
- **StatsBar** — open positions count, unrealized PnL, realized PnL, total exposure, paper mode indicator
- **PriceChart** — BTC/USDT 1m candlestick chart seeded from Binance public API, updates with live price on every tick
- **PositionsPanel** — real-time position table with live PnL calculated from market feed, flash animations on PnL change, manual close per position
- **EmergencyButton** — double-confirm emergency close all, disabled when no open positions

**WebSocket connections:**

- `/ws/positions` — position lifecycle events + snapshot on connect
- `/ws/market` — live price ticks for PnL calculation
- `/ws/system` — emergency stop alerts

**Architecture:**

```
Browser
↓
usePositions / useMarket / useSystem (hooks)
↓
Zustand store (global state)
↓
StatusBar + StatsBar + PriceChart + PositionsPanel
```

Lives at: `frontend/` — runs as separate Docker service on port 3000.

**Bugs fixed during implementation:**

| File | Bug | Fix |
|------|-----|-----|
| `app/main.py` | CORS blocked all frontend requests | Added `CORSMiddleware` with `allow_origins=["http://localhost:3000"]` |
| `frontend/app/page.tsx` | PriceChart crashed on SSR — `window` not available | Wrapped with `next/dynamic` + `ssr: false` |
| `frontend/components/analytics/StatsBar.tsx` | File had wrong content (PriceChart code) — copy error | Replaced with correct StatsBar implementation |
| `frontend/components/chart/PriceChart.tsx` | Chart rendered white — transparent background not supported | Changed `background.color` from `transparent` to `#080c0f` |

---

## Current Tech Stack

### Backend
- FastAPI + Python 3.12 AsyncIO
- SQLAlchemy Async + AsyncPG
- Alembic migrations
- PostgreSQL 16
- Redis 7
- Docker + Docker Compose
- Structlog (structured JSON logging)

### Frontend
- Next.js 14 App Router + TypeScript
- Zustand (global state)
- TradingView Lightweight Charts
- Tailwind CSS
- JetBrains Mono + IBM Plex Mono

### Trading
- Binance API via CCXT
- Technical indicators via `ta` library
- Event-driven strategy engine
- AI trade validation via DeepSeek
- Risk manager with emergency stop
- Paper trading engine
- Full trade lifecycle with audit trail

### AI
- DeepSeek `deepseek-v4-flash`
- Trade signal validation (BUY / SELL / HOLD)
- Thinking mode explicitly disabled — deterministic fast responses

---

## Performance Notes

The system is optimized to minimize unnecessary I/O:

- **SQL echo disabled** — SQLAlchemy never logs queries in any environment
- **PnL in-memory cache** — unrealized PnL calculated in RAM, flushed to DB every 60s
- **Tick interval** — fallback ticker polls every 10s (not every 2s)
- **Risk checked before AI** — DeepSeek is only called after risk validation passes; already-rejected signals (symbol open, max positions) never reach the AI
- **AI called on signals only** — DeepSeek is never called on HOLD signals or price ticks
- **Trailing stop audit throttled** — `STOP_LOSS_MOVED` events only written when stop moves ≥ 0.1%; DB column still updates on every meaningful move
- **Strategy loader cached** — file `mtime` checked before reimport; no disk I/O on unchanged strategies
- **Reconciliation skipped in paper trading** — `run()` returns instantly when `PAPER_TRADING=true`; no Binance API or DB calls

This keeps DB writes low and logs clean even with many open positions.

---

## Current Project Structure

```
mcp-trading-bot/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
├── .env
│
├── alembic/
│   └── versions/
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── main.py
│   │
│   ├── api/
│   │   └── positions.py                  ← REST endpoints
│   │
│   ├── events/
│   │   └── event_bus.py                  ← EventBus (in-process + Redis Streams)
│   │
│   ├── models/
│   │   ├── trades.py                     ← Position, Trade, enums
│   │   ├── trade_events.py               ← Audit trail
│   │   ├── daily_metrics.py              ← Daily performance
│   │   ├── signals.py
│   │   └── metrics.py
│   │
│   ├── repositories/
│   │   ├── trades_repository.py
│   │   ├── signals_repository.py
│   │   └── metrics_repository.py
│   │
│   ├── services/
│   │   ├── binance_service.py
│   │   ├── nvidia_service.py             ← DeepSeek AI client
│   │   └── websocket_service.py
│   │
│   ├── trading/
│   │   ├── ai_filter.py
│   │   ├── indicators.py
│   │   ├── market_data.py
│   │   ├── risk_manager.py               ← Symbol guard + global limits
│   │   ├── strategy.py                   ← BaseStrategy ABC
│   │   ├── strategy_loader.py            ← mtime cache, hot-reload
│   │   ├── strategy_engine.py
│   │   ├── executor.py
│   │   ├── portfolio.py
│   │   ├── backtesting.py
│   │   ├── trading_bot.py                ← Main orchestrator
│   │   │
│   │   ├── engines/
│   │   │   └── market_data_engine.py     ← WebSocket + candle cache
│   │   │
│   │   ├── lifecycle/
│   │   │   ├── trade_lifecycle_service.py ← PnL cache + trailing stop throttle
│   │   │   ├── position_monitor.py        ← Sync get_latest_price, None guard
│   │   │   └── pnl_engine.py
│   │   │
│   │   └── broker/
│   │       └── reconciliation.py          ← Skips in paper trading
│   │
│   ├── websocket/
│   │   └── manager.py                    ← WS ConnectionManager + endpoints
│   │
│   ├── mcp_server/
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── schemas.py
│   │
│   └── utils/
│       ├── retries.py
│       ├── helpers.py
│       └── validators.py
│
├── frontend/                             ← Next.js 14 dashboard (port 3000)
│   ├── app/
│   │   └── page.tsx
│   ├── components/
│   │   ├── analytics/
│   │   │   └── StatsBar.tsx
│   │   ├── chart/
│   │   │   └── PriceChart.tsx
│   │   ├── positions/
│   │   │   └── PositionsPanel.tsx
│   │   └── ui/
│   │       ├── StatusBar.tsx
│   │       └── EmergencyButton.tsx
│   ├── hooks/
│   │   ├── usePositions.ts
│   │   ├── useMarket.ts
│   │   └── useSystem.ts
│   └── store/
│       └── index.ts                      ← Zustand global store
│
├── strategies/
│   ├── examples/
│   │   └── ema_rsi_strategy.py
│   └── custom/
│       └── my_strategy.py                ← EMA crossover + RSI confluence
│
└── tests/
```

---

## Adding a Custom Strategy

Create a file in `strategies/custom/`:

```python
from app.trading.strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    name = "my_strategy"
    description = "My custom strategy"
    timeframe = "1m"
    stop_loss_percent = 0.02
    take_profit_percent = 0.04
    trailing_stop_percent = 0.01

    async def generate_signal(self, dataframe) -> str:
        latest = dataframe.iloc[-1]
        if latest["ema_20"] > latest["ema_50"] and latest["rsi"] < 70:
            return "BUY"
        if latest["ema_20"] < latest["ema_50"] and latest["rsi"] > 30:
            return "SELL"
        return "HOLD"
```

> **Important:** Strategies should return `HOLD` the vast majority of the time.
> A strategy that signals on every candle calls DeepSeek every minute.
> Use confluence filters (crossover events, RSI zones, multiple conditions) so
> signals are rare and meaningful. The built-in `my_custom_strategy` uses
> EMA crossover events as the primary filter — a cross only happens a few times
> per day, not every candle.

Strategies are hot-loaded when a file changes — no restart required.

---

## Current Trading Mode

```env
PAPER_TRADING=true
BINANCE_TESTNET=true
```

- NO real money
- NO real orders sent to exchange
- Full simulated execution
- Safe for development and testing

---

## IMPORTANT: AI Token Consumption

With `deepseek-v4-flash` and `thinking: disabled`:

- Average: ~150 tokens per validation request
- AI is called ONLY after risk validation passes
- AI is NOT called on HOLD signals, price ticks, or risk-rejected signals
- A well-filtered strategy triggers AI a few times per day, not per candle

This is the correct architecture — AI validates strong signals, it does not run on every market update.

---

### Phase 4 ✅ — Analytics Engine (Complete)

Production-grade analytics engine fully operational.

**Backend:**

- **AnalyticsService** — `app/services/analytics_service.py`
  - `run_daily_rollup(date)` — agrega posiciones cerradas del día en `daily_metrics`
  - `get_equity_curve(days)` — serie diaria de PnL acumulado
  - `get_sharpe_ratio(days)` — Sharpe ratio anualizado (252d, RF=0)
  - `get_max_drawdown(days)` — peak-to-trough sobre equity curve en $ y %
  - `get_ai_performance_metrics()` — win rate global + métricas del AI filter
  - `get_trade_duration_stats()` — avg/min/max duración, desglose por close_reason
  - `catchup_missing_days(days)` — rellena días faltantes al arrancar

- **RollupTask** — `app/tasks/rollup.py`
  - Catchup automático de 30 días al arrancar
  - Loop que ejecuta rollup exactamente a medianoche UTC
  - Asyncio puro — sin Celery ni APScheduler

- **5 endpoints nuevos** en `analytics_router`:
  - `GET /analytics/equity-curve?days=30`
  - `GET /analytics/sharpe?days=30`
  - `GET /analytics/drawdown?days=30`
  - `GET /analytics/trade-stats`
  - `GET /analytics/ai-performance`

**Frontend:**

- **EquityChart** — `frontend/components/analytics/EquityChart.tsx`
  - TradingView Lightweight Charts área bajo la curva
  - Color verde/rojo según PnL acumulado positivo/negativo
  - Responsive con ResizeObserver

- **MetricsPanel** — `frontend/components/analytics/MetricsPanel.tsx`
  - Grid de métricas: Sharpe ratio, Max Drawdown, Win Rate, Total PnL
  - Trades cerrados, duración media, desglose por razón de cierre
  - Sección AI Filter: señales validadas, confianza media

- **useAnalytics hook** — `frontend/hooks/useAnalytics.ts`
  - Fetcha los 5 endpoints en paralelo con Promise.all
  - Polling automático cada 60 segundos

- **Zustand analytics store** — `frontend/store/analytics.ts`
  - Estado tipado: equityCurve, sharpe, drawdown, tradeStats, aiPerformance

- **Tab `[ ANALYTICS ]`** en `frontend/app/page.tsx`
  - Navegación entre `[ TRADING ]` y `[ ANALYTICS ]` sin reload
  - Layout: EquityChart (flex-1) + MetricsPanel (420px)

**Bugs fixed post-launch:**

| File | Bug | Fix |
|------|-----|-----|
| `app/services/analytics_service.py` | `KeyError: 'TradeEvent'` en scripts standalone — modelo no registrado en SQLAlchemy | Agregado `from app.models.trade_events import TradeEvent` al inicio del módulo |
| `frontend/components/analytics/EquityChart.tsx` | Chart renderiza en blanco — `flex-1` sin `minHeight: 0` da altura 0 al ResizeObserver | Agregado `style={{ minHeight: 0 }}` al contenedor del chart y al div padre |
| `alembic` | `DuplicateObject: type "signaltype" already exists` — tablas creadas por `init_db()` antes de correr migraciones | `alembic stamp head` para marcar migración inicial como aplicada sin ejecutarla |

**Verificado en producción:**

# Phase 5 ✅ — Strategy Config Engine (COMPLETE)

## Overview

Production-grade strategy management system. Strategies have been migrated from hardcoded `.py` files to JSON configurations stored in the database, with compilation at runtime. Features a full CRUD REST API with versioning, rollback capabilities, and live enable/disable toggles.

---

## Backend Architecture

### Data Models

#### `StrategyConfig` — `app/models/strategy_config.py`

Core strategy configuration model with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Strategy identifier |
| `timeframe` | String | Trading timeframe (e.g., 1h, 4h, daily) |
| `symbols` | Array | List of trading symbols |
| `stop_loss_pct` | Decimal | Stop loss percentage |
| `take_profit_pct` | Decimal | Take profit percentage |
| `trailing_stop_pct` | Decimal | Trailing stop percentage |
| `indicators` | JSON | Indicator definitions |
| `entry_rules` | JSON | Entry condition rules |
| `exit_rules` | JSON | Exit condition rules |
| `enabled` | Boolean | Default `False` — must be explicitly activated |
| `version` | Integer | Auto-incremented on each save; snapshots in `StrategyVersion` |

#### `StrategyVersion` — `app/models/strategy_config.py`

Append-only versioning model that captures complete configuration snapshots.

- **Foreign Key**: `strategy_configs.id` with `ondelete="CASCADE"`
- **Purpose**: Enables full rollback and version history tracking
- **Usage**: Each update triggers automatic version creation

### Services

#### `StrategyConfigService` — `app/services/strategy_config_service.py`

Handles all strategy configuration operations:

**CRUD Operations:**
- `create(data)` — Create new strategy configuration
- `get(id)` — Retrieve single strategy by ID
- `list()` — List all strategies
- `update(id, data)` — Update configuration (bumps version)
- `delete(id)` — Delete strategy and cascading versions

**Control Operations:**
- `enable(id)` — Activate strategy for live trading
- `disable(id)` — Deactivate strategy
- `rollback(id, target_version)` — Restore previous configuration snapshot, create new version

**Validation:**
- `validate(data)` — Dry-run validation without persistence
  - Returns: `{valid: bool, errors: [str]}`

**Auto-Versioning:**
- Version automatically incremented on each update
- Full configuration snapshot preserved per version

#### `DBStrategyLoader` — `app/trading/db_strategy_loader.py`

Loads and compiles strategies from the database at runtime.

**Key Method:**
- `load_strategies_async()` — Merges file-based strategies (via `StrategyLoader`) with compiled configurations from DB

**Integration:**
- Replaces `StrategyLoader` in `TradingBot`
- Seamless async/await pattern

#### `IndicatorEngine`

Compiles indicator definitions from configuration and applies them to DataFrames at runtime.

---

## REST API — 10 Endpoints

**Base Path**: `/strategies/`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| **GET** | `/strategies/` | List all strategies |
| **POST** | `/strategies/` | Create new strategy |
| **GET** | `/strategies/{id}` | Get strategy by ID |
| **PUT** | `/strategies/{id}` | Update strategy (bumps version) |
| **DELETE** | `/strategies/{id}` | Delete strategy |
| **POST** | `/strategies/{id}/enable` | Activate for live trading |
| **POST** | `/strategies/{id}/disable` | Deactivate |
| **POST** | `/strategies/{id}/rollback` | Restore version: `{target_version: int}` |
| **GET** | `/strategies/{id}/versions` | Get version history |
| **POST** | `/strategies/validate` | Dry-run validation (no save) |

### Response Format

All responses use a consistent envelope:

```json
{
  "data": {},
  "meta": {}
}
```

---

## Backend Patches Applied

### `app/main.py`
- Import `StrategyConfigService` and `strategies_router`
- Initialize service in `lifespan` event
- Register router in application
- Expose `trading_bot` in `app.state` so `emergency_close` endpoint can access live prices from `market_engine`

### `app/trading/trading_bot.py`
- Replace `StrategyLoader` → `DBStrategyLoader`
- Change `load_strategies()` → `await load_strategies_async()`

### `app/trading/indicators.py`
- Add `ema_8` and `ema_13` to `apply_all()` for backward compatibility with `my_custom_strategy.py`

### `app/models/strategy_config.py` (Bug Fix)
- **Issue**: `StrategyVersion.strategy_id` missing explicit `ForeignKey` declaration
  - SQLAlchemy could not resolve the relationship
  - Endpoint returned empty/error responses
- **Fix**: Declare `ForeignKey("strategy_configs.id", ondelete="CASCADE")` correctly
  - Add `ForeignKey` to imports from `sqlalchemy`

---

## Frontend Architecture

### State Management — `store/strategies.ts`

Zustand store with complete type definitions:

**Types:**
- `StrategyConfig`
- `Rule`
- `IndicatorConfig`
- `StrategyVersion`
- `ValidationResult`

**Actions:**
- `setStrategies(strategies)` — Set list of strategies
- `upsertStrategy(strategy)` — Create or update strategy
- `removeStrategy(id)` — Remove strategy from store
- `setSelectedId(id)` — Set currently selected strategy
- `setSaving(bool)` — Toggle saving state
- `setValidating(bool)` — Toggle validation state
- `setValidationResult(result)` — Set validation results
- `setVersions(versions)` — Set version history
- `setVersionsLoading(bool)` — Toggle version loading state

### Hooks — `hooks/useStrategies.ts`

Provides high-level interface to strategy operations:

**Behavior:**
- Fetches strategies on mount
- Polling every 30 seconds

**Exposed Methods:**
- `reload()` — Manual refresh
- `createStrategy(data)` — Create new
- `updateStrategy(id, data)` — Update existing
- `deleteStrategy(id)` — Delete strategy
- `enableStrategy(id)` — Activate
- `disableStrategy(id)` — Deactivate
- `rollbackStrategy(id, targetVersion)` — Restore version
- `validateStrategy(data)` — Dry-run validation
- `loadVersions(id)` — Load version history

### API Client — `lib/api.ts`

Added `api.strategies` object with 10 endpoint methods. Existing methods remain unchanged.

---

## Frontend Components

### `StrategyStatusBadge`

Visual indicator of strategy status:
- **LIVE**: Green dot with glow effect (`shadow-[0_0_6px_#00d4a0]`)
- **OFF**: Dimmed dot with "LIVE/OFF" label

### `StrategyList`

Left panel (320px) displaying all strategies:
- Rows show: name, status badge, version, timeframe
- **[ + NEW STRATEGY ]** button at top
- Empty state with **[ + CREATE FIRST STRATEGY ]** button
- Selected row highlighted with green left border

### `StrategyEditor`

Main editing panel with three modes:

#### Empty Mode
- Displayed when no strategy is selected and no creation in progress

#### View Mode
- **Header**: Strategy name, status badges, metadata chips
- **Action Row**: EDIT / ENABLE-DISABLE / VERSION HISTORY / DELETE buttons
- **Sections** (read-only):
  - Risk Config
  - Indicators
  - Entry Rules
  - Exit Rules
  - Audit trail

#### Edit/Create Mode
- **Basic Fields**: Name, timeframe, symbols
- **Risk Config**: Inputs as percentages (auto-parsed to decimal)
- **Indicators (Dynamic)**:
  - Type selector
  - Period input
  - Column selector
- **Entry Rules (Dynamic)**:
  - Indicator selector
  - Operator selector
  - Conditional fields based on selected operator
- **Exit Rules (Dynamic)**:
  - Same structure as entry rules
  - Toggle to clear rule
- **Action Row**:
  - **[ VALIDATE ]** — Run dry-run validation
  - **[ SAVE / CREATE ]** — Persist to database
  - **[ CANCEL ]** — Discard changes
- **Error Display**: Inline error messages below form

### `VersionHistoryPanel`

Slide-in panel (288px, right side):
- **Layout**: Lists versions newest-first
- **Current Version**: Highlighted in green with "CURRENT" badge
- **Restore Action**: **[ RESTORE ]** button with `window.confirm` before executing rollback

### Page Integration — `app/page.tsx`

**Type Extension**: Added `'strategies'` to page type union
```typescript
type: 'trading' | 'analytics' | 'strategies'
```

**Tab**: New **[ STRATEGIES ]** tab

**Hook Integration**: `useStrategies()` mounted in `WsProviders`

**Layout**:
- `StrategyList` (320px, `border-r`)
- `StrategyEditor` (`flex-1`)

---

## Bug Fixes & Verification

### Fixed Issues

| File | Bug | Fix |
|------|-----|-----|
| `app/models/strategy_config.py` | `StrategyVersion.strategy_id` missing explicit `ForeignKey` declaration; SQLAlchemy couldn't resolve relationship | Declare `ForeignKey("strategy_configs.id", ondelete="CASCADE")` correctly in model |
| `app/trading/lifecycle/position_monitor.py` | Error `'side'` en cada market tick después de cerrar una posición — el guard `if not position` estaba ubicado *después* de `update_unrealized_pnl`, que internamente intentaba reconstruir el cache accediendo a `position.side` de una posición ya cerrada | Mover el guard al inicio de `_process_tick`, antes de cualquier operación; limpiar `_pnl_cache` al detectar posición cerrada; limpiar también en `_on_position_closed` |
| `app/trading/lifecycle/trade_lifecycle_service.py` | `update_unrealized_pnl` reconstruía el cache desde DB para posiciones cerradas o eliminadas, causando el error `'side'` en ticks subsiguientes | Agregar guard de status dentro del bloque de reconstrucción de cache: si `position.status` no es `FILLED` o `PARTIALLY_FILLED`, retornar sin tocar el cache |
| `app/api/positions.py` | `POST /positions/{id}/close` solo devolvía `{"message": "close_requested"}` sin ejecutar ningún cierre real — el endpoint estaba incompleto | Implementar la llamada real a `lifecycle.close_position()` obteniendo el servicio desde `request.app.state`; devolver la posición cerrada completa con PnL calculado |
| `app/api/positions.py` | `POST /positions/emergency-close` igual que el anterior — solo devolvía un status string sin cerrar nada | Implementar llamada real a `lifecycle.emergency_close_all()` con precios en vivo desde `market_engine` cuando está disponible |
| `app/main.py` | `trading_bot` no expuesto en `app.state`, impidiendo que el endpoint de emergency close acceda a precios en vivo | Agregar `app.state.trading_bot = trading_bot` en el lifespan junto a `app.state.lifecycle` |

### Production Verification Checklist

- ✅ Backend logs show `strategy_config_service_initialized` on startup
- ✅ Backend logs show `compiled_strategies_loaded` when loading DB strategies
- ✅ `/strategies/` endpoint responds with proper envelope structure
- ✅ **[ STRATEGIES ]** tab visible in frontend
- ✅ No errors in console when navigating tabs
- ✅ CRUD operations work end-to-end
- ✅ No `'side'` errors in logs after position close
- ✅ `POST /positions/{id}/close` returns closed position with `realized_pnl` and `close_reason: MANUAL`
- ✅ Double-close attempt correctly returns `400 Position is not open`
- ✅ Bot generating signals and opening positions in paper mode
- ✅ All 5 analytics endpoints returning `200`
- ✅ 7 DB tables present with correct schema

---

## Summary

Phase 5 delivers a complete, production-ready strategy management system that:
- ✅ Decouples strategy definitions from application code
- ✅ Enables non-technical users to create and modify strategies
- ✅ Provides full version control and rollback capabilities
- ✅ Integrates seamlessly with existing trading engine
- ✅ Offers polished UI/UX for strategy management

## Roadmap

### Phase 1 ✅ Core Bot
Basic async trading pipeline. Market data → Indicators → Strategy → Risk → AI → Paper trade.
**Status: Complete and verified working.**

### Phase 2 ✅ Trade Lifecycle & Persistence
Production-grade lifecycle and persistence. Positions, fills, audit trail, PnL engine,
SL/TP/trailing stop monitor, EventBus, WebSocket layer, broker reconciliation.
Post-launch bugs fixed and performance optimized.
**Status: Complete and verified working.**

### Phase 3 ✅ Frontend Dashboard
Production-grade Next.js 14 dashboard. Live candlestick chart, real-time positions panel,
WebSocket connections to all three backend streams, emergency close, paper mode indicator.
Post-launch bugs fixed (CORS, SSR crash, copy error, chart background).
**Status: Complete and verified working.**

### Phase 4 ✅ Analytics Engine
Production-grade analytics engine with end-of-day rollup, equity curve, and performance metrics.
Sharpe ratio, max drawdown, trade duration stats, AI filter performance, five new REST endpoints,
EquityChart + MetricsPanel in frontend Analytics tab. RollupTask runs at midnight UTC via asyncio.
Post-launch bugs fixed (TradeEvent registration, EquityChart minHeight, alembic stamp).
**Status: Complete and verified working.**

### Phase 5 ✅ Strategy Config Engine
Strategies migrated from hardcoded .py files to JSON configs stored in DB,
compiled at runtime via IndicatorEngine + rule compiler. Full CRUD REST API
(10 endpoints) with versioning, rollback, enable/disable, and dry-run validation.
DBStrategyLoader merges file + DB strategies on every candle. Frontend Strategies
tab: StrategyList, StrategyEditor (view/edit/create modes), VersionHistoryPanel
slide-in, StrategyStatusBadge. Zustand store + useStrategies hook with 30s polling.
Fix: ForeignKey declaration on StrategyVersion. Status: Complete and verified working.
**Status: Complete and verified working.**

---

## Phase 6 ✅ — AI Copilot / Conversational Trading (Complete)

The main differentiator of the platform. A natural language interface that lets you control the trading bot by typing commands.

### What it does

Type anything. The copilot interprets your intent, calls real backend services, and responds with data or confirmation.

**Example interactions:**

```
> What's my current PnL?
→ AI fetches open positions, calculates unrealized PnL, responds with table

> List all strategies
→ Returns strategy table: name, status, timeframe, SL/TP

> Enable the ema_crossover strategy
→ ⚡ ENABLE STRATEGY ✓ — strategy is now LIVE

> Set stop loss to 1.5% on ema_crossover_db
→ ⚡ UPDATE STRATEGY RISK ✓ — stop_loss_pct updated to 0.015

> Disable all strategies
→ ⚡ DISABLE ALL STRATEGIES ✓ — 3 strategies disabled

> Close all positions
→ AI asks for confirmation first
> Yes, close them
→ ⚡ CLOSE ALL POSITIONS ✓ — 2 positions closed, PnL: -$12.40

> What's the BTC price?
→ BTC/USDT: $67,420.00 (live)

> Show my analytics summary
→ Sharpe: 1.24 | Max DD: -$42.00 (-2.1%) | Win Rate: 58.3%
```

### Architecture

```
Frontend CopilotChat
↓ POST /copilot/chat { message, conversation_history }
↓
CopilotService
↓ DeepSeek function calling (tool_choice=auto)
↓
Tool dispatcher → real services:
  get_portfolio_status    → TradeLifecycleService
  get_analytics_summary   → AnalyticsService
  list_strategies         → StrategyConfigService
  enable/disable_strategy → StrategyConfigService
  update_strategy_risk    → StrategyConfigService
  close_position          → TradeLifecycleService
  close_all_positions     → TradeLifecycleService
  get_market_price        → MarketDataEngine (sync, no await)
↓
Response { response, actions_taken, data }
↓
Frontend renders: text + action badges + data table
```

### New files

**Backend:**
- `app/api/copilot.py` — `POST /copilot/chat` endpoint
- `app/services/copilot_service.py` — AI orchestration + tool dispatcher
- Updated `app/main.py` — CopilotService init + router registration
- `alembic/versions/phase6_copilot_history.py` — optional session log table

**Frontend:**
- `frontend/components/copilot/CopilotChat.tsx` — terminal chat UI
- `frontend/hooks/useCopilot.ts` — send/receive logic
- `frontend/store/copilot.ts` — Zustand message store
- Updated `frontend/app/page.tsx` — `[ COPILOT ]` tab
- Updated `frontend/lib/api.ts` — `api.copilot.chat()`

### Safety rules built in

- Destructive actions (close position, close all, emergency stop) require explicit user confirmation before the AI executes them
- The copilot works in `ENABLE_TRADING=false` mode — read-only queries (PnL, analytics, strategies) always work; action commands return a clear error message
- `get_latest_price()` is called synchronously (no await) as required by MarketDataEngine
- Conversation history capped at last 10 turns to avoid token bloat

### Token cost

Each copilot message: ~200–600 tokens (DeepSeek `deepseek-chat`).
Tool calls add ~100–200 tokens per tool executed.
Typical interaction: 300–800 tokens total.

### Applying the migration (optional)

```bash
alembic upgrade head
```

The copilot works without running this migration. The table is only needed if you want to persist conversation history server-side for future replay/audit features.

### Phase 7 🔲 Multi-Broker Connectivity
Currently only Binance is supported (paper trading mode).

What is needed:
- Broker abstraction layer (common interface for all brokers)
- Bybit connector
- MetaTrader 4 / MetaTrader 5 bridge
- Oanda connector
- Interactive Brokers connector
- Position mirroring across brokers
- Per-broker reconciliation

### Phase 8 🔲 Portfolio Engine
No portfolio-level view exists yet.

What is needed:
- Total exposure tracking across all symbols
- Margin analysis
- Capital allocation per strategy
- Correlation risk between open positions
- Portfolio-level drawdown limits
- Multi-account routing

### Phase 9 🔲 Alerting & Notifications
No notifications implemented yet.

What is needed:
- Telegram bot integration
- Discord webhook alerts
- Email notifications
- Alert rules engine (price alerts, PnL thresholds, drawdown alerts)
- Push notifications (mobile)

### Phase 10 🔲 Strategy Marketplace
Long-term community goal.

What is needed:
- Share strategies between users
- Backtest library
- Strategy performance leaderboard
- AI-rated strategies
- Community strategies

---

## Long-Term Architecture Vision

```
Frontend (Next.js)
↓
Realtime Gateway (WebSockets)
↓
AI Orchestrator / Copilot
↓
Trading Engine
↓
Execution Engine
↓
Broker Connectors
↓
Exchanges / Brokers
```

---

## Future Platform Features

- Voice commands
- Telegram integration
- Discord alerts
- Strategy marketplace
- Replay / backtesting mode
- AI explainability layer
- Portfolio AI
- Multi-account routing
- Copy trading
- Social trading

---

## Current Conclusion

Phases 1, 2, and 3 are complete and verified working in production (Docker).

The system currently:
- Processes real market data via Binance WebSocket streams
- Generates strategy signals on every candle close
- Checks risk first (symbol guard + global limits) before calling AI
- Validates strong signals with DeepSeek AI (`deepseek-v4-flash`, thinking disabled)
- Persists positions, fills, and audit trail to PostgreSQL
- Monitors open positions for SL/TP/trailing stop in real time
- Broadcasts live updates via WebSocket to any connected frontend
- Displays a live trading dashboard (Next.js 14) with real-time chart, positions, PnL, and emergency controls
- Runs fully async inside Docker infrastructure
- Optimized: PnL in-memory, DB writes minimized, trailing stop throttled, reconciliation skipped in paper trading, strategy loader cached
- Agrega métricas diarias en `daily_metrics` vía rollup automático a medianoche UTC
- Calcula Sharpe ratio, max drawdown, equity curve y trade stats via API REST
- Muestra tab `[ ANALYTICS ]` en el frontend con EquityChart y MetricsPanel en tiempo real

**The next milestone is Phase 5 — Runtime Strategy Config System.**
