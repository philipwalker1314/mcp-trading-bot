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

> If tables already exist (created by `init_db()` on first boot), stamp the current
> revision without running SQL:
> ```bash
> alembic stamp head
> ```

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
DEEPSEEK_MODEL=deepseek-chat

AI_TRADING_ENABLED=false

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

> **DEEPSEEK_MODEL** — use `deepseek-chat` (fast, cheap).
> `deepseek-v4-flash` is a valid alias but deprecated 2026/07/24.
> Do NOT use `deepseek-v4-pro` (expensive, uses thinking tokens).

> **ENABLE_TRADING** — `false` by default so infrastructure boots safely without
> executing trades. Set to `true` to activate the trading bot.

> **AI_TRADING_ENABLED** — controls whether DeepSeek is called for signal validation.
> Can also be toggled at runtime from the frontend without restarting (Phase 7).
> When `false`, the AI filter echoes the strategy signal directly (mock mode).

> **DEBUG** — keep `false` in production. SQL echo is hardcoded to `False`
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
| GET | `/health` | Health check (includes `ai_trading_enabled`) |
| GET | `/status` | Trading status + open positions count |
| GET | `/positions/` | List all positions (filterable) |
| GET | `/positions/open` | Open positions only |
| GET | `/positions/{id}` | Single position detail |
| GET | `/positions/{id}/events` | Full audit trail |
| POST | `/positions/{id}/close` | Manual close at given price |
| POST | `/positions/emergency-close` | Emergency close all open positions |
| GET | `/analytics/daily` | Daily performance stats |
| GET | `/analytics/summary` | Portfolio snapshot |
| GET | `/analytics/equity-curve` | Equity curve (30d default) |
| GET | `/analytics/sharpe` | Sharpe ratio anualizado |
| GET | `/analytics/drawdown` | Max drawdown |
| GET | `/analytics/trade-stats` | Trade duration stats |
| GET | `/analytics/ai-performance` | AI filter performance metrics |
| GET | `/strategies/` | List all strategy configs |
| POST | `/strategies/` | Create new strategy |
| GET | `/strategies/{id}` | Get strategy by ID |
| PUT | `/strategies/{id}` | Update strategy (bumps version) |
| DELETE | `/strategies/{id}` | Delete strategy |
| POST | `/strategies/{id}/enable` | Activate strategy for live trading |
| POST | `/strategies/{id}/disable` | Deactivate strategy |
| POST | `/strategies/{id}/rollback` | Rollback to a previous version |
| GET | `/strategies/{id}/versions` | Version history |
| POST | `/strategies/validate` | Dry-run validation (no save) |
| POST | `/copilot/chat` | AI Copilot natural language interface |
| GET | `/ai-metrics/` | AI filter session stats + token usage |
| POST | `/ai-metrics/reset` | Reset session counters |
| GET | `/ai-trading/status` | Current AI on/off state |
| POST | `/ai-trading/toggle` | Toggle AI on/off at runtime (no restart) |
| POST | `/ai-trading/enable` | Enable AI trading |
| POST | `/ai-trading/disable` | Disable AI trading |
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

---

### Phase 2 ✅ — Trade Lifecycle & Persistence (Complete)

