"""Custom prompt builder for tiered agent configurations.

Tier system:
- FREE (0 SOL): Base engine only, no customization
- BASIC (0.1 SOL): Sliders only, no freeform text
- PRO (1 SOL): Sliders + unlimited freeform strategy prompt
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union


class AgentTier(Enum):
    """Agent subscription tiers."""
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"


@dataclass
class AgentSliders:
    """Structured personality parameters (0-100 scale).

    Attributes:
        aggression: Low = passive, High = aggressive betting
        bluff_frequency: How often to bluff (0=never, 100=frequently)
        tightness: Low = loose (plays many hands), High = tight (selective)
        position_awareness: Weight of position in decisions
    """
    aggression: int = 50
    bluff_frequency: int = 30
    tightness: int = 50
    position_awareness: int = 70

    def __post_init__(self) -> None:
        """Validate slider values are in range."""
        for field_name in ["aggression", "bluff_frequency", "tightness", "position_awareness"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0 or value > 100:
                raise ValueError(f"{field_name} must be an integer between 0 and 100, got {value}")


def _get_aggression_label(value: int) -> str:
    """Get descriptive label for aggression level."""
    if value > 70:
        return "(very aggressive)"
    elif value > 30:
        return "(balanced)"
    else:
        return "(passive)"


def _get_bluff_label(value: int) -> str:
    """Get descriptive label for bluff frequency."""
    if value > 50:
        return "(frequent bluffer)"
    else:
        return "(selective bluffer)"


def _get_tightness_label(value: int) -> str:
    """Get descriptive label for tightness."""
    if value > 70:
        return "(very tight)"
    elif value > 30:
        return "(balanced)"
    else:
        return "(loose)"


def build_custom_prompt(
    tier: AgentTier | str,
    sliders: AgentSliders,
    custom_text: str = "",
) -> str:
    """Build the custom portion of agent prompt.

    Args:
        tier: Agent tier (FREE, BASIC, PRO)
        sliders: Personality slider configuration
        custom_text: Custom strategy text (PRO tier only)

    Returns:
        Custom prompt string to append to base prompt.
        Empty string for FREE tier.
    """
    # Handle string tier input
    if isinstance(tier, str):
        tier = AgentTier(tier.upper())

    if tier == AgentTier.FREE:
        return ""

    # Build slider prompt
    slider_prompt = f"""
## PERSONALITY PARAMETERS

Your playing style is calibrated as follows:
- Aggression Level: {sliders.aggression}/100 {_get_aggression_label(sliders.aggression)}
- Bluff Frequency: {sliders.bluff_frequency}/100 {_get_bluff_label(sliders.bluff_frequency)}
- Hand Selection: {sliders.tightness}/100 {_get_tightness_label(sliders.tightness)}
- Position Weight: {sliders.position_awareness}/100

Adjust your decisions according to these parameters while maintaining mathematically sound play.
"""

    if tier == AgentTier.BASIC:
        # BASIC tier: sliders only, no freeform text
        return slider_prompt

    # PRO tier: sliders + freeform text
    if custom_text.strip():
        user_prompt = f"""
## CUSTOM INSTRUCTIONS FROM OWNER

{custom_text}
"""
        return slider_prompt + user_prompt

    return slider_prompt
