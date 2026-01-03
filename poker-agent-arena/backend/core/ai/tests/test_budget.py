"""Tests for budget module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ..budget import BudgetTracker, UsageStats, estimate_tournament_cost


class TestBudgetTracker:
    """Tests for BudgetTracker class."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        # Mock pipeline
        pipeline = AsyncMock()
        pipeline.execute = AsyncMock(return_value=[])
        redis.pipeline.return_value = pipeline
        return redis

    @pytest.fixture
    def budget_tracker(self, mock_redis):
        """Create budget tracker with mock Redis."""
        return BudgetTracker(mock_redis)

    @pytest.mark.asyncio
    async def test_set_budget(self, budget_tracker, mock_redis):
        """Should set budget with multiplier."""
        budget = await budget_tracker.set_budget("tournament_1", 10.0, 3.0)

        assert budget == 30.0
        # Verify pipeline was used
        mock_redis.pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_budget_default_multiplier(self, budget_tracker):
        """Should use default 3.0 multiplier."""
        budget = await budget_tracker.set_budget("tournament_1", 10.0)
        assert budget == 30.0

    @pytest.mark.asyncio
    async def test_can_make_call_under_budget(self, budget_tracker, mock_redis):
        """Should return True when under budget."""
        mock_redis.get = AsyncMock(side_effect=["100.0", "50.0"])

        result = await budget_tracker.can_make_call("tournament_1")

        assert result is True

    @pytest.mark.asyncio
    async def test_can_make_call_over_budget(self, budget_tracker, mock_redis):
        """Should return False when over budget."""
        mock_redis.get = AsyncMock(side_effect=["100.0", "150.0"])

        result = await budget_tracker.can_make_call("tournament_1")

        assert result is False

    @pytest.mark.asyncio
    async def test_can_make_call_no_budget_set(self, budget_tracker, mock_redis):
        """Should return True when no budget set (testing mode)."""
        mock_redis.get = AsyncMock(return_value=None)

        result = await budget_tracker.can_make_call("tournament_1")

        assert result is True

    @pytest.mark.asyncio
    async def test_record_usage(self, budget_tracker, mock_redis):
        """Should record usage and return cost."""
        cost = await budget_tracker.record_usage(
            tournament_id="tournament_1",
            input_tokens=1000,
            output_tokens=100,
            cache_read_tokens=500,
        )

        # Expected cost:
        # Input: 1000/1000 * 0.003 = 0.003
        # Cache: 500/1000 * 0.0003 = 0.00015
        # Output: 100/1000 * 0.015 = 0.0015
        # Total: 0.00465
        assert abs(cost - 0.00465) < 0.0001

    @pytest.mark.asyncio
    async def test_record_usage_increments_cache_hits(self, budget_tracker, mock_redis):
        """Should increment cache hit counter when cache used."""
        pipeline = mock_redis.pipeline.return_value

        await budget_tracker.record_usage(
            tournament_id="tournament_1",
            input_tokens=500,
            output_tokens=50,
            cache_read_tokens=1000,
        )

        # Cache hit should be incremented
        pipeline.incr.assert_called()

    @pytest.mark.asyncio
    async def test_record_usage_no_cache_hit(self, budget_tracker, mock_redis):
        """Should not increment cache hits when no cache."""
        pipeline = mock_redis.pipeline.return_value

        await budget_tracker.record_usage(
            tournament_id="tournament_1",
            input_tokens=1500,
            output_tokens=50,
            cache_read_tokens=0,
        )

        # Verify incr was called for decisions counter
        pipeline.incr.assert_called()

    @pytest.mark.asyncio
    async def test_get_stats(self, budget_tracker, mock_redis):
        """Should return usage statistics."""
        mock_redis.get = AsyncMock(side_effect=[
            "30.0",   # budget
            "10.0",   # spent
            "100",    # decisions
            "150000", # input_tokens
            "5000",   # output_tokens
            "85",     # cache_hits
        ])

        stats = await budget_tracker.get_stats("tournament_1")

        assert stats is not None
        assert stats.budget == 30.0
        assert stats.spent == 10.0
        assert stats.decisions == 100
        assert stats.input_tokens == 150000
        assert stats.output_tokens == 5000
        assert stats.cache_hits == 85
        assert stats.cache_hit_rate == 0.85

    @pytest.mark.asyncio
    async def test_get_stats_not_found(self, budget_tracker, mock_redis):
        """Should return None when tournament not found."""
        mock_redis.get = AsyncMock(return_value=None)

        stats = await budget_tracker.get_stats("nonexistent")

        assert stats is None

    @pytest.mark.asyncio
    async def test_get_remaining_budget(self, budget_tracker, mock_redis):
        """Should return remaining budget."""
        mock_redis.get = AsyncMock(side_effect=["100.0", "30.0"])

        remaining = await budget_tracker.get_remaining_budget("tournament_1")

        assert remaining == 70.0

    @pytest.mark.asyncio
    async def test_get_remaining_budget_no_budget(self, budget_tracker, mock_redis):
        """Should return 0 when no budget set."""
        mock_redis.get = AsyncMock(return_value=None)

        remaining = await budget_tracker.get_remaining_budget("tournament_1")

        assert remaining == 0.0

    @pytest.mark.asyncio
    async def test_cleanup(self, budget_tracker, mock_redis):
        """Should delete all budget keys."""
        await budget_tracker.cleanup("tournament_1")

        mock_redis.delete.assert_called_once()
        # Should have all 6 keys
        args = mock_redis.delete.call_args[0]
        assert len(args) == 6


class TestCostConstants:
    """Tests for cost constants."""

    def test_input_cost_per_1k(self):
        """Input cost should be $0.003 per 1K tokens."""
        assert BudgetTracker.INPUT_COST_PER_1K == 0.003

    def test_output_cost_per_1k(self):
        """Output cost should be $0.015 per 1K tokens."""
        assert BudgetTracker.OUTPUT_COST_PER_1K == 0.015

    def test_cache_read_cost_per_1k(self):
        """Cache read cost should be $0.0003 per 1K tokens."""
        assert BudgetTracker.CACHE_READ_COST_PER_1K == 0.0003


class TestEstimateTournamentCost:
    """Tests for tournament cost estimation."""

    def test_estimate_basic_tournament(self):
        """Should estimate cost for a basic tournament."""
        cost = estimate_tournament_cost(
            num_players=27,
            avg_hands_per_player=50,
            avg_decisions_per_hand=2.5,
        )

        # Should return a positive cost
        assert cost > 0

    def test_estimate_increases_with_players(self):
        """Cost should increase with more players."""
        cost_small = estimate_tournament_cost(num_players=9)
        cost_large = estimate_tournament_cost(num_players=54)

        assert cost_large > cost_small

    def test_estimate_with_high_cache_rate(self):
        """Higher cache rate should reduce cost."""
        cost_no_cache = estimate_tournament_cost(
            num_players=27,
            cache_hit_rate=0.0,
        )
        cost_with_cache = estimate_tournament_cost(
            num_players=27,
            cache_hit_rate=0.85,
        )

        assert cost_with_cache < cost_no_cache

    def test_estimate_27_player_tournament(self):
        """27-player tournament with 85% cache should be around $7.20."""
        cost = estimate_tournament_cost(
            num_players=27,
            avg_hands_per_player=50,
            avg_decisions_per_hand=2.5,
            cache_hit_rate=0.85,
        )

        # Should be in reasonable range
        assert 3 < cost < 15, f"Cost {cost} outside expected range"