Production-grade lifecycle and persistence layer:

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
AI Validation (DeepSeek deepseek-chat, selective — Phase 7)
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
positions         — aggregated market exposure per symbol
trades            — individual execution fills
trade_events      — complete audit trail (every state change)
daily_metrics     — aggregated daily performance
signals           — strategy signal history
metrics           — general metrics store
strategy_configs  — JSON strategy configurations (Phase 5)
strategy_versions — immutable version snapshots (Phase 5)
copilot_sessions  — optional copilot history log (Phase 6)
```

**Bugs fixed:**

| File | Bug | Fix |
|------|-----|-----|
| `broker/reconciliation.py` | `too many values to unpack` on Binance balance loop | Iterate `balances` as list of dicts |
| `trading/trading_bot.py` | `NoneType has no attribute get_latest_price` | Pass `market_engine` in `__init__`, not `start()` |
| `lifecycle/position_monitor.py` | `object float can't be used in await expression` | `get_latest_price()` is synchronous — removed `await` |
| `database.py` | SQL echo flooding logs | Hardcoded `echo=False` |
| `lifecycle/trade_lifecycle_service.py` | DB write on every price tick | PnL in-memory; DB flush every 60s |
| `trading_bot.py` | Fallback polling too aggressive | `interval_seconds` increased to 10s |
| `trading/risk_manager.py` | Duplicate positions per symbol | Added `_open_symbols: set[str]` |
| `lifecycle/trade_lifecycle_service.py` | `trade_events` flooded with trailing stop entries | Throttled: only writes if stop moved ≥ 0.1% |
| `trading/trading_bot.py` | `_open_symbols` never cleared on auto SL/TP close | Subscribe to `POSITION_CLOSED`; call `risk_manager.close_trade(symbol)` |
| `trading/broker/reconciliation.py` | Reconciliation ran full cycle every 60s in paper trading | Early return when `PAPER_TRADING=true` |
| `trading/strategy_loader.py` | `importlib.reload()` on every candle regardless of changes | Cache file `mtime`; skip if unchanged |

---

### Phase 3 ✅ — Frontend Dashboard (Complete)

Production-grade trading dashboard built with Next.js 14:

**Stack:**
- Next.js 14 App Router + TypeScript
- Zustand — global state management
- TradingView Lightweight Charts — live candlestick chart
- JetBrains Mono + IBM Plex Mono — terminal aesthetic
- Tailwind CSS — utility styling

**Features:**
- **StatusBar** — live BTC/USDT price, WebSocket status (POS/MKT/SYS), bot running indicator, AI ON/OFF toggle button (Phase 7)
- **StatsBar** — open positions count, unrealized PnL, realized PnL, total exposure, paper mode indicator
- **PriceChart** — BTC/USDT 1m candlestick chart seeded from Binance public API, updates on every tick
- **PositionsPanel** — real-time position table with live PnL, flash animations on change, manual close per position
- **EmergencyButton** — double-confirm emergency close all, disabled when no open positions

**WebSocket connections:**
- `/ws/positions` — position lifecycle events + snapshot on connect
- `/ws/market` — live price ticks for PnL calculation
- `/ws/system` — emergency stop alerts

**Bugs fixed:**

| File | Bug | Fix |
|------|-----|-----|
| `app/main.py` | CORS blocked all frontend requests | Added `CORSMiddleware` |
| `frontend/app/page.tsx` | PriceChart crashed on SSR | Wrapped with `next/dynamic` + `ssr: false` |
| `frontend/components/analytics/StatsBar.tsx` | Wrong content (copy error) | Replaced with correct implementation |
| `frontend/components/chart/PriceChart.tsx` | Chart rendered white | `background.color` changed from `transparent` to `#080c0f` |

---

### Phase 4 ✅ — Analytics Engine (Complete)

Production-grade analytics engine:

**Backend:**
- **AnalyticsService** — `app/services/analytics_service.py`
  - `run_daily_rollup(date)` — aggregates closed positions into `daily_metrics`
  - `get_equity_curve(days)` — daily PnL series
  - `get_sharpe_ratio(days)` — annualized Sharpe (252d, RF=0)
  - `get_max_drawdown(days)` — peak-to-trough on equity curve
  - `get_ai_performance_metrics()` — global win rate + AI filter metrics
  - `get_trade_duration_stats()` — avg/min/max duration by close reason
  - `catchup_missing_days(days)` — fills missing days on startup

- **RollupTask** — `app/tasks/rollup.py`
  - Auto catchup 30 days on startup
  - Loop executes rollup at midnight UTC
  - Pure asyncio — no Celery or APScheduler

