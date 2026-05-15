import asyncio
import json
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.logger import get_logger

logger = get_logger("event_bus")


# ─────────────────────────────────────────────
# Event envelope
# ─────────────────────────────────────────────

@dataclass
class Event:
    """Standard event envelope."""
    type:       str
    payload:    dict
    timestamp:  str = ""
    source:     str = "trading_engine"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**data)


# ─────────────────────────────────────────────
# In-process bus
# ─────────────────────────────────────────────

class InProcessBus:
    """
    Fast, synchronous, in-process pub/sub.
    Zero latency. Does NOT survive restarts.
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)
        logger.debug(
            "handler_subscribed",
            event_type=event_type,       # ← renamed from 'event' to 'event_type'
            handler=handler.__name__,
        )

    def subscribe_all(self, handler: Callable):
        self.subscribe("*", handler)

    async def publish(self, event: Event):
        handlers = (
            self._handlers.get(event.type, []) +
            self._handlers.get("*", [])
        )
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "in_process_handler_error",
                    event_type=event.type,   # ← renamed
                    handler=handler.__name__,
                    error=str(e),
                )


# ─────────────────────────────────────────────
# Redis Streams publisher
# ─────────────────────────────────────────────

class RedisStreamPublisher:
    """
    Publishes events to Redis Streams.
    Durable, replayable, cross-service.
    """

    STREAM_PREFIX = "trading:events"
    MAXLEN        = 10_000

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def publish(self, event: Event):
        stream_key = f"{self.STREAM_PREFIX}:{event.type}"
        try:
            await self.redis.xadd(
                stream_key,
                {"data": event.to_json()},
                maxlen=self.MAXLEN,
                approximate=True,
            )
            logger.debug(
                "redis_stream_published",
                stream=stream_key,
                event_type=event.type,   # ← renamed
            )
        except Exception as e:
            logger.error(
                "redis_stream_publish_error",
                stream=stream_key,
                error=str(e),
            )


# ─────────────────────────────────────────────
# Redis Streams consumer
# ─────────────────────────────────────────────

class RedisStreamConsumer:

    def __init__(
        self,
        redis: aioredis.Redis,
        stream: str,
        group: str,
        consumer_name: str,
        handler: Callable,
        block_ms: int = 1000,
    ):
        self.redis        = redis
        self.stream       = stream
        self.group        = group
        self.consumer     = consumer_name
        self.handler      = handler
        self.block_ms     = block_ms
        self.running      = False

    async def _ensure_group(self):
        try:
            await self.redis.xgroup_create(
                self.stream,
                self.group,
                id="0",
                mkstream=True,
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def start(self):
        await self._ensure_group()
        self.running = True

        logger.info(
            "stream_consumer_started",
            stream=self.stream,
            group=self.group,
        )

        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=self.group,
                    consumername=self.consumer,
                    streams={self.stream: ">"},
                    count=10,
                    block=self.block_ms,
                )
                if not messages:
                    continue

                for _, entries in messages:
                    for message_id, fields in entries:
                        try:
                            data = json.loads(fields[b"data"])
                            event = Event.from_dict(data)
                            await self.handler(event)
                            await self.redis.xack(
                                self.stream, self.group, message_id
                            )
                        except Exception as e:
                            logger.error(
                                "stream_message_processing_error",
                                stream=self.stream,
                                error=str(e),
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "stream_consumer_error",
                    stream=self.stream,
                    error=str(e),
                )
                await asyncio.sleep(2)

    async def stop(self):
        self.running = False


# ─────────────────────────────────────────────
# Unified EventBus (façade)
# ─────────────────────────────────────────────

class EventBus:
    """
    Public façade combining in-process and
    Redis Streams publishing behind a single API.
    """

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._in_process = InProcessBus()
        self._redis_pub  = (
            RedisStreamPublisher(redis_client)
            if redis_client else None
        )

    def subscribe(self, event_type: str, handler: Callable):
        self._in_process.subscribe(event_type, handler)

    def subscribe_all(self, handler: Callable):
        self._in_process.subscribe_all(handler)

    async def publish(
        self,
        event_type: str,
        payload: Any,
        source: str = "trading_engine",
    ):
        if hasattr(payload, "__dict__"):
            payload_dict = {
                k: str(v) for k, v in payload.__dict__.items()
                if not k.startswith("_")
            }
        elif isinstance(payload, dict):
            payload_dict = payload
        else:
            payload_dict = {"data": str(payload)}

        event = Event(
            type=event_type,
            payload=payload_dict,
            source=source,
        )

        logger.debug(
            "event_published",
            event_type=event_type,   # ← renamed
        )

        await self._in_process.publish(event)

        if self._redis_pub:
            await self._redis_pub.publish(event)

    async def create_consumer(
        self,
        stream_suffix: str,
        group: str,
        consumer_name: str,
        handler: Callable,
    ) -> RedisStreamConsumer | None:
        if not self._redis_pub:
            logger.warning(
                "redis_not_configured_skipping_consumer",
                stream=stream_suffix,
            )
            return None

        stream = f"{RedisStreamPublisher.STREAM_PREFIX}:{stream_suffix}"
        return RedisStreamConsumer(
            redis=self._redis_pub.redis,
            stream=stream,
            group=group,
            consumer_name=consumer_name,
            handler=handler,
        )


# ─────────────────────────────────────────────
# Event type constants
# ─────────────────────────────────────────────

class Events:
    # Position lifecycle
    POSITION_OPENED  = "position.opened"
    POSITION_CLOSED  = "position.closed"
    POSITION_UPDATED = "position.updated"

    # Risk triggers
    STOP_LOSS_HIT    = "position.stop_loss_hit"
    TAKE_PROFIT_HIT  = "position.take_profit_hit"
    TRAILING_UPDATED = "position.trailing_updated"

    # PnL
    PNL_UPDATED      = "pnl.updated"

    # Risk / system
    EMERGENCY_STOP   = "risk.emergency_stop"
    DAILY_DRAWDOWN   = "risk.daily_drawdown_limit"

    # Market data
    MARKET_TICK      = "market.tick"
    CANDLE_CLOSED    = "market.candle_closed"
