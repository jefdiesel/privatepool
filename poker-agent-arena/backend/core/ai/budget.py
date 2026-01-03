"""Budget tracking for AI tournament costs.

Tracks API usage per tournament to enforce cost limits.
Uses Redis for distributed state management.
"""

from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis


@dataclass
class UsageStats:
    """API usage statistics for a tournament."""
    budget: float
    spent: float
    decisions: int
    input_tokens: int
    output_tokens: int
    cache_hits: int
    cache_hit_rate: float


class BudgetTracker:
    """Tracks AI API costs per tournament.

    Claude Sonnet pricing (as of 2024):
    - Input: $0.003 per 1K tokens
    - Output: $0.015 per 1K tokens
    - Cache read: $0.0003 per 1K tokens (90% savings)

    Budget formula:
    - Budget = expected_cost * multiplier (default 3.0)
    - Expected cost based on estimated decisions and token usage
    """

    # Claude Sonnet 4 pricing
    INPUT_COST_PER_1K = 0.003
    OUTPUT_COST_PER_1K = 0.015
    CACHE_READ_COST_PER_1K = 0.0003  # 90% discount for cached tokens

    def __init__(self, redis_client: redis.Redis):
        """Initialize budget tracker.

        Args:
            redis_client: Redis client for distributed state
        """
        self.redis = redis_client

    async def set_budget(
        self,
        tournament_id: str,
        expected_cost: float,
        multiplier: float = 3.0,
    ) -> float:
        """Set budget for a tournament.

        Args:
            tournament_id: Tournament identifier
            expected_cost: Estimated cost in USD
            multiplier: Safety multiplier (default 3.0)

        Returns:
            Actual budget set
        """
        budget = expected_cost * multiplier

        # Initialize all counters
        pipe = self.redis.pipeline()
        pipe.set(f"ai:budget:{tournament_id}", str(budget))
        pipe.set(f"ai:spent:{tournament_id}", "0")
        pipe.set(f"ai:decisions:{tournament_id}", "0")
        pipe.set(f"ai:tokens_input:{tournament_id}", "0")
        pipe.set(f"ai:tokens_output:{tournament_id}", "0")
        pipe.set(f"ai:cache_hits:{tournament_id}", "0")
        await pipe.execute()

        return budget

    async def can_make_call(self, tournament_id: str) -> bool:
        """Check if tournament has remaining budget.

        Args:
            tournament_id: Tournament identifier

        Returns:
            True if spent < budget
        """
        budget = await self.redis.get(f"ai:budget:{tournament_id}")
        spent = await self.redis.get(f"ai:spent:{tournament_id}")

        if budget is None:
            # No budget set - allow by default (for testing)
            return True

        budget_val = float(budget)
        spent_val = float(spent or 0)

        return spent_val < budget_val

    async def record_usage(
        self,
        tournament_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
    ) -> float:
        """Record API usage for budget tracking.

        Args:
            tournament_id: Tournament identifier
            input_tokens: Non-cached input tokens used
            output_tokens: Output tokens used
            cache_read_tokens: Cached input tokens read

        Returns:
            Cost of this API call in USD
        """
        # Calculate cost
        # Non-cached input tokens
        input_cost = (input_tokens / 1000) * self.INPUT_COST_PER_1K
        # Cached tokens at reduced rate
        cache_cost = (cache_read_tokens / 1000) * self.CACHE_READ_COST_PER_1K
        # Output tokens
        output_cost = (output_tokens / 1000) * self.OUTPUT_COST_PER_1K

        total_cost = input_cost + cache_cost + output_cost

        # Update all counters atomically
        pipe = self.redis.pipeline()
        pipe.incrbyfloat(f"ai:spent:{tournament_id}", total_cost)
        pipe.incr(f"ai:decisions:{tournament_id}")
        pipe.incrby(f"ai:tokens_input:{tournament_id}", input_tokens + cache_read_tokens)
        pipe.incrby(f"ai:tokens_output:{tournament_id}", output_tokens)

        if cache_read_tokens > 0:
            pipe.incr(f"ai:cache_hits:{tournament_id}")

        await pipe.execute()

        return total_cost

    async def get_stats(self, tournament_id: str) -> Optional[UsageStats]:
        """Get usage statistics for a tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            UsageStats or None if tournament not found
        """
        budget = await self.redis.get(f"ai:budget:{tournament_id}")
        if budget is None:
            return None

        spent = await self.redis.get(f"ai:spent:{tournament_id}")
        decisions = await self.redis.get(f"ai:decisions:{tournament_id}")
        input_tokens = await self.redis.get(f"ai:tokens_input:{tournament_id}")
        output_tokens = await self.redis.get(f"ai:tokens_output:{tournament_id}")
        cache_hits = await self.redis.get(f"ai:cache_hits:{tournament_id}")

        decisions_val = int(decisions or 0)
        cache_hits_val = int(cache_hits or 0)

        cache_hit_rate = 0.0
        if decisions_val > 0:
            cache_hit_rate = cache_hits_val / decisions_val

        return UsageStats(
            budget=float(budget),
            spent=float(spent or 0),
            decisions=decisions_val,
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            cache_hits=cache_hits_val,
            cache_hit_rate=cache_hit_rate,
        )

    async def get_remaining_budget(self, tournament_id: str) -> float:
        """Get remaining budget for a tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            Remaining budget in USD (0 if none set)
        """
        budget = await self.redis.get(f"ai:budget:{tournament_id}")
        spent = await self.redis.get(f"ai:spent:{tournament_id}")

        if budget is None:
            return 0.0

        return float(budget) - float(spent or 0)

    async def cleanup(self, tournament_id: str) -> None:
        """Clean up budget tracking data for completed tournament.

        Args:
            tournament_id: Tournament identifier
        """
        keys = [
            f"ai:budget:{tournament_id}",
            f"ai:spent:{tournament_id}",
            f"ai:decisions:{tournament_id}",
            f"ai:tokens_input:{tournament_id}",
            f"ai:tokens_output:{tournament_id}",
            f"ai:cache_hits:{tournament_id}",
        ]
        await self.redis.delete(*keys)