- **5 new endpoints** in `analytics_router`:
  - `GET /analytics/equity-curve?days=30`
  - `GET /analytics/sharpe?days=30`
  - `GET /analytics/drawdown?days=30`
  - `GET /analytics/trade-stats`
  - `GET /analytics/ai-performance`

**Frontend:**
- **EquityChart** — TradingView area chart, green/red based on cumulative PnL, responsive with ResizeObserver
- **MetricsPanel** — Sharpe ratio, max drawdown, win rate, total PnL, trade count, avg duration, AI filter section
- **useAnalytics hook** — fetches all 5 endpoints in parallel with `Promise.all`, polls every 60s
- **`[ ANALYTICS ]` tab** in `page.tsx`

**Bugs fixed:**

| File | Bug | Fix |
|------|-----|-----|
| `analytics_service.py` | `KeyError: 'TradeEvent'` — model not registered in SQLAlchemy | Added `from app.models.trade_events import TradeEvent` |
| `EquityChart.tsx` | Chart renders blank — `flex-1` without `minHeight: 0` | Added `style={{ minHeight: 0 }}` |
| `alembic` | `DuplicateObject: type "signaltype" already exists` | `alembic stamp head` to mark migration as applied |

---

### Phase 5 ✅ — Strategy Config Engine (Complete)

Strategies migrated from hardcoded `.py` files to JSON configurations stored in DB, compiled at runtime.

**Backend:**

- **`StrategyConfig`** model — JSON strategy stored in DB with versioning

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Strategy identifier |
| `timeframe` | String | Trading timeframe |
| `symbols` | Array | List of trading symbols |
| `stop_loss_pct` | Float | Stop loss percentage |
| `take_profit_pct` | Float | Take profit percentage |
| `trailing_stop_pct` | Float | Trailing stop percentage |
| `indicators` | JSON | Indicator definitions |
| `entry_rules` | JSON | Entry condition rules |
| `exit_rules` | JSON | Exit condition rules |
| `enabled` | Boolean | Default `False` |
| `version` | Integer | Auto-incremented on each save |
| `ai_validation_required` | Boolean | Default `True` (Phase 7) |
| `confidence_threshold` | Float | Default `0.75` (Phase 7) |

- **`StrategyVersion`** — immutable append-only version snapshots with `CASCADE` delete
- **`RuntimeStrategyCompiler`** — compiles JSON rule trees into live `BaseStrategy` instances
- **`IndicatorEngine`** — applies indicator configs to DataFrames at runtime
- **`RuleEvaluator`** — evaluates rules (`gt`, `lt`, `between`, `crosses_above`, `crosses_below`, etc.)
- **`DBStrategyLoader`** — merges file-based + DB strategies on every candle
- **`StrategyConfigService`** — full CRUD + versioning + rollback + dry-run validation

