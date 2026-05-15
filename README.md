# MCP Trading Bot

## Overview

MCP Trading Bot is an enterprise-grade AI trading platform built with:

* FastAPI
* PostgreSQL
* Redis
* Docker
* SQLAlchemy Async
* Binance API
* NVIDIA AI Models
* MCP (Model Context Protocol)
* Strategy Engine
* AI Signal Validation
* Risk Management System
* Real-time Trading Infrastructure

The project is designed to evolve into a fully autonomous AI-powered trading platform with:

* conversational AI control
* live dashboards
* strategy generation via prompts
* portfolio analytics
* backtesting
* live/paper trading
* multi-strategy orchestration
* multi-exchange support

---

# Current Architecture

```text
Frontend Dashboard (future)
        ↓
FastAPI Backend
        ↓
Trading Engine
        ↓
Strategies
        ↓
AI Filter (NVIDIA)
        ↓
Risk Manager
        ↓
Executor
        ↓
Binance API
```

---

# Current Features

## Infrastructure

* Dockerized stack
* Async Python architecture
* PostgreSQL persistence
* Redis support
* Alembic migrations
* Structured logging
* Async lifecycle management

---

## Trading Engine

* Strategy loader
* Multi-strategy execution
* Technical indicators
* Risk validation
* Trade execution pipeline
* Paper trading support
* Binance integration
* AI validation layer

---

## AI Integration

Integrated with NVIDIA AI models through:

* NVIDIA Build Platform
* OpenAI-compatible API interface

Current AI responsibilities:

* signal validation
* trade filtering
* risk-aware decision support

Future responsibilities:

* strategy generation
* autonomous optimization
* conversational trading control
* market analysis
* portfolio optimization

---

# Current Project Structure

```text
mcp-trading-bot/
│
├── alembic/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── trading/
│   ├── mcp_server/
│   └── utils/
│
├── strategies/
│   ├── custom/
│   ├── examples/
│   └── templates/
│
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Current Trading Flow

```text
Binance Market Data
        ↓
Indicators Engine
        ↓
Trading Strategy
        ↓
NVIDIA AI Filter
        ↓
Risk Manager
        ↓
Executor
        ↓
Paper Trade / Real Trade
```

---

# Current Indicators

Implemented indicators:

* EMA
* RSI
* MACD
* ATR
* Volatility

---

# Current Strategies

Example strategies:

* EMA + RSI strategy
* Custom strategy template

Custom strategies are loaded dynamically from:

```text
strategies/custom/
```

---

# Environment Variables

Create:

```text
.env
```

Example:

```env
APP_NAME=MCP Trading Bot
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=trading

REDIS_HOST=redis
REDIS_PORT=6379

BINANCE_API_KEY=YOUR_KEY
BINANCE_SECRET_KEY=YOUR_SECRET
BINANCE_TESTNET=true
PAPER_TRADING=true

NVIDIA_API_KEY=YOUR_NVIDIA_API_KEY
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
```

---

# Binance Setup

## Binance Spot Testnet

Use:

[https://testnet.binance.vision](https://testnet.binance.vision)

Generate:

* API KEY
* SECRET KEY

Add them into:

```text
.env
```

---

# NVIDIA AI Setup

Create API key at:

[https://build.nvidia.com](https://build.nvidia.com)

Add:

```env
NVIDIA_API_KEY=YOUR_KEY
```

---

# Running The Project

## Clone

```bash
git clone <repo>
cd mcp-trading-bot
```

---

# Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Export Python Path

```bash
export PYTHONPATH=$(pwd)
```

---

# Alembic Migration

Generate migration:

```bash
alembic revision --autogenerate -m "initial_tables"
```

Apply migrations:

```bash
alembic upgrade head
```

---

# Docker Build

```bash
docker-compose build
```

---

# Start Stack

```bash
docker-compose up -d
```

---

# Verify Containers

```bash
docker ps
```

Expected:

```text
mcp-trading-bot_app_1
mcp-trading-bot_db_1
mcp-trading-bot_redis_1
```

---

# API Endpoints

## Swagger UI

```text
http://SERVER_IP:8000/docs
```

---

## Health

```bash
curl http://localhost:8000/health
```

---

## Status

```bash
curl http://localhost:8000/status
```

---

# Logs

```bash
docker-compose logs -f app
```

---

# Current Operating Modes

## Paper Trading

```env
PAPER_TRADING=true
```

No real money.
No real orders.

---

## Binance Testnet Trading

```env
PAPER_TRADING=false
BINANCE_TESTNET=true
```

Executes orders in Binance sandbox.

---

## Real Trading

```env
PAPER_TRADING=false
BINANCE_TESTNET=false
```

WARNING:
This uses real money.

---

# What Is Still Missing

The backend engine is functional.

However, the platform still lacks the full product layer.

---

# Missing Features / Future Roadmap

## 1. Frontend Dashboard

Planned stack:

* Next.js
* Tailwind
* shadcn/ui
* Zustand
* React Query

Dashboard capabilities:

* live portfolio
* live trades
* live PnL
* active positions
* signals
* risk metrics
* strategy control
* AI interaction

---

## 2. Conversational AI Control

Planned functionality:

```text
"Pause all scalping strategies"
"Trade only BTC and ETH"
"Increase risk to 1.5%"
"Generate RSI strategy"
```

The AI layer will:

* generate strategies
* modify runtime parameters
* control active trading systems
* manage symbols
* optimize strategies

---

## 3. Strategy Builder UI

Planned features:

* create strategies visually
* AI-generated strategies
* upload custom strategies
* parameter editing
* enable/disable strategies
* live deployment

---

## 4. Multi-Symbol Control

Future functionality:

* BTC
* ETH
* SOL
* XRP
* DOGE
* custom symbol lists

Managed directly from UI.

---

## 5. Real-Time WebSocket Engine

Current system uses polling.

Planned upgrade:

* Binance WebSocket streams
* real-time candles
* ultra-low latency processing
* live order events

---

## 6. Advanced Portfolio Analytics

Planned analytics:

* Sharpe ratio
* winrate
* exposure
* drawdown
* volatility
* expectancy
* equity curves

---

## 7. Backtesting Platform

Planned features:

* historical simulations
* visual charts
* strategy optimization
* parameter sweeps
* performance reports

---

## 8. Monitoring Stack

Planned integrations:

* Prometheus
* Grafana
* alerting
* uptime monitoring
* execution metrics

---

## 9. Telegram / Discord Integration

Planned functionality:

* trade alerts
* notifications
* AI summaries
* remote bot control

---

## 10. AI Strategy Generation

One of the major future goals:

```text
"Create a high-frequency BTC scalping strategy"
```

The AI will generate:

* indicators
* entry logic
* exit logic
* risk logic
* executable strategy files

automatically.

---

# Long-Term Vision

The long-term objective is to build:

```text
GPT for algorithmic trading
```

A complete AI-native trading operating system capable of:

* autonomous strategy generation
* portfolio management
* conversational control
* multi-agent coordination
* live execution
* self-optimization

---

# Current Status

## Infrastructure

COMPLETE

## Backend Engine

COMPLETE

## Async Runtime

COMPLETE

## Trading Core

COMPLETE

## Product Layer / Frontend

IN PROGRESS

## AI Conversational Platform

PLANNED

---

# Important Notes

This project is currently under active development.

Use:

* paper trading
* Binance testnet
* sandbox environments

before enabling real trading.

Never use real funds before:

* validating strategies
* validating risk controls
* testing execution
* testing failover behavior
* validating AI decisions

---

# License

Private / Internal Development
