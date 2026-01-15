"""Custom prompt builder for tiered agent configurations.

Tier system:
- FREE (0 SOL): Base engine only, no customization
- BASIC (0.1 SOL): Real-time sliders during live tournament play
- PRO (1 SOL): Real-time sliders + custom freeform strategy prompt
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
    """Personality parameters (1-10 scale).

    Attributes:
        aggression: 1 = passive (checking/calling), 10 = aggressive (betting/raising)
        tightness: 1 = loose (plays many hands), 10 = tight (selective hands)

    Default is 5,5 (balanced play style).
    """
    aggression: int = 5
    tightness: int = 5

    def __post_init__(self) -> None:
        """Validate slider values are in range (1-10 integers only)."""
        for field_name in ["aggression", "tightness"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 1 or value > 10:
                raise ValueError(f"{field_name} must be an integer between 1 and 10, got {value}")


def _get_aggression_label(value: int) -> str:
    """Get descriptive label for aggression level (1-10 scale)."""
    if value >= 8:
        return "(very aggressive - frequently bet and raise)"
    elif value >= 6:
        return "(moderately aggressive)"
    elif value >= 4:
        return "(balanced)"
    elif value >= 2:
        return "(moderately passive)"
    else:
        return "(very passive - prefer checking and calling)"


def _get_tightness_label(value: int) -> str:
    """Get descriptive label for tightness (1-10 scale)."""
    if value >= 8:
        return "(very tight - only play premium hands)"
    elif value >= 6:
        return "(moderately tight)"
    elif value >= 4:
        return "(balanced hand selection)"
    elif value >= 2:
        return "(moderately loose)"
    else:
        return "(very loose - play a wide range of hands)"


def build_custom_prompt(
    tier: AgentTier | str,
    sliders: AgentSliders,
    custom_text: str = "",
) -> str:
    """Build the custom portion of agent prompt.

    Args:
        tier: Agent tier (FREE, BASIC, PRO)
        sliders: Personality slider configuration (aggression and tightness, 1-10 scale)
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

    # Build slider prompt with 1-10 scale
    slider_prompt = f"""
## PERSONALITY PARAMETERS

Your playing style is calibrated as follows:

**Aggression Level: {sliders.aggression}/10** {_get_aggression_label(sliders.aggression)}
- Higher values mean you should bet and raise more frequently
- Lower values mean you should check and call more often

**Hand Selection (Tightness): {sliders.tightness}/10** {_get_tightness_label(sliders.tightness)}
- Higher values mean you should be more selective, only playing strong starting hands
- Lower values mean you should play a wider range of hands

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