**10 REST endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/strategies/` | List all |
| POST | `/strategies/` | Create |
| GET | `/strategies/{id}` | Get |
| PUT | `/strategies/{id}` | Update (bumps version) |
| DELETE | `/strategies/{id}` | Delete |
| POST | `/strategies/{id}/enable` | Activate |
| POST | `/strategies/{id}/disable` | Deactivate |
| POST | `/strategies/{id}/rollback` | Restore version |
| GET | `/strategies/{id}/versions` | Version history |
| POST | `/strategies/validate` | Dry-run (no save) |

**Frontend:**
- **`StrategyList`** — left panel (320px), name + status badge + version + timeframe
- **`StrategyEditor`** — view / edit / create modes with dynamic indicator and rule builders
- **`VersionHistoryPanel`** — slide-in panel with restore button and `window.confirm`
- **`StrategyStatusBadge`** — green glow dot (LIVE) / dim dot (OFF)
- **`[ STRATEGIES ]` tab** in `page.tsx`

**Bugs fixed:**

| File | Bug | Fix |
|------|-----|-----|
| `strategy_config.py` | `StrategyVersion.strategy_id` missing `ForeignKey` | Declared correctly with `ondelete="CASCADE"` |
| `position_monitor.py` | `'side'` error on tick after close — guard after `update_unrealized_pnl` | Move guard to start of `_process_tick` |
| `trade_lifecycle_service.py` | Cache rebuilt for closed positions, causing `'side'` KeyError | Guard by status before rebuilding cache |
| `positions.py` | `POST /positions/{id}/close` returned stub, didn't close | Implemented real `lifecycle.close_position()` call |
| `positions.py` | `POST /positions/emergency-close` same stub issue | Implemented real `lifecycle.emergency_close_all()` |
| `main.py` | `trading_bot` not in `app.state` | Added `app.state.trading_bot = trading_bot` |

---

### Phase 6 ✅ — AI Copilot / Conversational Trading (Complete)

Natural language interface to control the entire trading bot by typing commands.

**What it does:**

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

**Architecture:**

```
Frontend CopilotChat
↓ POST /copilot/chat { message, conversation_history }
↓
CopilotService
↓ DeepSeek function calling (tool_choice=auto)
↓
Tool dispatcher → real services:
  get_portfolio_status     → TradeLifecycleService
  get_analytics_summary    → AnalyticsService
  get_daily_stats          → AnalyticsService
  list_strategies          → StrategyConfigService
  enable_strategy          → StrategyConfigService
  disable_strategy         → StrategyConfigService
  disable_all_strategies   → StrategyConfigService
  update_strategy_risk     → StrategyConfigService
  close_position           → TradeLifecycleService
  close_all_positions      → TradeLifecycleService
  get_market_price         → MarketDataEngine (sync, no await)
↓
Response { response, actions_taken, data }
↓
Frontend renders: text + action badges + data table
```

**Available copilot tools:**

| Tool | What it does |
|------|-------------|
| `get_portfolio_status` | Open positions, unrealized/realized PnL, exposure |
| `get_analytics_summary` | Sharpe, drawdown, win rate, total PnL |
| `get_daily_stats` | Today's trade count, durations, close reasons |
| `list_strategies` | All strategies with status, version, risk params |
| `enable_strategy` | Activate a strategy by name or ID |
| `disable_strategy` | Deactivate a strategy by name or ID |
| `disable_all_strategies` | Deactivate all enabled strategies at once |
| `update_strategy_risk` | Update SL/TP/trailing on a strategy |
| `close_position` | Close a specific position (requires confirm) |
| `close_all_positions` | Emergency close all (requires confirm) |
| `get_market_price` | Live price for any symbol |

> **Note:** The copilot can modify and manage existing strategies but cannot
> create new strategies from scratch — that requires the Strategies tab UI or
> the REST API. Creating strategies via natural language is planned for a future phase.

**Safety rules:**
- Destructive actions require explicit user confirmation in conversation before executing
- Works in `ENABLE_TRADING=false` — read-only queries always work; action commands return clear error
- Conversation history capped at last 10 turns to avoid token bloat

**Token cost:**
- Each message: ~200–600 tokens
- Tool calls: ~100–200 tokens per tool
- Typical interaction: 300–800 tokens total

**New files:**
- `app/api/copilot.py` — `POST /copilot/chat` endpoint
- `app/services/copilot_service.py` — AI orchestration + tool dispatcher
- `alembic/versions/phase6_copilot_history.py` — optional session log table
- `frontend/components/copilot/CopilotChat.tsx` — terminal chat UI
- `frontend/hooks/useCopilot.ts` — send/receive + loading state
- `frontend/store/copilot.ts` — Zustand message store
- Updated `frontend/lib/api.ts` — `api.copilot.chat()`

---

### Phase 7 ✅ — Selective AI Filter + Runtime Controls (Complete)

Reduces unnecessary AI calls by scoring signal quality before deciding whether to call DeepSeek. Strong signals execute directly; weak signals go through AI validation.

**The problem with always calling AI:**
- ~2s latency on every signal regardless of quality
- Token consumption on obvious strong signals
- Full external service dependency on every execution

**Signal Strength Evaluator:**

Each signal is scored 0.0–1.0 based on indicator confluence:

| Component | Score |
|-----------|-------|
| EMA 8/13 crossover event (primary signal) | +0.30 |
| EMA 20/50 macro trend alignment | +0.15 |
| RSI in confluence zone | +0.15 |
| MACD momentum confirmation | +0.15 |
| Low volatility | +0.10 |
| Price above/below key EMA structure | +0.10 |
| RSI not at extremes | +0.05 |

**Decision logic per signal:**

```
strategy signal generated
↓
risk check (cheap, in-memory)
↓
signal strength evaluated (0.0–1.0)
↓
if ai_validation_required = False  → execute directly (AI disabled for this strategy)
if strength >= confidence_threshold → execute directly (strong signal, AI skipped)
if strength <  confidence_threshold → call DeepSeek AI (weak/uncertain signal)
```

**Per-strategy AI config (new fields in `strategy_configs`):**

| Field | Default | Description |
|-------|---------|-------------|
| `ai_validation_required` | `true` | Set `false` to skip AI entirely for this strategy |
| `confidence_threshold` | `0.75` | Signals above this strength skip AI |

**Expected impact:**

```
BEFORE (Phase 6):
  15 signals/day → 15 AI calls → ~2250 tokens → always 2s latency