def estimate_tournament_cost(
    num_players: int,
    avg_hands_per_player: int = 50,
    avg_decisions_per_hand: float = 2.5,
    system_prompt_tokens: int = 1500,
    game_state_tokens: int = 400,
    output_tokens: int = 50,
    cache_hit_rate: float = 0.85,
) -> float:
    """Estimate total API cost for a tournament.

    Args:
        num_players: Number of players in tournament
        avg_hands_per_player: Average hands each player plays
        avg_decisions_per_hand: Average decisions per hand
        system_prompt_tokens: System prompt token count
        game_state_tokens: Average game state tokens
        output_tokens: Average output tokens per decision
        cache_hit_rate: Expected cache hit rate

    Returns:
        Estimated cost in USD
    """
    # Total decisions in tournament
    total_decisions = num_players * avg_hands_per_player * avg_decisions_per_hand

    # Per-decision token breakdown
    input_per_decision = system_prompt_tokens + game_state_tokens
    cached_per_decision = system_prompt_tokens * cache_hit_rate
    uncached_per_decision = input_per_decision - cached_per_decision

    # Total tokens
    total_uncached_input = total_decisions * uncached_per_decision
    total_cached_input = total_decisions * cached_per_decision
    total_output = total_decisions * output_tokens

    # Calculate costs
    uncached_cost = (total_uncached_input / 1000) * BudgetTracker.INPUT_COST_PER_1K
    cached_cost = (total_cached_input / 1000) * BudgetTracker.CACHE_READ_COST_PER_1K
    output_cost = (total_output / 1000) * BudgetTracker.OUTPUT_COST_PER_1K

    return uncached_cost + cached_cost + output_cost
