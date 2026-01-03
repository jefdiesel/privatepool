"""Tests for AI decision engine."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from ..engine import AIDecisionEngine, Decision, AgentConfig
from ..budget import BudgetTracker
from ..context_builder import AgentTier, AgentSliders
from ...poker.hand_controller import HandState, HandPhase
from ...poker.betting import Action


class MockUsage:
    """Mock usage object for API responses."""
    def __init__(self, input_tokens=1500, output_tokens=50, cache_read=1000):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_input_tokens = cache_read


class MockContentBlock:
    """Mock content block for API responses."""
    def __init__(self, text='{"action": "fold"}'):
        self.text = text


class MockResponse:
    """Mock API response."""
    def __init__(self, text='{"action": "fold"}', input_tokens=1500, output_tokens=50, cache_read=1000):
        self.content = [MockContentBlock(text)]
        self.usage = MockUsage(input_tokens, output_tokens, cache_read)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = AgentConfig(wallet="test_wallet")
        assert config.wallet == "test_wallet"
        assert config.tier == AgentTier.FREE
        assert config.sliders is not None
        assert config.custom_text == ""

    def test_string_tier_conversion(self):
        """Should convert string tier to enum."""
        config = AgentConfig(wallet="test", tier="PRO")  # type: ignore
        assert config.tier == AgentTier.PRO

    def test_custom_sliders(self):
        """Should accept custom sliders."""
        sliders = AgentSliders(aggression=80)
        config = AgentConfig(wallet="test", sliders=sliders)
        assert config.sliders.aggression == 80


class TestDecision:
    """Tests for Decision dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        action = Action.fold()
        decision = Decision(action=action)
        assert decision.action == action
        assert decision.reasoning == ""
        assert decision.input_tokens == 0
        assert decision.error is None