AFTER (Phase 7):
  15 signals/day → ~6 AI calls → ~900 tokens → strong signals <100ms latency
```

**Runtime AI toggle (no restart needed):**

```bash
# Check state
GET /ai-trading/status

# Toggle on/off
POST /ai-trading/toggle

# Explicit control
POST /ai-trading/enable
POST /ai-trading/disable
```

The **AI ON / AI OFF** button in the StatusBar does the same with one click.
State is in-memory — resets to `.env` value on container restart.
When OFF: `AIFilter` echoes the strategy signal directly (mock mode, 0 tokens).

**AI Monitor tab (`[ AI MONITOR ]`):**

- Skip rate — % of signals that bypassed AI this session
- Tokens consumed + estimated cost
- AI decisions breakdown (BUY / SELL / HOLD counts)
- Rolling feed of last 20 signals with strength bar and outcome
- Right panel: per-strategy confidence threshold configuration

**New files:**
- `app/trading/signal_strength_evaluator.py` — scores signal quality 0.0–1.0
- `app/trading/ai_token_tracker.py` — in-memory session usage tracker (singleton)
- `app/api/ai_metrics.py` — `GET /ai-metrics/`, `POST /ai-metrics/reset`
- `app/api/ai_toggle.py` — `GET/POST /ai-trading/status|toggle|enable|disable`
- `alembic/versions/phase7_ai_filter_selective.py` — migration for two new columns
- `frontend/store/ai_metrics.ts` — Zustand store
- `frontend/hooks/useAIMetrics.ts` — polling hook (every 10s)
- `frontend/components/ai/AITokenMonitor.tsx` — monitor panel

**Modified files:**
- `app/models/strategy_config.py` — `ai_validation_required`, `confidence_threshold`
- `app/trading/trading_bot.py` — selective AI logic in `_on_candle_closed`
- `app/main.py` — registers `ai_metrics_router` and `ai_toggle_router`
- `frontend/app/page.tsx` — `[ AI MONITOR ]` tab
- `frontend/components/system/StatusBar.tsx` — AI ON/OFF toggle button

---

## Roadmap

### Phase 8 🔲 — Multi-Broker Connectivity

Currently only Binance is supported (paper trading mode).

What is needed:
- Broker abstraction layer (common interface for all brokers)
- Bybit connector
- MetaTrader 4 / MetaTrader 5 bridge
- Oanda connector
- Interactive Brokers connector
- Position mirroring across brokers
- Per-broker reconciliation

### Phase 9 🔲 — Portfolio Engine

No portfolio-level view exists yet.

What is needed:
- Total exposure tracking across all symbols
- Margin analysis
- Capital allocation per strategy
- Correlation risk between open positions
- Portfolio-level drawdown limits
- Multi-account routing

### Phase 10 🔲 — Alerting & Notifications

No notifications implemented yet.

What is needed:
- Telegram bot integration
- Discord webhook alerts
- Email notifications
- Alert rules engine (price alerts, PnL thresholds, drawdown alerts)
- Push notifications (mobile)

### Phase 11 🔲 — Strategy Marketplace

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
- Strategy creation via Copilot (natural language → JSON config → DB)

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
- AI trade validation via DeepSeek (selective — Phase 7)
- Risk manager with emergency stop
- Paper trading engine
- Full trade lifecycle with audit trail

### AI
- DeepSeek `deepseek-chat`
- Trade signal validation (BUY / SELL / HOLD)
- Function calling for Copilot (11 tools)
- Selective invocation based on signal strength score
- Runtime on/off toggle without restart

---

## Performance Notes

- **SQL echo disabled** — SQLAlchemy never logs queries in any environment
- **PnL in-memory cache** — unrealized PnL calculated in RAM, flushed to DB every 60s
- **Tick interval** — fallback ticker polls every 10s (not every 2s)
- **Risk checked before AI** — DeepSeek only called after risk validation passes
- **Signal strength evaluated before AI** — strong signals (≥ threshold) skip AI entirely
- **AI callable on/off at runtime** — no restart needed, state survives until container restart
- **Trailing stop audit throttled** — events only written when stop moves ≥ 0.1%
- **Strategy loader cached** — file `mtime` checked before reimport; hot-reload still works
- **Reconciliation skipped in paper trading** — instant no-op when `PAPER_TRADING=true`

---

## AI Token Consumption

| Scenario | Tokens/day (est.) |
|----------|-------------------|
| Phase 6 — all signals through AI | ~2250 |
| Phase 7 — selective (60% strong) | ~900 (−60%) |
| AI disabled via toggle | 0 |

Average per AI call: ~150 tokens (signal validation).
Average per Copilot interaction: ~300–800 tokens.

---

## Adding a Custom Strategy (file-based)

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

Strategies are hot-loaded when a file changes — no restart required.

> **Important:** Strategies should return `HOLD` the vast majority of the time.
> Use confluence filters (crossover events, RSI zones, multiple conditions) so
> signals are rare and meaningful. The built-in `my_custom_strategy` uses
> EMA 8/13 crossover events — a cross only happens a few times per day.

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
│       ├── 5b740c8edfd8_initial_tables.py
│       ├── phase5_strategy_configs.py
│       ├── phase6_copilot_history.py
│       └── phase7_ai_filter_selective.py
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── positions.py               ← REST endpoints (positions + analytics)
│   │   ├── strategies.py              ← Strategy CRUD (Phase 5)
│   │   ├── copilot.py                 ← Copilot chat (Phase 6)
│   │   ├── ai_metrics.py              ← Token usage metrics (Phase 7)
│   │   └── ai_toggle.py               ← Runtime AI on/off (Phase 7)
│   │
│   ├── events/
│   │   └── event_bus.py               ← EventBus (in-process + Redis Streams)
│   │
│   ├── models/
│   │   ├── trades.py                  ← Position, Trade, enums
│   │   ├── trade_events.py            ← Audit trail
│   │   ├── daily_metrics.py           ← Daily performance
│   │   ├── signals.py
│   │   ├── metrics.py
│   │   └── strategy_config.py         ← Phase 5 + Phase 7 fields
│   │
│   ├── repositories/
│   │   ├── trades_repository.py
│   │   ├── signals_repository.py
│   │   └── metrics_repository.py
│   │
│   ├── services/
│   │   ├── binance_service.py
│   │   ├── nvidia_service.py          ← DeepSeek AI client
│   │   ├── websocket_service.py
│   │   ├── analytics_service.py       ← Phase 4
│   │   ├── strategy_config_service.py ← Phase 5
│   │   └── copilot_service.py         ← Phase 6
│   │
│   ├── tasks/
│   │   └── rollup.py                  ← Midnight UTC rollup (Phase 4)
│   │
│   ├── trading/
│   │   ├── ai_filter.py
│   │   ├── ai_token_tracker.py        ← Phase 7
│   │   ├── signal_strength_evaluator.py ← Phase 7
│   │   ├── indicators.py
│   │   ├── market_data.py
│   │   ├── risk_manager.py            ← Symbol guard + global limits
│   │   ├── strategy.py                ← BaseStrategy ABC
│   │   ├── strategy_loader.py         ← mtime cache, hot-reload
│   │   ├── strategy_compiler.py       ← RuntimeStrategyCompiler (Phase 5)
│   │   ├── db_strategy_loader.py      ← File + DB merge (Phase 5)
│   │   ├── strategy_engine.py
│   │   ├── trading_bot.py             ← Main orchestrator + selective AI (Phase 7)
│   │   ├── executor.py
│   │   ├── portfolio.py
│   │   ├── backtesting.py
│   │   │
│   │   ├── engines/
│   │   │   └── market_data_engine.py  ← WebSocket + candle cache
│   │   │
│   │   ├── lifecycle/
│   │   │   ├── trade_lifecycle_service.py
│   │   │   ├── position_monitor.py
│   │   │   └── pnl_engine.py
│   │   │
│   │   └── broker/
│   │       └── reconciliation.py      ← Skips in paper trading
│   │
│   ├── websocket/
│   │   └── manager.py                 ← WS ConnectionManager + endpoints
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
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx                   ← All tabs (Phase 7: AI Monitor added)
│   ├── components/
│   │   ├── ai/
│   │   │   └── AITokenMonitor.tsx     ← Phase 7
│   │   ├── analytics/
│   │   │   ├── StatsBar.tsx
│   │   │   ├── EquityChart.tsx        ← Phase 4
│   │   │   └── MetricsPanel.tsx       ← Phase 4
│   │   ├── chart/
│   │   │   └── PriceChart.tsx
│   │   ├── copilot/
│   │   │   └── CopilotChat.tsx        ← Phase 6
│   │   ├── positions/
│   │   │   ├── PositionsPanel.tsx
│   │   │   ├── PositionRow.tsx
│   │   │   └── EmergencyButton.tsx
│   │   ├── strategies/
│   │   │   ├── StrategyList.tsx       ← Phase 5
│   │   │   ├── StrategyEditor.tsx     ← Phase 5
│   │   │   ├── StrategyStatusBadge.tsx ← Phase 5
│   │   │   └── VersionHistoryPanel.tsx ← Phase 5
│   │   └── system/
│   │       └── StatusBar.tsx          ← Phase 7: AI ON/OFF button
│   ├── hooks/
│   │   ├── usePositions.ts
│   │   ├── useMarket.ts
│   │   ├── useSystem.ts
│   │   ├── useAnalytics.ts            ← Phase 4
│   │   ├── useStrategies.ts           ← Phase 5
│   │   ├── useCopilot.ts              ← Phase 6
│   │   └── useAIMetrics.ts            ← Phase 7
│   ├── store/
│   │   ├── trading.ts
│   │   ├── analytics.ts               ← Phase 4
│   │   ├── strategies.ts              ← Phase 5
│   │   ├── copilot.ts                 ← Phase 6
│   │   └── ai_metrics.ts              ← Phase 7
│   └── lib/
│       └── api.ts                     ← REST client (all phases)
│
├── strategies/
│   ├── examples/
│   │   └── ema_rsi_strategy.py
│   └── custom/
│       └── my_strategy.py             ← EMA 8/13 crossover + RSI confluence
│
└── tests/
```
