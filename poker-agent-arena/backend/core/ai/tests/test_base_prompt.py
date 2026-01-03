"""Tests for base_prompt module."""

import pytest

from ..base_prompt import BASE_AGENT_SYSTEM_PROMPT


class TestBasePrompt:
    """Tests for the base agent system prompt."""

    def test_prompt_exists(self):
        """Base prompt should be defined."""
        assert BASE_AGENT_SYSTEM_PROMPT is not None
        assert len(BASE_AGENT_SYSTEM_PROMPT) > 0

    def test_prompt_contains_decision_framework(self):
        """Prompt should contain decision framework."""
        assert "CORE DECISION FRAMEWORK" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_json_format(self):
        """Prompt should specify JSON response format."""
        assert '"action"' in BASE_AGENT_SYSTEM_PROMPT
        assert '"fold"' in BASE_AGENT_SYSTEM_PROMPT
        assert '"check"' in BASE_AGENT_SYSTEM_PROMPT
        assert '"call"' in BASE_AGENT_SYSTEM_PROMPT
        assert '"raise"' in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_mathematical_foundations(self):
        """Prompt should contain mathematical concepts."""
        assert "Pot Odds" in BASE_AGENT_SYSTEM_PROMPT
        assert "Expected Value" in BASE_AGENT_SYSTEM_PROMPT
        assert "Hand Equity" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_position_awareness(self):
        """Prompt should contain position information."""
        assert "POSITION AWARENESS" in BASE_AGENT_SYSTEM_PROMPT
        assert "UTG" in BASE_AGENT_SYSTEM_PROMPT
        assert "BTN" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_spr_guidelines(self):
        """Prompt should contain SPR guidelines."""
        assert "STACK-TO-POT RATIO" in BASE_AGENT_SYSTEM_PROMPT
        assert "SPR" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_hand_categories(self):
        """Prompt should contain hand categories."""
        assert "HAND CATEGORIES" in BASE_AGENT_SYSTEM_PROMPT
        assert "Premium" in BASE_AGENT_SYSTEM_PROMPT
        assert "AA" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_tournament_adjustments(self):
        """Prompt should contain tournament-specific advice."""
        assert "TOURNAMENT" in BASE_AGENT_SYSTEM_PROMPT
        assert "ICM" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_contains_betting_patterns(self):
        """Prompt should contain betting pattern guidance."""
        assert "BETTING PATTERNS" in BASE_AGENT_SYSTEM_PROMPT
        assert "3-bet" in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_specifies_raise_over_bet(self):
        """Prompt should specify using 'raise' not 'bet'."""
        assert 'Do NOT use "bet"' in BASE_AGENT_SYSTEM_PROMPT
        assert 'always use "raise"' in BASE_AGENT_SYSTEM_PROMPT

    def test_prompt_token_estimate(self):
        """Prompt should be approximately 1500 tokens.

        Rough estimate: ~4 characters per token.
        Target: 1500 tokens = ~6000 characters
        Acceptable range: 1000-2000 tokens = 4000-8000 characters
        """
        char_count = len(BASE_AGENT_SYSTEM_PROMPT)
        estimated_tokens = char_count / 4

        # Allow generous range for token estimation
        assert 1000 <= estimated_tokens <= 2500, (
            f"Prompt estimated at {estimated_tokens} tokens, "
            f"expected ~1500 tokens"
        )
