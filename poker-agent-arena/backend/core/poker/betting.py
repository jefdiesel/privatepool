"""Betting logic for poker rounds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, List


ActionType = Literal["fold", "check", "call", "raise"]


class InvalidActionError(Exception):
    """Raised when an invalid action is attempted."""
    pass


@dataclass
class Action:
    """Represents a player action in a betting round."""
    action_type: ActionType
    amount: int | None = None  # Only for "raise"

    @classmethod
    def fold(cls) -> "Action":
        return cls("fold")

    @classmethod
    def check(cls) -> "Action":
        return cls("check")

    @classmethod
    def call(cls) -> "Action":
        return cls("call")

    @classmethod
    def raise_to(cls, amount: int) -> "Action":
        return cls("raise", amount)


@dataclass
class PlayerInHand:
    """Represents a player's state within a hand."""
    wallet: str
    stack: int
    current_bet: int = 0
    is_active: bool = True  # False if folded
    is_all_in: bool = False
    has_acted: bool = False


@dataclass
class BettingState:
    """Current state of a betting round."""
    pot: int
    current_bet: int
    min_raise: int
    last_raise_amount: int  # For calculating next min-raise
    players: list[PlayerInHand]
    action_on: int  # Index of player to act
    num_active: int  # Players still in hand (not folded)
    num_to_act: int  # Players who still need to act this round


class BettingRound:
    """Manages a single betting round (preflop, flop, turn, river).

    Rules:
    - Can't check if there's a bet to call
    - Raise must be at least min_raise
    - All-in is always valid regardless of amount
    - Round ends when all active players have acted and bets are matched
    """

    def __init__(self, players: list[PlayerInHand], pot: int, big_blind: int):
        """Initialize a betting round.

        Args:
            players: List of players in the hand
            pot: Current pot size
            big_blind: Big blind amount (used for min raise)
        """
        self.big_blind = big_blind

        # Count active players (not folded and not all-in)
        num_active = sum(1 for p in players if p.is_active)

        # Count players who can still act (active and not all-in)
        num_to_act = sum(1 for p in players if p.is_active and not p.is_all_in)

        # Reset has_acted for all players at start of round
        for p in players:
            p.has_acted = False

        # Find first player that can act
        action_on = 0
        for i, p in enumerate(players):
            if p.is_active and not p.is_all_in:
                action_on = i
                break

        self.state = BettingState(
            pot=pot,
            current_bet=0,
            min_raise=big_blind,
            last_raise_amount=big_blind,
            players=players,
            action_on=action_on,
            num_active=num_active,
            num_to_act=num_to_act
        )

    def get_valid_actions(self) -> list[ActionType]:
        """Return valid actions for current player."""
        player = self.state.players[self.state.action_on]

        if not player.is_active or player.is_all_in:
            return []

        actions: list[ActionType] = []

        amount_to_call = self.state.current_bet - player.current_bet

        if amount_to_call > 0:
            # There's a bet to call
            actions.append("fold")
            actions.append("call")
            # Can always raise (all-in counts as raise even if below min)
            actions.append("raise")
        else:
            # No bet to call
            actions.append("check")
            actions.append("raise")

        return actions

    def apply_action(self, action: Action) -> BettingState:
        """Apply action and return updated state.

        Raises:
            InvalidActionError: If action is not valid
        """
        player = self.state.players[self.state.action_on]
        valid_actions = self.get_valid_actions()

        if action.action_type not in valid_actions:
            raise InvalidActionError(f"Action {action.action_type} is not valid. Valid actions: {valid_actions}")

        if action.action_type == "fold":
            self._apply_fold(player)
        elif action.action_type == "check":
            self._apply_check(player)
        elif action.action_type == "call":
            self._apply_call(player)
        elif action.action_type == "raise":
            self._apply_raise(player, action.amount)

        # Mark player as having acted
        player.has_acted = True

        # Advance to next player if round not complete
        if not self.is_round_complete():
            self.advance_action()

        return self.state

    def _apply_fold(self, player: PlayerInHand) -> None:
        """Apply fold action."""
        player.is_active = False
        self.state.num_active -= 1
        self.state.num_to_act -= 1

    def _apply_check(self, player: PlayerInHand) -> None:
        """Apply check action."""
        # Check is only valid when current_bet == player.current_bet
        # This is already validated in get_valid_actions
        self.state.num_to_act -= 1

    def _apply_call(self, player: PlayerInHand) -> None:
        """Apply call action."""
        amount_to_call = self.state.current_bet - player.current_bet

        # If player can't fully call, they go all-in
        if amount_to_call >= player.stack:
            amount_to_call = player.stack
            player.is_all_in = True

        player.stack -= amount_to_call
        player.current_bet += amount_to_call
        self.state.pot += amount_to_call
        self.state.num_to_act -= 1

    def _apply_raise(self, player: PlayerInHand, raise_to_amount: int | None) -> None:
        """Apply raise action."""
        if raise_to_amount is None:
            raise InvalidActionError("Raise action requires an amount")

        amount_to_call = self.state.current_bet - player.current_bet
        total_to_put_in = raise_to_amount - player.current_bet

        # Check if this is an all-in (always valid)
        is_all_in = total_to_put_in >= player.stack

        if is_all_in:
            # All-in is always valid
            total_to_put_in = player.stack
            raise_to_amount = player.current_bet + total_to_put_in
            player.is_all_in = True
        else:
            # Not all-in, must meet minimum raise
            min_raise_to = self.state.current_bet + self.state.min_raise
            if raise_to_amount < min_raise_to:
                raise InvalidActionError(
                    f"Raise to {raise_to_amount} is below minimum raise of {min_raise_to}"
                )

        # Calculate the raise amount (difference from current bet)
        raise_amount = raise_to_amount - self.state.current_bet

        player.stack -= total_to_put_in
        player.current_bet = raise_to_amount
        self.state.pot += total_to_put_in
        self.state.current_bet = raise_to_amount

        # Update min raise for next raise (must be at least the size of this raise)
        if raise_amount > 0:
            self.state.last_raise_amount = raise_amount
            self.state.min_raise = raise_amount

        # After a raise, all other active players need to act again
        self._reset_action_needed()
        player.has_acted = True  # Current player has acted

    def _reset_action_needed(self) -> None:
        """Reset has_acted for all active players (after a raise)."""
        count = 0
        for p in self.state.players:
            if p.is_active and not p.is_all_in:
                p.has_acted = False
                count += 1
        self.state.num_to_act = count

    def is_round_complete(self) -> bool:
        """Check if betting round is complete.

        Complete when:
        - All but one player folded, OR
        - All active players have matched the current bet and had a chance to act
        """
        # All but one folded
        if self.state.num_active <= 1:
            return True

        # Check if all active non-all-in players have acted and matched
        for p in self.state.players:
            if p.is_active and not p.is_all_in:
                # Must have acted
                if not p.has_acted:
                    return False
                # Must have matched current bet (or be all-in)
                if p.current_bet < self.state.current_bet:
                    return False

        return True

    def advance_action(self) -> int:
        """Move action to next active player. Return new action_on index."""
        num_players = len(self.state.players)
        start = self.state.action_on

        for i in range(1, num_players + 1):
            next_idx = (start + i) % num_players
            player = self.state.players[next_idx]

            # Skip folded and all-in players
            if player.is_active and not player.is_all_in:
                self.state.action_on = next_idx
                return next_idx

        # No valid player found, return current
        return self.state.action_on
