"""
app/services/copilot_service.py — Phase 6: AI Copilot orchestration.

Architecture:
  User message
  → DeepSeek (function calling / tool use)
  → CopilotService dispatches tool calls to real services
  → Assembles response + actions_taken list
  → Returns to API

Tools available to the AI:
  get_portfolio_status    — open positions + PnL
  get_analytics_summary   — sharpe, drawdown, win rate, equity curve
  get_daily_stats         — today's trade count, PnL
  list_strategies         — all strategy configs
  enable_strategy         — enable a strategy by name or id
  disable_strategy        — disable a strategy by name or id
  update_strategy_risk    — update SL/TP/trailing on a strategy
  close_position          — close a specific position
  close_all_positions     — emergency close all (requires confirm=true)
  get_market_price        — current price for a symbol

All destructive actions require the AI to explicitly pass confirm=True,
which it should only do after the user has confirmed in conversation.
"""

import json
from typing import Any

from openai import OpenAI

from app.config import settings
from app.logger import get_logger

logger = get_logger("copilot_service")

# ─────────────────────────────────────────────
# Tool definitions (OpenAI / DeepSeek format)
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_status",
            "description": "Get current open positions, unrealized PnL, realized PnL, and total exposure.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_summary",
            "description": "Get performance analytics: Sharpe ratio, max drawdown, win rate, total realized PnL, trade count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back. Default 30.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_stats",
            "description": "Get today's trading stats: trades opened, closed, PnL, win rate.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_strategies",
            "description": "List all strategy configurations with their status (enabled/disabled), version, timeframe, and risk params.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled_only": {
                        "type": "boolean",
                        "description": "If true, only return enabled strategies.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enable_strategy",
            "description": "Enable a strategy so it starts generating signals. Use the strategy name or ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_name": {
                        "type": "string",
                        "description": "Strategy name (exact match from list_strategies).",
                    },
                    "strategy_id": {
                        "type": "integer",
                        "description": "Strategy ID as alternative to name.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "disable_strategy",
            "description": "Disable a strategy so it stops generating signals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_name": {
                        "type": "string",
                        "description": "Strategy name (exact match from list_strategies).",
                    },
                    "strategy_id": {
                        "type": "integer",
                        "description": "Strategy ID as alternative to name.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "disable_all_strategies",
            "description": "Disable all currently enabled strategies at once.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_strategy_risk",
            "description": "Update stop loss, take profit, or trailing stop percentage on a strategy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "strategy_name": {"type": "string"},
                    "strategy_id":   {"type": "integer"},
                    "stop_loss_pct": {
                        "type": "number",
                        "description": "Stop loss as decimal (e.g. 0.02 = 2%). Pass null to leave unchanged.",
                    },
                    "take_profit_pct": {
                        "type": "number",
                        "description": "Take profit as decimal (e.g. 0.04 = 4%). Pass null to leave unchanged.",
                    },
                    "trailing_stop_pct": {
                        "type": "number",
                        "description": "Trailing stop as decimal. Pass null to remove trailing stop.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_position",
            "description": "Close a specific open position by ID at current market price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position_id": {
                        "type": "integer",
                        "description": "Position ID to close.",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true. Ask user to confirm before setting this.",
                    },
                },
                "required": ["position_id", "confirm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_all_positions",
            "description": "Emergency close ALL open positions at current market price. DESTRUCTIVE — only call after explicit user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true. Only set after user explicitly confirms they want to close everything.",
                    }
                },
                "required": ["confirm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_price",
            "description": "Get the current live price for a trading symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol, e.g. BTC/USDT",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
]

# ─────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a trading terminal copilot. You help the user manage their algorithmic trading bot.

RULES:
- Respond in terminal style: concise, precise, no fluff.
- Use tool calls to get real data before answering data questions.
- For destructive actions (close positions, close all), ask the user to confirm FIRST. Only call the tool with confirm=true AFTER they say yes.
- Never invent data. If you don't have it, call the appropriate tool.
- Format numbers clearly: PnL as $X.XX, percentages as X.XX%.
- If trading is disabled, say so clearly for action commands.
- Keep responses short. Use line breaks for lists. No markdown headers.

PERSONALITY:
- Direct. No apologies. No filler words.
- Like a Bloomberg terminal that can talk.
"""


# ─────────────────────────────────────────────
# CopilotService
# ─────────────────────────────────────────────

class CopilotService:
    """
    Orchestrates: user message → AI tool calls → real service actions → response.
    Stateless per request — no session storage (history passed in from frontend).
    """

    def __init__(self):
        self._client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30.0,
        )

    async def chat(
        self,
        message:              str,
        conversation_history: list[dict],
        lifecycle=None,
        trading_bot=None,
        analytics=None,
        strategy_svc=None,
    ) -> dict:
        """
        Main entry point. Returns:
        {
            response:      str,
            actions_taken: list[dict],
            data:          any,
        }
        """
        actions_taken: list[dict] = []
        data_payload:  Any        = None

        # Build message list for the AI
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in conversation_history[-10:]:  # keep last 10 turns for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        # ── First AI call ─────────────────────
        try:
            response = await self._call_ai(messages)
        except Exception as e:
            logger.error("copilot_ai_call_failed", error=str(e))
            return {
                "response":      f"AI unavailable: {str(e)}",
                "actions_taken": [],
                "data":          None,
            }

        # ── Tool call loop ────────────────────
        max_rounds = 5
        rounds     = 0

        while response.choices[0].finish_reason == "tool_calls" and rounds < max_rounds:
            rounds += 1
            tool_calls = response.choices[0].message.tool_calls

            # Add assistant message with tool calls to history
            messages.append({
                "role":       "assistant",
                "content":    response.choices[0].message.content or "",
                "tool_calls": [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })

            # Execute each tool call
            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                logger.info("copilot_tool_call", tool=tool_name, args=args)

                tool_result, action_record = await self._dispatch_tool(
                    tool_name=tool_name,
                    args=args,
                    lifecycle=lifecycle,
                    trading_bot=trading_bot,
                    analytics=analytics,
                    strategy_svc=strategy_svc,
                )

                if action_record:
                    actions_taken.append(action_record)
                if isinstance(tool_result, dict) and "data" in tool_result:
                    data_payload = tool_result["data"]

                # Add tool result to message history
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(tool_result, default=str),
                })

            # Next AI call with tool results
            try:
                response = await self._call_ai(messages)
            except Exception as e:
                logger.error("copilot_ai_followup_failed", error=str(e))
                break

        final_text = response.choices[0].message.content or "Done."

        return {
            "response":      final_text,
            "actions_taken": actions_taken,
            "data":          data_payload,
        }

    # ─────────────────────────────────────────
    # AI call (sync wrapped in thread)
    # ─────────────────────────────────────────

    async def _call_ai(self, messages: list[dict]):
        import asyncio
        return await asyncio.to_thread(
            self._client.chat.completions.create,
            model=settings.DEEPSEEK_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1,
            max_tokens=800,
        )

    # ─────────────────────────────────────────
    # Tool dispatcher
    # ─────────────────────────────────────────

    async def _dispatch_tool(
        self,
        tool_name:    str,
        args:         dict,
        lifecycle=None,
        trading_bot=None,
        analytics=None,
        strategy_svc=None,
    ) -> tuple[dict, dict | None]:
        """
        Returns (tool_result_dict, action_record_or_None).
        tool_result_dict is sent back to the AI.
        action_record is stored in actions_taken for the frontend.
        """
        try:
            if tool_name == "get_portfolio_status":
                return await self._get_portfolio_status(lifecycle), None

            elif tool_name == "get_analytics_summary":
                days = args.get("days", 30)
                return await self._get_analytics_summary(analytics, days), None

            elif tool_name == "get_daily_stats":
                return await self._get_daily_stats(analytics), None

            elif tool_name == "list_strategies":
                enabled_only = args.get("enabled_only", False)
                return await self._list_strategies(strategy_svc, enabled_only), None

            elif tool_name == "enable_strategy":
                result = await self._toggle_strategy(strategy_svc, args, enable=True)
                action = {"action": "enable_strategy", "args": args, "result": result.get("status")}
                return result, action

            elif tool_name == "disable_strategy":
                result = await self._toggle_strategy(strategy_svc, args, enable=False)
                action = {"action": "disable_strategy", "args": args, "result": result.get("status")}
                return result, action

            elif tool_name == "disable_all_strategies":
                result = await self._disable_all_strategies(strategy_svc)
                action = {"action": "disable_all_strategies", "result": result.get("status")}
                return result, action

            elif tool_name == "update_strategy_risk":
                result = await self._update_strategy_risk(strategy_svc, args)
                action = {"action": "update_strategy_risk", "args": args, "result": result.get("status")}
                return result, action

            elif tool_name == "close_position":
                if not args.get("confirm"):
                    return {"error": "confirm must be true"}, None
                result = await self._close_position(lifecycle, trading_bot, args)
                action = {"action": "close_position", "position_id": args.get("position_id"), "result": result.get("status")}
                return result, action

            elif tool_name == "close_all_positions":
                if not args.get("confirm"):
                    return {"error": "confirm must be true — ask user first"}, None
                result = await self._close_all_positions(lifecycle, trading_bot)
                action = {"action": "close_all_positions", "result": result.get("status")}
                return result, action

            elif tool_name == "get_market_price":
                return await self._get_market_price(trading_bot, args.get("symbol", "BTC/USDT")), None

            else:
                return {"error": f"Unknown tool: {tool_name}"}, None

        except Exception as e:
            logger.error("copilot_tool_error", tool=tool_name, error=str(e))
            return {"error": str(e)}, None

    # ─────────────────────────────────────────
    # Tool implementations
    # ─────────────────────────────────────────

    async def _get_portfolio_status(self, lifecycle) -> dict:
        if lifecycle is None:
            return {
                "trading_enabled": False,
                "open_positions":  [],
                "total_unrealized": 0.0,
                "total_realized":   0.0,
                "note": "Trading runtime is disabled (ENABLE_TRADING=false)",
            }
        positions = await lifecycle.get_open_positions()
        serialized = []
        for p in positions:
            serialized.append({
                "id":              p.id,
                "symbol":          p.symbol,
                "side":            p.side.value,
                "entry_price":     p.avg_entry_price,
                "quantity":        p.remaining_quantity,
                "unrealized_pnl":  p.unrealized_pnl,
                "realized_pnl":    p.realized_pnl,
                "stop_loss":       p.stop_loss,
                "take_profit":     p.take_profit,
                "strategy":        p.strategy_name,
            })
        return {
            "data": {
                "open_positions":   serialized,
                "count":            len(serialized),
                "total_unrealized": sum(p["unrealized_pnl"] for p in serialized),
                "total_realized":   sum(p["realized_pnl"]   for p in serialized),
                "total_exposure":   sum(
                    p["entry_price"] * p["quantity"] for p in serialized
                ),
            }
        }

    async def _get_analytics_summary(self, analytics, days: int) -> dict:
        if analytics is None:
            return {"error": "Analytics service not available"}
        try:
            sharpe   = await analytics.get_sharpe_ratio(days=days)
            drawdown = await analytics.get_max_drawdown(days=days)
            ai_perf  = await analytics.get_ai_performance_metrics()
            return {
                "data": {
                    "sharpe_ratio":       sharpe.get("sharpe_ratio"),
                    "max_drawdown":       drawdown.get("max_drawdown"),
                    "max_drawdown_pct":   drawdown.get("max_drawdown_pct"),
                    "win_rate":           ai_perf.get("overall_win_rate"),
                    "total_trades":       ai_perf.get("total_trades"),
                    "total_realized_pnl": ai_perf.get("total_realized_pnl"),
                    "days":               days,
                }
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_daily_stats(self, analytics) -> dict:
        if analytics is None:
            return {"error": "Analytics service not available"}
        try:
            stats = await analytics.get_trade_duration_stats()
            return {"data": stats}
        except Exception as e:
            return {"error": str(e)}

    async def _list_strategies(self, strategy_svc, enabled_only: bool) -> dict:
        if strategy_svc is None:
            return {"error": "Strategy service not available"}
        configs = await strategy_svc.list_all(enabled_only=enabled_only)
        return {
            "data": [
                {
                    "id":               c.id,
                    "name":             c.name,
                    "enabled":          c.enabled,
                    "version":          c.version,
                    "timeframe":        c.timeframe,
                    "symbols":          c.symbols,
                    "stop_loss_pct":    c.stop_loss_pct,
                    "take_profit_pct":  c.take_profit_pct,
                    "trailing_stop_pct": c.trailing_stop_pct,
                }
                for c in configs
            ]
        }

    async def _toggle_strategy(self, strategy_svc, args: dict, enable: bool) -> dict:
        if strategy_svc is None:
            return {"error": "Strategy service not available", "status": "error"}
        strategy_id   = args.get("strategy_id")
        strategy_name = args.get("strategy_name")
        if not strategy_id and not strategy_name:
            return {"error": "Provide strategy_name or strategy_id", "status": "error"}
        if not strategy_id and strategy_name:
            config = await strategy_svc.get_by_name(strategy_name)
            if not config:
                return {"error": f"Strategy '{strategy_name}' not found", "status": "error"}
            strategy_id = config.id
        result = await strategy_svc.set_enabled(strategy_id, enable)
        return {
            "status":  "ok",
            "name":    result.name,
            "enabled": result.enabled,
        }

    async def _disable_all_strategies(self, strategy_svc) -> dict:
        if strategy_svc is None:
            return {"error": "Strategy service not available", "status": "error"}
        enabled = await strategy_svc.list_all(enabled_only=True)
        disabled = []
        for config in enabled:
            await strategy_svc.set_enabled(config.id, False)
            disabled.append(config.name)
        return {"status": "ok", "disabled": disabled, "count": len(disabled)}

    async def _update_strategy_risk(self, strategy_svc, args: dict) -> dict:
        if strategy_svc is None:
            return {"error": "Strategy service not available", "status": "error"}
        strategy_id   = args.get("strategy_id")
        strategy_name = args.get("strategy_name")
        if not strategy_id and strategy_name:
            config = await strategy_svc.get_by_name(strategy_name)
            if not config:
                return {"error": f"Strategy '{strategy_name}' not found", "status": "error"}
            strategy_id = config.id
        update_data = {}
        if args.get("stop_loss_pct") is not None:
            update_data["stop_loss_pct"] = float(args["stop_loss_pct"])
        if args.get("take_profit_pct") is not None:
            update_data["take_profit_pct"] = float(args["take_profit_pct"])
        if "trailing_stop_pct" in args:
            update_data["trailing_stop_pct"] = args["trailing_stop_pct"]
        if not update_data:
            return {"error": "No risk fields provided", "status": "error"}
        result = await strategy_svc.update(strategy_id, update_data, "Updated via Copilot")
        return {
            "status":            "ok",
            "name":              result.name,
            "stop_loss_pct":     result.stop_loss_pct,
            "take_profit_pct":   result.take_profit_pct,
            "trailing_stop_pct": result.trailing_stop_pct,
        }

    async def _close_position(self, lifecycle, trading_bot, args: dict) -> dict:
        if lifecycle is None:
            return {"error": "Trading runtime disabled", "status": "error"}
        position_id = args.get("position_id")
        if not position_id:
            return {"error": "position_id required", "status": "error"}
        # Get live price
        position = await lifecycle.get_position(position_id)
        if not position:
            return {"error": f"Position {position_id} not found", "status": "error"}
        exit_price = position.avg_entry_price  # fallback
        if trading_bot and hasattr(trading_bot, "market_engine"):
            live = trading_bot.market_engine.get_latest_price(position.symbol)
            if live:
                exit_price = live
        from app.models.trades import CloseReason
        closed = await lifecycle.close_position(position_id, exit_price, CloseReason.MANUAL)
        if not closed:
            return {"error": "Close failed or position already closed", "status": "error"}
        return {
            "status":       "ok",
            "position_id":  position_id,
            "realized_pnl": closed.realized_pnl,
            "exit_price":   exit_price,
        }

    async def _close_all_positions(self, lifecycle, trading_bot) -> dict:
        if lifecycle is None:
            return {"error": "Trading runtime disabled", "status": "error"}
        current_prices: dict[str, float] = {}
        if trading_bot and hasattr(trading_bot, "market_engine"):
            open_positions = await lifecycle.get_open_positions()
            for p in open_positions:
                price = trading_bot.market_engine.get_latest_price(p.symbol)
                if price:
                    current_prices[p.symbol] = price
        closed = await lifecycle.emergency_close_all(current_prices=current_prices)
        return {
            "status":           "ok",
            "positions_closed": len(closed),
            "total_pnl":        sum(p.realized_pnl for p in closed),
        }

    async def _get_market_price(self, trading_bot, symbol: str) -> dict:
        if trading_bot and hasattr(trading_bot, "market_engine"):
            # get_latest_price is synchronous — no await
            price = trading_bot.market_engine.get_latest_price(symbol)
            if price:
                return {"symbol": symbol, "price": price, "source": "live"}
        # Fallback: fetch from Binance REST
        try:
            from app.services.binance_service import BinanceService
            binance = BinanceService()
            ticker = await binance.fetch_ticker(symbol)
            return {"symbol": symbol, "price": float(ticker["last"]), "source": "rest"}
        except Exception as e:
            return {"error": str(e)}
