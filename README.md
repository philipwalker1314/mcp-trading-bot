```python
content = """# MCP Trading Bot

AI-powered autonomous trading infrastructure with:

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

> **Autonomous AI Trading Operating System** > The long-term goal is to build a complete AI-native trading platform capable of:

- Autonomous trading
- Conversational strategy management
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

**Restart Containers**

```bash
docker-compose restart

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
DEEPSEEK_BASE_URL=[https://api.deepseek.com](https://api.deepseek.com)
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

---

## Application URLs

* **API:** [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)
* **Swagger Docs:** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](https://www.google.com/search?q=http://localhost:8000/health)
* **Status:** [http://localhost:8000/status](https://www.google.com/search?q=http://localhost:8000/status)

---

## Current Status

**YES — The bot is already operational.**

The current system successfully:

* Connects to Binance
* Fetches live OHLCV market data
* Calculates indicators
* Runs trading strategies
* Sends signals to AI validation
* Runs risk validation
* Executes paper trades
* Runs fully async inside Docker infrastructure

*The complete pipeline is already functional.*

### Current Trading Pipeline

```text
Binance Market Data
↓
Indicators
↓
Strategy Engine
↓
AI Validation Layer
↓
Risk Manager
↓
Execution Engine
↓
Paper Trading

```

---

## Current Tech Stack

### Backend

* FastAPI
* Python AsyncIO
* SQLAlchemy Async
* Alembic
* PostgreSQL
* Redis
* Docker
* Structlog
* AsyncPG

### Trading

* Binance API
* Technical indicators
* Strategy engine
* Risk management
* Execution engine
* Paper trading engine

### AI

* DeepSeek V4 Flash
* AI trade validation
* AI orchestration layer

---

## Current Project Structure

```text
mcp-trading-bot/
├── Dockerfile
├── README.md
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
├── .env
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── app/
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── main.py
│   │
│   ├── models/
│   │   ├── trades.py
│   │   ├── signals.py
│   │   └── metrics.py
│   │
│   ├── repositories/
│   │   ├── trades_repository.py
│   │   ├── signals_repository.py
│   │   └── metrics_repository.py
│   │
│   ├── services/
│   │   └── nvidia_service.py
│   │
│   ├── trading/
│   │   ├── ai_filter.py
│   │   ├── indicators.py
│   │   ├── market_data.py
│   │   ├── order_executor.py
│   │   ├── risk_manager.py
│   │   ├── strategy.py
│   │   ├── strategy_loader.py
│   │   ├── trading_bot.py
│   │   └── binance_client.py
│   │
│   ├── utils/
│   │   └── retries.py
│   │
│   └── mcp_server/
│
├── strategies/
│   ├── examples/
│   │   └── ema_rsi_strategy.py
│   │
│   └── custom/
│       └── my_strategy.py
│
├── tests/
│
└── venv/

```

---

## Current Features

### Infrastructure

* Dockerized architecture
* PostgreSQL integration
* Redis integration
* Alembic migrations
* Async runtime
* Structured logging
* Async DB sessions
* Environment-based config

### Trading

* Binance OHLCV fetching
* Indicator calculation
* Strategy loading
* Strategy execution
* AI trade validation
* Risk validation
* Paper trading execution
* Async trading loop

### API

* FastAPI endpoints
* Health monitoring
* Status endpoints
* Swagger docs

### Verified Working Features

The following has already been tested successfully:

* Strategy signal generation
* DeepSeek AI responses
* AI validation flow
* Risk approval
* Paper trade execution
* Async trading loops
* Live Binance market data
* FastAPI async runtime
* Docker orchestration
* Database initialization

---

## Current Trading Mode

Current mode:

```env
PAPER_TRADING=true
BINANCE_TESTNET=true

```

This means:

* NO real money
* NO real trades
* Full simulated execution
* Safe testing environment

---

## IMPORTANT: AI Token Consumption

During testing we noticed high token consumption:

* 15 requests
* 2373 tokens

This is **NORMAL** for the current architecture because each request contains:

* System prompt
* Strategy prompt
* Market data
* AI response

Average usage: **~150 tokens/request**

### IMPORTANT ARCHITECTURE DECISION

The final architecture **SHOULD NOT** call AI every few seconds.
Current testing architecture:

```python
while True:
    fetch market
    run strategy
    call AI

```

*This is expensive and inefficient.*

### Correct Future Architecture

AI should **ONLY** intervene when:
A. A valid strategy signal appears
*(Example: EMA crossover ↓ AI validates trade)* -> NOT every market loop.
B. High volatility detected
C. Market regime changes
D. User requests AI assistance
E. Strategy generation

---

## Final Recommended Architecture

### Traditional Strategy Engine

Fast, deterministic, low-cost. Used for:

* Indicators
* Signals
* Technical analysis
* Trade execution

### AI Layer

Used **ONLY** for:

* Validation
* Optimization
* Reasoning
* Chat
* Strategy generation
* Orchestration
* Portfolio intelligence

---

## FUTURE GOAL: NO MORE .PY STRATEGIES

The final system should allow:

* Runtime strategy generation
* AI-generated strategies
* Natural language trading rules
* Visual strategy builders
* Dynamic strategy orchestration
**WITHOUT manually editing `.py` files.**

### AI Copilot Vision

The future platform should support:

* *"Trade BTC only during NY session."*
* *"Risk 1% per trade."*
* *"Close positions after 5 pip drawdown."*
* *"Disable trading during CPI news."*

The AI should translate those instructions into:

* Runtime strategy configs
* Risk policies
* Execution rules
* Trade lifecycle management

---

## PRIORITIES — NEXT IMPLEMENTATION PHASE

### 1. Persist Trades in Database (CRITICAL)

Currently paper trades execute successfully but are NOT persisted.
Need: Open positions, Closed trades, PnL tracking, Trade history, Timestamps, Position lifecycle.

### 2. Open Positions Manager

Need: Stop loss, Take profit, Trailing stop, Active position monitoring, Close logic, Partial exits, Emergency close.

### 3. Frontend Realtime Platform

Need: WebSockets, Live positions, Trading dashboard, AI panel, Realtime charts, Notifications.

### 4. Trade Lifecycle Engine

Need: Trade monitoring, Position updates, Realized PnL, Unrealized PnL, Position management, Smart exits.

### 5. Runtime Strategy Config System

Goal: Eliminate hardcoded `.py` strategies, Runtime strategy generation, AI-generated rules, Strategy marketplace, Visual strategy builder.

### 6. Broker Connectors

Need support for: Binance, Bybit, MetaTrader 4, MetaTrader 5, Oanda, Interactive Brokers, Paper trading brokers.

### 7. WebSocket Market Data (VERY IMPORTANT)

Current architecture uses polling.
Need: Live streaming candles, Tick data, Low latency processing, Event-driven execution.

### 8. Portfolio Engine

Need: Exposure tracking, Risk aggregation, Margin analysis, Portfolio allocation, Capital management.

### 9. Analytics Engine

Need: Winrate, Sharpe ratio, Drawdown, Profit factor, Trade analytics, AI performance metrics.

### 10. AI Copilot / Conversational Trading

This is the MAIN differentiator.
Goal:
User talks to the platform ↓ AI interprets intent ↓ AI configures trading engine ↓ Bot operates autonomously

---

## MetaTrader Integration Vision

Future support should include:

* MetaTrader 4
* MetaTrader 5
* Live broker synchronization
* Position mirroring
* MT charts
* MT order execution
* MT expert advisor bridge

---

## Planned Frontend Architecture

The frontend should evolve into:
**AI Trading Operating System**
NOT just: *"another trading bot UI."*

### Planned Frontend Modules

**Trading Dashboard**

* Open trades
* Closed trades
* Live PnL
* Position controls
* Close buttons
* Emergency close all

**Open Positions Panel**

* Active positions
* Historical trades
* Position filters
* Realtime updates
* Close individual trade
* Close all trades

**AI Chatbox**

* Goal: User writes instructions ↓ AI translates intent ↓ Runtime trading configs ↓ Bot updates behavior automatically
* Examples: Trade only during London session, Risk 1% per trade, Close positions after 5 pip drawdown, Avoid CPI volatility.

**MetaTrader-style Charts**

* Realtime candles
* Drawing tools
* Indicators
* Multi-pair watchlists
* Live trade overlays
* TradingView integration

**Analytics**

* Performance metrics
* Risk analysis
* Portfolio insights
* AI analytics
* Trade history

### Planned Frontend Stack

Recommended: Next.js, React, TypeScript, TailwindCSS, Zustand, TanStack Query, TradingView Charts, WebSockets, ShadCN UI.

### Long-Term Architecture Vision

```text
Frontend (Next.js)
↓
Realtime Gateway (WebSockets)
↓
AI Orchestrator
↓
Trading Engine
↓
Execution Engine
↓
Broker Connectors
↓
Exchanges/Brokers

```

---

## Future Platform Features

Potential future implementations:

* Voice commands
* Telegram integration
* Discord alerts
* Strategy marketplace
* Replay mode
* AI explainability
* Portfolio AI
* Multi-account routing
* Copy trading
* Social trading

---

## Current Conclusion

The most important milestone has already been achieved:
**YES — the bot truly works.**

The current engine already:

* Processes real market data
* Generates strategy signals
* Uses live AI validation
* Executes paper trades
* Runs fully async
* Uses Docker infrastructure
* Uses PostgreSQL + Redis

The next phase is transforming the engine into a complete AI trading platform.
"""

with open("README.md", "w", encoding="utf-8") as f:
f.write(content)

```
Tu archivo MD está listo.
[file-tag: code-generated-file-0-1778820461157704110]

Aquí tienes el archivo `README.md` generado con todo el contenido del proyecto estructurado correctamente para que puedas guardarlo directamente en tu repositorio.

```
