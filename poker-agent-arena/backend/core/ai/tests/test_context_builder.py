"""Tests for context_builder module."""

import pytest

from ..context_builder import (
    AgentTier,
    AgentSliders,
    build_custom_prompt,
)


class TestAgentSliders:
    """Tests for AgentSliders dataclass."""

    def test_default_values(self):
        """Default slider values should be set."""
        sliders = AgentSliders()
        assert sliders.aggression == 50
        assert sliders.bluff_frequency == 30
        assert sliders.tightness == 50
        assert sliders.position_awareness == 70

    def test_custom_values(self):
        """Custom values should be accepted."""
        sliders = AgentSliders(
            aggression=80,
            bluff_frequency=60,
            tightness=30,
            position_awareness=90,
        )
        assert sliders.aggression == 80
        assert sliders.bluff_frequency == 60
        assert sliders.tightness == 30
        assert sliders.position_awareness == 90

    def test_validation_too_low(self):
        """Values below 0 should raise error."""
        with pytest.raises(ValueError):
            AgentSliders(aggression=-1)

    def test_validation_too_high(self):
        """Values above 100 should raise error."""
        with pytest.raises(ValueError):
            AgentSliders(aggression=101)

    def test_validation_non_integer(self):
        """Non-integer values should raise error."""
        with pytest.raises(ValueError):
            AgentSliders(aggression="fifty")  # type: ignore

    def test_boundary_values(self):
        """Boundary values 0 and 100 should be valid."""
        sliders = AgentSliders(
            aggression=0,
            bluff_frequency=100,
            tightness=0,
            position_awareness=100,
        )
        assert sliders.aggression == 0
        assert sliders.bluff_frequency == 100


class TestAgentTier:
    """Tests for AgentTier enum."""

    def test_free_tier(self):
        """FREE tier should exist."""
        assert AgentTier.FREE.value == "FREE"

    def test_basic_tier(self):
        """BASIC tier should exist."""
        assert AgentTier.BASIC.value == "BASIC"

    def test_pro_tier(self):
        """PRO tier should exist."""
        assert AgentTier.PRO.value == "PRO"


class TestBuildCustomPrompt:
    """Tests for build_custom_prompt function."""

    def test_free_tier_returns_empty(self):
        """FREE tier should return empty string."""
        sliders = AgentSliders()
        result = build_custom_prompt(AgentTier.FREE, sliders, "custom text")
        assert result == ""

    def test_free_tier_string_input(self):
        """FREE tier should work with string input."""
        sliders = AgentSliders()
        result = build_custom_prompt("FREE", sliders, "custom text")
        assert result == ""

    def test_basic_tier_includes_sliders(self):
        """BASIC tier should include slider info."""
        sliders = AgentSliders(aggression=80)
        result = build_custom_prompt(AgentTier.BASIC, sliders, "")

        assert "PERSONALITY PARAMETERS" in result
        assert "80/100" in result
        assert "Aggression Level" in result

    def test_basic_tier_no_custom_text(self):
        """BASIC tier should not include custom text."""
        sliders = AgentSliders()
        result = build_custom_prompt(AgentTier.BASIC, sliders, "my custom strategy")

        assert "my custom strategy" not in result
        assert "CUSTOM INSTRUCTIONS" not in result

    def test_pro_tier_includes_sliders(self):
        """PRO tier should include slider info."""
        sliders = AgentSliders(tightness=90)
        result = build_custom_prompt(AgentTier.PRO, sliders, "custom text")

        assert "PERSONALITY PARAMETERS" in result
        assert "90/100" in result
        assert "Hand Selection" in result

    def test_pro_tier_includes_custom_text(self):
        """PRO tier should include custom text."""
        sliders = AgentSliders()
        result = build_custom_prompt(AgentTier.PRO, sliders, "Play aggressively preflop")

        assert "CUSTOM INSTRUCTIONS FROM OWNER" in result
        assert "Play aggressively preflop" in result

    def test_pro_tier_empty_custom_text(self):
        """PRO tier with empty custom text should not include custom section."""
        sliders = AgentSliders()
        result = build_custom_prompt(AgentTier.PRO, sliders, "")

        assert "PERSONALITY PARAMETERS" in result
        assert "CUSTOM INSTRUCTIONS" not in result

    def test_pro_tier_whitespace_custom_text(self):
        """PRO tier with whitespace-only custom text should not include custom section."""
        sliders = AgentSliders()
        result = build_custom_prompt(AgentTier.PRO, sliders, "   \n   ")

        assert "PERSONALITY PARAMETERS" in result
        assert "CUSTOM INSTRUCTIONS" not in result

    def test_aggression_labels(self):
        """Aggression labels should be correct."""
        sliders_passive = AgentSliders(aggression=20)
        sliders_balanced = AgentSliders(aggression=50)
        sliders_aggressive = AgentSliders(aggression=80)

        result_passive = build_custom_prompt(AgentTier.BASIC, sliders_passive, "")
        result_balanced = build_custom_prompt(AgentTier.BASIC, sliders_balanced, "")
        result_aggressive = build_custom_prompt(AgentTier.BASIC, sliders_aggressive, "")

        assert "(passive)" in result_passive
        assert "(balanced)" in result_balanced
        assert "(very aggressive)" in result_aggressive

    def test_bluff_labels(self):
        """Bluff frequency labels should be correct."""
        sliders_selective = AgentSliders(bluff_frequency=30)
        sliders_frequent = AgentSliders(bluff_frequency=60)

        result_selective = build_custom_prompt(AgentTier.BASIC, sliders_selective, "")
        result_frequent = build_custom_prompt(AgentTier.BASIC, sliders_frequent, "")

        assert "(selective bluffer)" in result_selective
        assert "(frequent bluffer)" in result_frequent

    def test_tightness_labels(self):
        """Tightness labels should be correct."""
        sliders_loose = AgentSliders(tightness=20)
        sliders_balanced = AgentSliders(tightness=50)
        sliders_tight = AgentSliders(tightness=80)

        result_loose = build_custom_prompt(AgentTier.BASIC, sliders_loose, "")
        result_balanced = build_custom_prompt(AgentTier.BASIC, sliders_balanced, "")
        result_tight = build_custom_prompt(AgentTier.BASIC, sliders_tight, "")

        assert "(loose)" in result_loose
        assert "(balanced)" in result_balanced
        assert "(very tight)" in result_tight

    def test_string_tier_case_insensitive(self):
        """String tier input should be case insensitive."""
        sliders = AgentSliders()

        result_lower = build_custom_prompt("basic", sliders, "")
        result_upper = build_custom_prompt("BASIC", sliders, "")
        result_mixed = build_custom_prompt("Basic", sliders, "")

        assert "PERSONALITY PARAMETERS" in result_lower
        assert "PERSONALITY PARAMETERS" in result_upper
        assert "PERSONALITY PARAMETERS" in result_mixed
