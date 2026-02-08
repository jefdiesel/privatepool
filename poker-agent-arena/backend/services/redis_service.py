"""Redis service for caching and real-time state management."""

from __future__ import annotations

from typing import Any

import redis.asyncio as redis

# Global Redis client
_redis_client: redis.Redis | None = None


async def init_redis(redis_url: str) -> None:
    """Initialize Redis connection."""
    global _redis_client

    _redis_client = redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_redis() -> redis.Redis:
    """Get Redis client for dependency injection."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized")
    return _redis_client


async def get_redis_client() -> redis.Redis | None:
    """Get Redis client, returning None if not available.

    Use this for optional Redis operations where fallback behavior is acceptable.
    """
    return _redis_client


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy."""
    if _redis_client is None:
        return False

    try:
        await _redis_client.ping()
        return True
    except Exception:
        return False


async def get_redis_info() -> dict | None:
    """Get Redis server info for health monitoring.

    Returns:
        Dictionary with Redis metrics or None if unavailable
    """
    if _redis_client is None:
        return None

    try:
        info = await _redis_client.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "total_connections_received": info.get("total_connections_received", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
        }
    except Exception:
        return None


class RedisService:
    """High-level Redis operations for the poker arena."""

    def __init__(self, client: redis.Redis):
        self.client = client

    # Tournament State Operations

    async def set_tournament_state(self, tournament_id: str, state: dict[str, Any]) -> None:
        """Set active tournament state with TTL."""
        import json

        key = f"tournament:{tournament_id}:state"
        await self.client.set(key, json.dumps(state), ex=86400)  # 24 hour TTL

    async def get_tournament_state(self, tournament_id: str) -> dict[str, Any] | None:
        """Get active tournament state."""
        import json

        key = f"tournament:{tournament_id}:state"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Table State Operations

    async def set_table_state(self, table_id: str, state: dict[str, Any]) -> None:
        """Set table state with TTL."""
        import json

        key = f"table:{table_id}:state"
        await self.client.set(key, json.dumps(state), ex=86400)

    async def get_table_state(self, table_id: str) -> dict[str, Any] | None:
        """Get table state."""
        import json

        key = f"table:{table_id}:state"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Hand State Operations

    async def set_hand_state(self, hand_id: str, state: dict[str, Any]) -> None:
        """Set current hand state with short TTL."""
        import json

        key = f"hand:{hand_id}:state"
        await self.client.set(key, json.dumps(state), ex=300)  # 5 minute TTL

    async def get_hand_state(self, hand_id: str) -> dict[str, Any] | None:
        """Get current hand state."""
        import json

        key = f"hand:{hand_id}:state"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    # Rate Limiting

    async def check_rate_limit(
        self,
        wallet: str,
        endpoint: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is within rate limit."""
        key = f"ratelimit:{wallet}:{endpoint}"
        count = await self.client.incr(key)

        if count == 1:
            await self.client.expire(key, window_seconds)

        return count <= limit

    # Budget Tracking

    async def set_budget(self, tournament_id: str, budget: float) -> None:
        """Set budget for a tournament."""
        await self.client.set(f"budget:{tournament_id}", str(budget))
        await self.client.set(f"spent:{tournament_id}", "0")

    async def get_budget_status(self, tournament_id: str) -> tuple[float, float]:
        """Get budget and spent amount for tournament."""
        budget = float(await self.client.get(f"budget:{tournament_id}") or 0)
        spent = float(await self.client.get(f"spent:{tournament_id}") or 0)
        return budget, spent

    async def record_usage(
        self,
        tournament_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool = False,
    ) -> None:
        """Record API usage for budget tracking."""
        # Claude Sonnet pricing
        input_cost = (input_tokens / 1000) * 0.003
        output_cost = (output_tokens / 1000) * 0.015
        total_cost = input_cost + output_cost

        await self.client.incrbyfloat(f"spent:{tournament_id}", total_cost)
        await self.client.incr(f"decisions:{tournament_id}")
        await self.client.incrby(f"tokens_input:{tournament_id}", input_tokens)
        await self.client.incrby(f"tokens_output:{tournament_id}", output_tokens)

        if cache_hit:
            await self.client.incr(f"cache_hits:{tournament_id}")

    async def can_make_call(self, tournament_id: str) -> bool:
        """Check if we're within budget."""
        budget, spent = await self.get_budget_status(tournament_id)
        return spent < budget

    # Session Management

    async def set_session(self, socket_id: str, session_data: dict[str, Any]) -> None:
        """Set player session mapping."""
        import json

        key = f"session:{socket_id}"
        await self.client.set(key, json.dumps(session_data), ex=86400)  # 24 hour TTL

    async def get_session(self, socket_id: str) -> dict[str, Any] | None:
        """Get player session data."""
        import json

        key = f"session:{socket_id}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def delete_session(self, socket_id: str) -> None:
        """Delete player session."""
        await self.client.delete(f"session:{socket_id}")
