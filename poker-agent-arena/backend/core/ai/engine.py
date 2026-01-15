"""AI Decision Engine for poker tournaments.

Uses Claude (claude-sonnet-4-5-20250929) to make poker decisions with:
- System prompt caching for 85%+ token savings
- Timeout handling (5s normal, 10s all-in)
- Budget enforcement
- Decision logging
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import anthropic

from .base_prompt import BASE_AGENT_SYSTEM_PROMPT
from .context_builder import AgentTier, AgentSliders, build_custom_prompt
from .game_state_formatter import format_game_state
from .action_parser import parse_response, ActionParseError
from .budget import BudgetTracker
from .logging import DecisionLogger, DecisionLog

from ..poker.betting import Action
from ..poker.hand_controller import HandState


@dataclass
class Decision:
    """Result of an AI decision."""
    action: Action
    reasoning: str = ""  # For debugging, not sent to client
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    decision_time_ms: int = 0
    error: Optional[str] = None


@dataclass
class AgentConfig:
    """Configuration for a poker agent.

    For BASIC/PRO tiers, sliders are fetched from live settings at decision time.
    The custom_text is only used for PRO tier and is fetched from registration.
    """
    wallet: str
    tier: AgentTier = AgentTier.FREE
    sliders: AgentSliders = None  # type: ignore
    custom_text: str = ""

    def __post_init__(self):
        if self.sliders is None:
            self.sliders = AgentSliders()
        if isinstance(self.tier, str):
            self.tier = AgentTier(self.tier.upper())

    @classmethod
    def from_live_settings(
        cls,
        wallet: str,
        tier: str,
        aggression: int,
        tightness: int,
        custom_text: str = "",
    ) -> "AgentConfig":
        """Create AgentConfig from live settings.

        Args:
            wallet: Player wallet address
            tier: Agent tier (FREE, BASIC, PRO)
            aggression: Live aggression setting (1-10)
            tightness: Live tightness setting (1-10)
            custom_text: Custom prompt text (PRO tier only)

        Returns:
            AgentConfig with live slider values
        """
        return cls(
            wallet=wallet,
            tier=AgentTier(tier.upper()),
            sliders=AgentSliders(aggression=aggression, tightness=tightness),
            custom_text=custom_text,
        )


class AIDecisionEngine:
    """Makes poker decisions using Claude with prompt caching.

    Key optimizations:
    - System prompt caching (85% token savings)
    - Compressed game state format
    - Budget tracking per tournament
    - Timeout handling with conservative fallback
    """

    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    DEFAULT_TIMEOUT_NORMAL = 5
    DEFAULT_TIMEOUT_ALLIN = 10
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff

    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        budget_tracker: BudgetTracker,
        decision_logger: Optional[DecisionLogger] = None,
        model: str = DEFAULT_MODEL,
        timeout_normal: int = DEFAULT_TIMEOUT_NORMAL,
        timeout_allin: int = DEFAULT_TIMEOUT_ALLIN,
    ):
        """Initialize AI decision engine.

        Args:
            client: Anthropic async client
            budget_tracker: Budget tracker for cost management
            decision_logger: Optional decision logger for analytics
            model: Claude model to use
            timeout_normal: Timeout for normal decisions (seconds)
            timeout_allin: Timeout for all-in decisions (seconds)
        """
        self.client = client
        self.budget = budget_tracker
        self.logger = decision_logger
        self.model = model
        self.timeout_normal = timeout_normal
        self.timeout_allin = timeout_allin

    def _build_system_prompt(self, agent_config: AgentConfig) -> str:
        """Build full system prompt with customizations.

        Args:
            agent_config: Agent configuration

        Returns:
            Complete system prompt
        """
        custom_part = build_custom_prompt(
            tier=agent_config.tier,
            sliders=agent_config.sliders,
            custom_text=agent_config.custom_text,
        )

        if custom_part:
            return BASE_AGENT_SYSTEM_PROMPT + "\n" + custom_part

        return BASE_AGENT_SYSTEM_PROMPT

    async def get_decision(
        self,
        wallet: str,
        hand_state: HandState,
        agent_config: AgentConfig,
        tournament_id: str,
        hole_cards: List[str],
        button_seat: int,
        ante: int = 0,
        hand_number: int = 0,
        action_history: Optional[List[dict]] = None,
        is_all_in_decision: bool = False,
    ) -> Decision:
        """Get a decision for the given game state.

        Args:
            wallet: Player's wallet address
            hand_state: Current hand state
            agent_config: Agent configuration (tier, sliders, custom text)
            tournament_id: Tournament identifier for budget tracking
            hole_cards: Player's hole cards
            button_seat: Button seat position
            ante: Current ante amount
            hand_number: Hand number in tournament
            action_history: Action history for context
            is_all_in_decision: Whether this is an all-in decision (longer timeout)

        Returns:
            Decision with action and metadata
        """
        start_time = time.time()

        # Check budget
        if not await self.budget.can_make_call(tournament_id):
            return self._budget_exceeded_fallback(hand_state, wallet, start_time)

        # Build prompts
        system_prompt = self._build_system_prompt(agent_config)
        user_prompt = format_game_state(
            hand_state=hand_state,
            player_wallet=wallet,
            hole_cards=hole_cards,
            button_seat=button_seat,
            ante=ante,
            hand_number=hand_number,
            action_history=action_history,
        )

        # Determine timeout
        timeout = self.timeout_allin if is_all_in_decision else self.timeout_normal

        # Call Claude with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await asyncio.wait_for(
                    self._call_claude(system_prompt, user_prompt),
                    timeout=timeout,
                )

                # Parse response
                decision = self._process_response(
                    response=response,
                    hand_state=hand_state,
                    wallet=wallet,
                    start_time=start_time,
                )

                # Record usage
                await self.budget.record_usage(
                    tournament_id=tournament_id,
                    input_tokens=decision.input_tokens,
                    output_tokens=decision.output_tokens,
                    cache_read_tokens=decision.cache_read_tokens,
                )

                # Log decision
                if self.logger:
                    await self._log_decision(
                        decision=decision,
                        tournament_id=tournament_id,
                        hand_state=hand_state,
                        wallet=wallet,
                        hand_number=hand_number,
                    )

                return decision

            except asyncio.TimeoutError:
                if attempt == self.MAX_RETRIES - 1:
                    return self._timeout_fallback(hand_state, wallet, start_time)
                # Continue to retry

            except anthropic.RateLimitError:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAYS[attempt])
                else:
                    return self._error_fallback(
                        hand_state, wallet, start_time, "Rate limit exceeded"
                    )

            except anthropic.APIError as e:
                return self._error_fallback(
                    hand_state, wallet, start_time, str(e)
                )

        return self._error_fallback(
            hand_state, wallet, start_time, "Max retries exceeded"
        )

    async def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> anthropic.types.Message:
        """Call Claude API with prompt caching.

        Args:
            system_prompt: Full system prompt
            user_prompt: Game state prompt

        Returns:
            Claude API response
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=100,  # Responses are short JSON
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )
        return response

    def _process_response(
        self,
        response: anthropic.types.Message,
        hand_state: HandState,
        wallet: str,
        start_time: float,
    ) -> Decision:
        """Process Claude response into a Decision.

        Args:
            response: Claude API response
            hand_state: Current hand state
            wallet: Player wallet
            start_time: Request start time

        Returns:
            Decision with parsed action
        """
        decision_time_ms = int((time.time() - start_time) * 1000)

        # Extract text content
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text = block.text
                break

        # Parse action
        try:
            action = parse_response(response_text, hand_state, wallet)
        except ActionParseError:
            # Fallback on parse error
            action = self._get_conservative_action(hand_state, wallet)

        # Get usage stats
        usage = response.usage
        cache_read_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0

        return Decision(
            action=action,
            reasoning=response_text,
            input_tokens=usage.input_tokens - cache_read_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=cache_read_tokens,
            decision_time_ms=decision_time_ms,
        )

    def _get_conservative_action(
        self,
        hand_state: HandState,
        wallet: str,
    ) -> Action:
        """Get conservative fallback action.

        Check if possible, otherwise fold.
        """
        for player in hand_state.players:
            if player["wallet"] == wallet:
                if hand_state.current_bet <= player["current_bet"]:
                    return Action.check()
                break
        return Action.fold()

    def _budget_exceeded_fallback(
        self,
        hand_state: HandState,
        wallet: str,
        start_time: float,
    ) -> Decision:
        """Fallback when budget is exceeded."""
        decision_time_ms = int((time.time() - start_time) * 1000)
        action = self._get_conservative_action(hand_state, wallet)

        return Decision(
            action=action,
            reasoning="Budget exceeded",
            decision_time_ms=decision_time_ms,
            error="budget_exceeded",
        )

    def _timeout_fallback(
        self,
        hand_state: HandState,
        wallet: str,
        start_time: float,
    ) -> Decision:
        """Fallback when API times out."""
        decision_time_ms = int((time.time() - start_time) * 1000)
        action = self._get_conservative_action(hand_state, wallet)

        return Decision(
            action=action,
            reasoning="API timeout",
            decision_time_ms=decision_time_ms,
            error="timeout",
        )

    def _error_fallback(
        self,
        hand_state: HandState,
        wallet: str,
        start_time: float,
        error: str,
    ) -> Decision:
        """Fallback on API error."""
        decision_time_ms = int((time.time() - start_time) * 1000)
        action = self._get_conservative_action(hand_state, wallet)

        return Decision(
            action=action,
            reasoning=f"Error: {error}",
            decision_time_ms=decision_time_ms,
            error=error,
        )

    async def _log_decision(
        self,
        decision: Decision,
        tournament_id: str,
        hand_state: HandState,
        wallet: str,
        hand_number: int,
    ) -> None:
        """Log decision for analytics."""
        if self.logger is None:
            return

        # Get player info
        player = None
        for p in hand_state.players:
            if p["wallet"] == wallet:
                player = p
                break

        if player is None:
            return

        # Determine position (simplified)
        position = f"seat_{player.get('seat_position', 0)}"

        # Calculate to-call
        to_call = hand_state.current_bet - player["current_bet"]

        log = DecisionLog(
            tournament_id=tournament_id,
            hand_id=hand_state.hand_id,
            wallet=wallet,
            position=position,
            betting_round=hand_state.phase.value,
            action=decision.action.action_type,
            amount=decision.action.amount,
            pot_size=hand_state.pot,
            to_call=to_call,
            stack_size=player["stack"],
            decision_time_ms=decision.decision_time_ms,
            input_tokens=decision.input_tokens,
            output_tokens=decision.output_tokens,
            cache_read_tokens=decision.cache_read_tokens,
            cache_hit=decision.cache_read_tokens > 0,
            error=decision.error,
        )

        await self.logger.log_decision(log)
