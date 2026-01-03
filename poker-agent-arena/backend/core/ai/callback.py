"""Tournament decision callback factory.

Creates the decision callback that integrates the AI engine
with the tournament manager.
"""

from typing import Dict, Optional, Callable, Awaitable, List

from .engine import AIDecisionEngine, AgentConfig
from ..poker.betting import Action
from ..poker.hand_controller import HandState, HandController


# Type alias for the decision callback
DecisionCallback = Callable[[str, HandState], Awaitable[Action]]


def create_decision_callback(
    ai_engine: AIDecisionEngine,
    tournament_id: str,
    agent_configs: Dict[str, AgentConfig],
    get_hole_cards: Callable[[str], Optional[List[str]]],
    get_button_seat: Callable[[], int],
    get_ante: Callable[[], int],
    get_hand_number: Callable[[], int],
    get_action_history: Callable[[], Optional[List[dict]]],
) -> DecisionCallback:
    """Create a decision callback for tournament execution.

    This factory creates a callback compatible with TournamentManager.run()
    that delegates decisions to the AI engine.

    Args:
        ai_engine: The AI decision engine
        tournament_id: Tournament identifier
        agent_configs: Map of wallet -> AgentConfig for each player
        get_hole_cards: Function to get a player's hole cards
        get_button_seat: Function to get current button seat position
        get_ante: Function to get current ante amount
        get_hand_number: Function to get current hand number
        get_action_history: Function to get current action history

    Returns:
        Async callback function (wallet, HandState) -> Action
    """

    async def callback(wallet: str, hand_state: HandState) -> Action:
        """Decision callback for tournament.

        Args:
            wallet: Player's wallet address
            hand_state: Current hand state

        Returns:
            Action to take
        """
        # Get agent config or use defaults
        agent_config = agent_configs.get(
            wallet,
            AgentConfig(wallet=wallet)
        )

        # Get hole cards for this player
        hole_cards = get_hole_cards(wallet)
        if hole_cards is None:
            # No cards means player folded or error - fold
            return Action.fold()

        # Detect all-in situations for extended timeout
        is_all_in_decision = _is_significant_decision(hand_state, wallet)

        # Get decision from AI engine
        decision = await ai_engine.get_decision(
            wallet=wallet,
            hand_state=hand_state,
            agent_config=agent_config,
            tournament_id=tournament_id,
            hole_cards=hole_cards,
            button_seat=get_button_seat(),
            ante=get_ante(),
            hand_number=get_hand_number(),
            action_history=get_action_history(),
            is_all_in_decision=is_all_in_decision,
        )

        return decision.action

    return callback


def _is_significant_decision(hand_state: HandState, wallet: str) -> bool:
    """Determine if this is a significant decision warranting extra time.

    Significant decisions:
    - All-in situations (pot > 50% of stack)
    - Large bets relative to pot
    - Tournament-critical spots

    Args:
        hand_state: Current hand state
        wallet: Player's wallet

    Returns:
        True if decision deserves extended timeout
    """
    # Find player
    player = None
    for p in hand_state.players:
        if p["wallet"] == wallet:
            player = p
            break

    if player is None:
        return False

    stack = player["stack"]
    pot = hand_state.pot
    to_call = hand_state.current_bet - player["current_bet"]

    # All-in if call would be >= 50% of stack
    if to_call >= stack * 0.5:
        return True

    # Large pot relative to stack
    if pot >= stack * 0.75:
        return True

    # Short stack (< 20 BB effective)
    # Approximate BB from min_raise_to
    approx_bb = hand_state.min_raise_to // 2 if hand_state.min_raise_to > 0 else 100
    if stack < approx_bb * 20:
        return True

    return False


class TournamentAIIntegration:
    """Helper class for integrating AI with tournament execution.

    Manages the lifecycle of AI decision-making within a tournament,
    including callback creation and context management.
    """

    def __init__(
        self,
        ai_engine: AIDecisionEngine,
        tournament_id: str,
        agent_configs: Dict[str, AgentConfig],
    ):
        """Initialize tournament AI integration.

        Args:
            ai_engine: AI decision engine
            tournament_id: Tournament identifier
            agent_configs: Map of wallet -> AgentConfig
        """
        self.ai_engine = ai_engine
        self.tournament_id = tournament_id
        self.agent_configs = agent_configs

        # Current hand context
        self._current_controller: Optional[HandController] = None
        self._current_hand_number: int = 0
        self._button_seat: int = 0
        self._ante: int = 0

    def set_hand_context(
        self,
        controller: HandController,
        hand_number: int,
        button_seat: int,
        ante: int,
    ) -> None:
        """Set context for current hand.

        Args:
            controller: Current hand controller
            hand_number: Hand number
            button_seat: Button seat position
            ante: Current ante
        """
        self._current_controller = controller
        self._current_hand_number = hand_number
        self._button_seat = button_seat
        self._ante = ante

    def get_callback(self) -> DecisionCallback:
        """Get decision callback for current hand.

        Returns:
            Async callback function
        """
        def get_hole_cards(wallet: str) -> Optional[List[str]]:
            if self._current_controller is None:
                return None
            return self._current_controller.get_hole_cards(wallet)

        def get_button_seat() -> int:
            return self._button_seat

        def get_ante() -> int:
            return self._ante

        def get_hand_number() -> int:
            return self._current_hand_number

        def get_action_history() -> Optional[List[dict]]:
            if self._current_controller is None:
                return None
            return [
                {
                    "player_wallet": a.player_wallet,
                    "phase": a.phase.value,
                    "action_type": a.action_type,
                    "amount": a.amount,
                }
                for a in self._current_controller.actions
            ]

        return create_decision_callback(
            ai_engine=self.ai_engine,
            tournament_id=self.tournament_id,
            agent_configs=self.agent_configs,
            get_hole_cards=get_hole_cards,
            get_button_seat=get_button_seat,
            get_ante=get_ante,
            get_hand_number=get_hand_number,
            get_action_history=get_action_history,
        )

    def add_agent_config(self, wallet: str, config: AgentConfig) -> None:
        """Add or update agent configuration.

        Args:
            wallet: Player wallet
            config: Agent configuration
        """
        self.agent_configs[wallet] = config

    def get_agent_config(self, wallet: str) -> Optional[AgentConfig]:
        """Get agent configuration for a player.

        Args:
            wallet: Player wallet

        Returns:
            AgentConfig or None
        """
        return self.agent_configs.get(wallet)
