"""Hand controller module for orchestrating complete poker hands.

Manages the full lifecycle of a single poker hand from deal to showdown.
Integrates deck, betting, hand evaluation, and side pot calculation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable, Optional, List, Dict

from .deck import Deck
from .hand_evaluator import HandEvaluator, EvaluatedHand
from .betting import BettingRound, PlayerInHand, Action, ActionType, InvalidActionError
from .side_pots import SidePotCalculator, SidePot


class HandPhase(Enum):
    """Phases of a poker hand."""
    WAITING = "waiting"
    POSTING_BLINDS = "posting_blinds"
    DEALING = "dealing"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    COMPLETE = "complete"


@dataclass
class HandAction:
    """Record of a player action during the hand."""
    player_wallet: str
    phase: HandPhase
    action_type: str  # fold, check, call, raise, post_sb, post_bb, post_ante
    amount: int = 0
    timestamp_ms: int = 0


@dataclass
class HandResult:
    """Result of a completed hand."""
    winners: Dict[str, int]  # wallet -> amount won
    pot_total: int
    final_hands: Dict[str, EvaluatedHand]  # wallet -> evaluated hand (showdown only)
    side_pots: List[SidePot]
    eliminations: List[str]  # Players eliminated this hand
    actions: List[HandAction]


@dataclass
class HandState:
    """Current state of a hand for external observation."""
    hand_id: str
    phase: HandPhase
    pot: int
    community_cards: List[str]
    current_bet: int
    action_on: Optional[str]  # Wallet of player to act
    players: List[dict]  # List of player states (wallet, stack, current_bet, is_active, is_all_in)
    valid_actions: List[ActionType]
    min_raise_to: int


@dataclass
class PlayerConfig:
    """Configuration for a player entering a hand."""
    wallet: str
    stack: int
    seat_position: int


# Type for the decision callback
DecisionCallback = Callable[[HandState], Awaitable[Action]]


class HandController:
    """Orchestrates a complete poker hand from deal to showdown.

    State machine:
    WAITING -> POSTING_BLINDS -> DEALING -> PREFLOP -> FLOP -> TURN -> RIVER -> SHOWDOWN -> COMPLETE

    Can short-circuit to COMPLETE at any point if all players fold.

    Usage:
        controller = HandController(
            hand_id="hand_1",
            players=[PlayerConfig(wallet="...", stack=1000, seat_position=0), ...],
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"...",
        )

        result = await controller.run(decision_callback)
    """

    def __init__(
        self,
        hand_id: str,
        players: List[PlayerConfig],
        button_position: int,
        small_blind: int,
        big_blind: int,
        ante: int,
        deck_seed: bytes,
    ):
        """Initialize hand controller.

        Args:
            hand_id: Unique identifier for this hand
            players: List of PlayerConfig (must be in seat order)
            button_position: Index of player with button
            small_blind: Small blind amount
            big_blind: Big blind amount
            ante: Ante amount (paid by BB only, per spec)
            deck_seed: Seed for provably fair deck shuffle
        """
        if len(players) < 2:
            raise ValueError("Need at least 2 players for a hand")

        self.hand_id = hand_id
        self.button_position = button_position
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.ante = ante  # Paid by BB only

        # Initialize deck with provably fair seed
        self.deck = Deck(deck_seed)

        # Initialize player states (sorted by seat position)
        sorted_players = sorted(players, key=lambda p: p.seat_position)
        self.players: List[PlayerInHand] = [
            PlayerInHand(
                wallet=p.wallet,
                stack=p.stack,
                current_bet=0,
                is_active=True,
                is_all_in=False,
                has_acted=False,
            )
            for p in sorted_players
        ]
        self.seat_positions = {p.wallet: p.seat_position for p in sorted_players}

        # Map wallet to player index
        self.wallet_to_idx = {p.wallet: i for i, p in enumerate(self.players)}

        # Hole cards per player
        self.hole_cards: Dict[str, List[str]] = {}

        # Community cards
        self.community_cards: List[str] = []

        # Action history
        self.actions: List[HandAction] = []

        # Current phase
        self.phase = HandPhase.WAITING

        # Current betting round
        self.betting_round: Optional[BettingRound] = None

        # Total pot
        self.pot = 0

        # Track current bet for the hand
        self.current_bet = 0

        # Hand evaluator
        self.evaluator = HandEvaluator()

        # Side pot calculator
        self.pot_calculator = SidePotCalculator()

    def _get_sb_player_idx(self) -> int:
        """Get index of small blind player."""
        num_players = len(self.players)
        if num_players == 2:
            # Heads-up: button is small blind
            return self.button_position
        else:
            # 3+ players: first active player left of button
            return (self.button_position + 1) % num_players

    def _get_bb_player_idx(self) -> int:
        """Get index of big blind player."""
        num_players = len(self.players)
        if num_players == 2:
            # Heads-up: other player is big blind
            return (self.button_position + 1) % num_players
        else:
            # 3+ players: second active player left of button
            return (self.button_position + 2) % num_players

    def _get_preflop_action_idx(self) -> int:
        """Get index of first player to act preflop (UTG)."""
        num_players = len(self.players)
        if num_players == 2:
            # Heads-up: button acts first preflop
            return self.button_position
        else:
            # 3+ players: player left of BB acts first
            return (self.button_position + 3) % num_players

    def _get_postflop_action_idx(self) -> int:
        """Get index of first player to act postflop (first active left of button)."""
        num_players = len(self.players)
        for i in range(1, num_players + 1):
            idx = (self.button_position + i) % num_players
            if self.players[idx].is_active and not self.players[idx].is_all_in:
                return idx
        return 0

    def _post_blinds(self) -> None:
        """Post blinds and ante."""
        self.phase = HandPhase.POSTING_BLINDS

        sb_idx = self._get_sb_player_idx()
        bb_idx = self._get_bb_player_idx()

        sb_player = self.players[sb_idx]
        bb_player = self.players[bb_idx]

        # Post small blind
        sb_amount = min(self.small_blind, sb_player.stack)
        sb_player.stack -= sb_amount
        sb_player.current_bet = sb_amount
        self.pot += sb_amount
        if sb_player.stack == 0:
            sb_player.is_all_in = True

        self.actions.append(HandAction(
            player_wallet=sb_player.wallet,
            phase=self.phase,
            action_type="post_sb",
            amount=sb_amount,
        ))

        # Post big blind + ante (BB pays ante per spec)
        bb_total = self.big_blind + self.ante
        bb_amount = min(bb_total, bb_player.stack)
        bb_player.stack -= bb_amount
        bb_player.current_bet = bb_amount
        self.pot += bb_amount
        if bb_player.stack == 0:
            bb_player.is_all_in = True

        self.actions.append(HandAction(
            player_wallet=bb_player.wallet,
            phase=self.phase,
            action_type="post_bb",
            amount=bb_amount,
        ))

        if self.ante > 0:
            self.actions.append(HandAction(
                player_wallet=bb_player.wallet,
                phase=self.phase,
                action_type="post_ante",
                amount=min(self.ante, bb_amount),
            ))

        # Set current bet level
        self.current_bet = max(sb_player.current_bet, bb_player.current_bet)

    def _deal_hole_cards(self) -> None:
        """Deal hole cards to all players."""
        self.phase = HandPhase.DEALING

        for player in self.players:
            cards = self.deck.deal(2)
            self.hole_cards[player.wallet] = cards

    def _deal_community_cards(self, count: int) -> None:
        """Deal community cards (burn one first)."""
        # Burn a card
        self.deck.deal(1)
        # Deal community cards
        new_cards = self.deck.deal(count)
        self.community_cards.extend(new_cards)

    def _count_active_players(self) -> int:
        """Count players still in the hand."""
        return sum(1 for p in self.players if p.is_active)

    def _count_players_can_act(self) -> int:
        """Count players who can still take actions (not all-in, not folded)."""
        return sum(1 for p in self.players if p.is_active and not p.is_all_in)

    def _is_hand_over(self) -> bool:
        """Check if hand is over (only one player left)."""
        return self._count_active_players() <= 1

    def _all_in_showdown(self) -> bool:
        """Check if remaining players are all-in and no more betting possible."""
        active = [p for p in self.players if p.is_active]
        if len(active) <= 1:
            return False
        # All-in showdown if all active players are all-in or only one can act
        can_act = sum(1 for p in active if not p.is_all_in)
        return can_act <= 1

    def _reset_bets_for_new_round(self) -> None:
        """Reset current bets for a new betting round."""
        for player in self.players:
            player.current_bet = 0
            player.has_acted = False
        self.current_bet = 0

    def _reorder_players_for_betting(self, first_to_act_idx: int) -> List[PlayerInHand]:
        """Reorder player list so first_to_act_idx is first."""
        n = len(self.players)
        return [self.players[(first_to_act_idx + i) % n] for i in range(n)]

    def get_state(self) -> HandState:
        """Get current observable hand state."""
        action_on_wallet = None
        valid_actions: List[ActionType] = []
        min_raise_to = self.current_bet + self.big_blind

        if self.betting_round and not self.betting_round.is_round_complete():
            action_on_idx = self.betting_round.state.action_on
            # Map back to original player
            reordered_player = self.betting_round.state.players[action_on_idx]
            action_on_wallet = reordered_player.wallet
            valid_actions = self.betting_round.get_valid_actions()
            min_raise_to = self.betting_round.state.current_bet + self.betting_round.state.min_raise

        player_states = [
            {
                "wallet": p.wallet,
                "stack": p.stack,
                "current_bet": p.current_bet,
                "is_active": p.is_active,
                "is_all_in": p.is_all_in,
                "seat_position": self.seat_positions[p.wallet],
            }
            for p in self.players
        ]

        return HandState(
            hand_id=self.hand_id,
            phase=self.phase,
            pot=self.pot,
            community_cards=self.community_cards.copy(),
            current_bet=self.current_bet,
            action_on=action_on_wallet,
            players=player_states,
            valid_actions=valid_actions,
            min_raise_to=min_raise_to,
        )

    async def _run_betting_round(
        self,
        first_to_act_idx: int,
        decision_callback: DecisionCallback,
    ) -> None:
        """Run a complete betting round."""
        # Reorder players so first to act is index 0
        ordered_players = self._reorder_players_for_betting(first_to_act_idx)

        # Create betting round
        self.betting_round = BettingRound(
            players=ordered_players,
            pot=self.pot,
            big_blind=self.big_blind,
        )

        # Set initial current bet (from blinds if preflop)
        if self.phase == HandPhase.PREFLOP:
            # Find max current bet from blinds
            max_bet = max(p.current_bet for p in ordered_players)
            self.betting_round.state.current_bet = max_bet
            self.current_bet = max_bet

        # Run betting loop
        while not self.betting_round.is_round_complete():
            if self._is_hand_over():
                break

            # Get current state
            state = self.get_state()

            if state.action_on is None:
                break

            # Request decision from callback
            action = await decision_callback(state)

            # Find player in betting round
            action_idx = self.betting_round.state.action_on
            acting_player = ordered_players[action_idx]

            # Record action
            self.actions.append(HandAction(
                player_wallet=acting_player.wallet,
                phase=self.phase,
                action_type=action.action_type,
                amount=action.amount or 0,
            ))

            # Apply action
            try:
                self.betting_round.apply_action(action)
            except InvalidActionError as e:
                # If invalid action, default to fold
                self.betting_round.apply_action(Action.fold())
                self.actions[-1].action_type = "fold"

            # Update pot and current bet
            self.pot = self.betting_round.state.pot
            self.current_bet = self.betting_round.state.current_bet

        # Sync player states back to main list
        for ordered_p in ordered_players:
            main_idx = self.wallet_to_idx[ordered_p.wallet]
            main_p = self.players[main_idx]
            main_p.stack = ordered_p.stack
            main_p.current_bet = ordered_p.current_bet
            main_p.is_active = ordered_p.is_active
            main_p.is_all_in = ordered_p.is_all_in
            main_p.has_acted = ordered_p.has_acted

        self.betting_round = None

    def _determine_winners(self) -> Dict[str, int]:
        """Determine winners and distribute pot."""
        active_players = [p for p in self.players if p.is_active]

        # If only one player left, they win everything
        if len(active_players) == 1:
            winner = active_players[0]
            self._final_hands = {}
            self._side_pots = []
            return {winner.wallet: self.pot}

        # Evaluate hands first
        hand_rankings: Dict[str, int] = {}
        evaluated_hands: Dict[str, EvaluatedHand] = {}

        hands_list: List[tuple] = []
        for player in active_players:
            hole = self.hole_cards[player.wallet]
            evaluated = self.evaluator.evaluate(hole, self.community_cards)
            evaluated_hands[player.wallet] = evaluated
            hands_list.append((player.wallet, evaluated))

        # Rank hands (best = 0)
        hands_list.sort(key=lambda x: x[1], reverse=True)

        current_rank = 0
        prev_hand = None
        for wallet, hand in hands_list:
            if prev_hand is not None and hand != prev_hand:
                current_rank += 1
            hand_rankings[wallet] = current_rank
            prev_hand = hand

        # Calculate side pots
        side_pots = self.pot_calculator.calculate(self.players)

        # If no side pots but we have a pot and multiple active players,
        # create a main pot with all active players eligible
        if not side_pots and self.pot > 0 and len(active_players) > 1:
            from .side_pots import SidePot
            side_pots = [SidePot(
                amount=self.pot,
                eligible_players=[p.wallet for p in active_players]
            )]

        # Distribute pots
        winnings = self.pot_calculator.distribute(side_pots, hand_rankings)

        # Store for result
        self._final_hands = evaluated_hands
        self._side_pots = side_pots

        return winnings

    async def run(self, decision_callback: DecisionCallback) -> HandResult:
        """Run the complete hand.

        Args:
            decision_callback: Async function that takes HandState and returns Action

        Returns:
            HandResult with winners, pot distribution, and action history
        """
        self._final_hands: Dict[str, EvaluatedHand] = {}
        self._side_pots: List[SidePot] = []

        # Post blinds
        self._post_blinds()

        # Deal hole cards
        self._deal_hole_cards()

        # Preflop betting
        self.phase = HandPhase.PREFLOP
        if not self._is_hand_over() and self._count_players_can_act() > 1:
            first_to_act = self._get_preflop_action_idx()
            await self._run_betting_round(first_to_act, decision_callback)

        # Check for all-in showdown after preflop
        run_to_showdown = self._all_in_showdown() and self._count_active_players() > 1

        # Flop
        if not self._is_hand_over():
            self._reset_bets_for_new_round()
            self._deal_community_cards(3)
            self.phase = HandPhase.FLOP

            if not run_to_showdown and self._count_players_can_act() > 1:
                first_to_act = self._get_postflop_action_idx()
                await self._run_betting_round(first_to_act, decision_callback)

            if not run_to_showdown:
                run_to_showdown = self._all_in_showdown() and self._count_active_players() > 1

        # Turn
        if not self._is_hand_over():
            self._reset_bets_for_new_round()
            self._deal_community_cards(1)
            self.phase = HandPhase.TURN

            if not run_to_showdown and self._count_players_can_act() > 1:
                first_to_act = self._get_postflop_action_idx()
                await self._run_betting_round(first_to_act, decision_callback)

            if not run_to_showdown:
                run_to_showdown = self._all_in_showdown() and self._count_active_players() > 1

        # River
        if not self._is_hand_over():
            self._reset_bets_for_new_round()
            self._deal_community_cards(1)
            self.phase = HandPhase.RIVER

            if not run_to_showdown and self._count_players_can_act() > 1:
                first_to_act = self._get_postflop_action_idx()
                await self._run_betting_round(first_to_act, decision_callback)

        # Showdown
        self.phase = HandPhase.SHOWDOWN
        winners = self._determine_winners()

        # Distribute winnings
        for wallet, amount in winners.items():
            idx = self.wallet_to_idx[wallet]
            self.players[idx].stack += amount

        # Find eliminations (players with 0 stack)
        eliminations = [
            p.wallet for p in self.players
            if p.stack == 0
        ]

        self.phase = HandPhase.COMPLETE

        return HandResult(
            winners=winners,
            pot_total=self.pot,
            final_hands=self._final_hands,
            side_pots=self._side_pots,
            eliminations=eliminations,
            actions=self.actions,
        )

    def get_hole_cards(self, wallet: str) -> Optional[List[str]]:
        """Get hole cards for a specific player (for showdown display)."""
        return self.hole_cards.get(wallet)
