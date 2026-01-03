"""AI decision engine for poker agent arena.

This module provides Claude-based poker decision making with:
- Cached system prompts for cost optimization
- Tiered customization (FREE, BASIC, PRO)
- Budget tracking per tournament
- Action parsing and validation
"""

from .base_prompt import BASE_AGENT_SYSTEM_PROMPT
from .context_builder import AgentSliders, AgentTier, build_custom_prompt
from .game_state_formatter import format_game_state
from .action_parser import parse_response, ActionParseError
from .budget import BudgetTracker
from .engine import AIDecisionEngine, Decision
from .callback import create_decision_callback

__all__ = [
    "BASE_AGENT_SYSTEM_PROMPT",
    "AgentSliders",
    "AgentTier",
    "build_custom_prompt",
    "format_game_state",
    "parse_response",
    "ActionParseError",
    "BudgetTracker",
    "AIDecisionEngine",
    "Decision",
    "create_decision_callback",
]