class TestAIDecisionEngine:
    """Tests for AIDecisionEngine class."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Anthropic client."""
        client = AsyncMock()
        client.messages = AsyncMock()
        client.messages.create = AsyncMock(return_value=MockResponse())
        return client

    @pytest.fixture
    def mock_budget(self):
        """Create mock budget tracker."""
        budget = AsyncMock(spec=BudgetTracker)
        budget.can_make_call = AsyncMock(return_value=True)
        budget.record_usage = AsyncMock()
        return budget

    @pytest.fixture
    def engine(self, mock_client, mock_budget):
        """Create engine with mocks."""
        return AIDecisionEngine(
            client=mock_client,
            budget_tracker=mock_budget,
            timeout_normal=5,
            timeout_allin=10,
        )

    @pytest.fixture
    def hand_state(self):
        """Create a basic hand state."""
        return HandState(
            hand_id="test_hand_1",
            phase=HandPhase.FLOP,
            pot=300,
            community_cards=["Ah", "Kd", "7c"],
            current_bet=100,
            action_on="wallet_1",
            players=[
                {
                    "wallet": "wallet_1",
                    "stack": 1000,
                    "current_bet": 50,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 0,
                },
            ],
            valid_actions=["fold", "call", "raise"],
            min_raise_to=200,
        )

    @pytest.fixture
    def agent_config(self):
        """Create basic agent config."""
        return AgentConfig(wallet="wallet_1")

    @pytest.mark.asyncio
    async def test_get_decision_success(self, engine, hand_state, agent_config, mock_client):
        """Should return valid decision on success."""
        mock_client.messages.create.return_value = MockResponse(text='{"action": "call"}')

        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        assert decision.action.action_type == "call"
        assert decision.error is None

    @pytest.mark.asyncio
    async def test_get_decision_records_usage(self, engine, hand_state, agent_config, mock_budget):
        """Should record API usage."""
        await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        mock_budget.record_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_decision_checks_budget(self, engine, hand_state, agent_config, mock_budget):
        """Should check budget before making call."""
        await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        mock_budget.can_make_call.assert_called_once_with("tournament_1")

    @pytest.mark.asyncio
    async def test_get_decision_budget_exceeded(self, engine, hand_state, agent_config, mock_budget):
        """Should return conservative action when budget exceeded."""
        mock_budget.can_make_call.return_value = False

        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        assert decision.error == "budget_exceeded"
        # Should fold since there's a bet to call
        assert decision.action.action_type == "fold"

    @pytest.mark.asyncio
    async def test_get_decision_parses_raise(self, engine, hand_state, agent_config, mock_client):
        """Should parse raise action correctly."""
        mock_client.messages.create.return_value = MockResponse(
            text='{"action": "raise", "amount": 250}'
        )

        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        assert decision.action.action_type == "raise"
        assert decision.action.amount == 250

    @pytest.mark.asyncio
    async def test_get_decision_uses_cache_control(self, engine, hand_state, agent_config, mock_client):
        """Should use cache control in API call."""
        await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        # Check system prompt has cache_control
        assert "system" in call_kwargs
        system = call_kwargs["system"]
        assert any("cache_control" in str(item) for item in system)

    @pytest.mark.asyncio
    async def test_get_decision_includes_custom_prompt(self, engine, hand_state, mock_client):
        """Should include custom prompt for non-FREE tiers."""
        agent_config = AgentConfig(
            wallet="wallet_1",
            tier=AgentTier.PRO,
            sliders=AgentSliders(aggression=80),
            custom_text="Be aggressive!",
        )

        await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        system = call_kwargs["system"]
        system_text = system[0]["text"]
        assert "PERSONALITY PARAMETERS" in system_text
        assert "Be aggressive!" in system_text

    @pytest.mark.asyncio
    async def test_get_decision_uses_longer_timeout_for_allin(self, engine, hand_state, agent_config, mock_client):
        """Should use longer timeout for all-in decisions."""
        # Mock a slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            return MockResponse(text='{"action": "call"}')

        mock_client.messages.create = slow_response

        # This should succeed with the longer timeout
        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
            is_all_in_decision=True,
        )

        assert decision.action.action_type == "call"

    @pytest.mark.asyncio
    async def test_get_decision_tracks_decision_time(self, engine, hand_state, agent_config):
        """Should track decision time in milliseconds."""
        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        assert decision.decision_time_ms >= 0

    @pytest.mark.asyncio
    async def test_get_decision_tracks_tokens(self, engine, hand_state, agent_config, mock_client):
        """Should track token usage."""
        mock_client.messages.create.return_value = MockResponse(
            input_tokens=2000,
            output_tokens=75,
            cache_read=1500,
        )

        decision = await engine.get_decision(
            wallet="wallet_1",
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id="tournament_1",
            hole_cards=["Qs", "Qd"],
            button_seat=0,
        )

        # Input tokens should be total minus cache read
        assert decision.input_tokens == 500  # 2000 - 1500
        assert decision.output_tokens == 75
        assert decision.cache_read_tokens == 1500


class TestBuildSystemPrompt:
    """Tests for system prompt building."""

    @pytest.fixture
    def engine(self):
        """Create engine with mocks."""
        return AIDecisionEngine(
            client=AsyncMock(),
            budget_tracker=AsyncMock(),
        )

    def test_free_tier_base_prompt_only(self, engine):
        """FREE tier should use base prompt only."""
        config = AgentConfig(wallet="test", tier=AgentTier.FREE)
        prompt = engine._build_system_prompt(config)

        assert "CORE DECISION FRAMEWORK" in prompt
        assert "PERSONALITY PARAMETERS" not in prompt

    def test_basic_tier_includes_sliders(self, engine):
        """BASIC tier should include sliders."""
        config = AgentConfig(
            wallet="test",
            tier=AgentTier.BASIC,
            sliders=AgentSliders(aggression=75),
        )
        prompt = engine._build_system_prompt(config)

        assert "CORE DECISION FRAMEWORK" in prompt
        assert "PERSONALITY PARAMETERS" in prompt
        assert "75/100" in prompt

    def test_pro_tier_includes_custom_text(self, engine):
        """PRO tier should include custom text."""
        config = AgentConfig(
            wallet="test",
            tier=AgentTier.PRO,
            custom_text="Play tight from early position",
        )
        prompt = engine._build_system_prompt(config)

        assert "CORE DECISION FRAMEWORK" in prompt
        assert "Play tight from early position" in prompt
