"""Action parser for Claude responses.

Parses JSON responses from Claude and validates them against game rules.
Provides fallback behavior for malformed or invalid responses.
"""

import json
import re
from typing import Optional

from ..poker.betting import Action, ActionType
from ..poker.hand_controller import HandState


class ActionParseError(Exception):
    """Raised when action cannot be parsed from response."""
    pass


def _extract_json(response_text: str) -> Optional[dict]:
    """Extract JSON object from response text.

    Handles cases where Claude includes explanation text before/after JSON.
    """
    # Try direct JSON parse first
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    # Look for pattern like {"action": ...}
    json_pattern = r'\{[^{}]*"action"[^{}]*\}'
    matches = re.findall(json_pattern, response_text)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Try finding any JSON object
    json_pattern = r'\{[^{}]+\}'
    matches = re.findall(json_pattern, response_text)

    for match in matches:
        try:
            data = json.loads(match)
            if "action" in data:
                return data
        except json.JSONDecodeError:
            continue

    return None


def _validate_action_type(action: str) -> ActionType:
    """Validate and normalize action type."""
    action = action.lower().strip()

    # Normalize "bet" to "raise"
    if action == "bet":
        action = "raise"

    if action not in ("fold", "check", "call", "raise"):
        raise ActionParseError(f"Unknown action type: {action}")

    return action  # type: ignore


def _can_check(hand_state: HandState, player_current_bet: int) -> bool:
    """Check if player can check (no bet to call)."""
    return hand_state.current_bet <= player_current_bet


def _get_player_state(hand_state: HandState, player_wallet: str) -> dict:
    """Get player state from hand state."""
    for player in hand_state.players:
        if player["wallet"] == player_wallet:
            return player
    raise ActionParseError(f"Player {player_wallet} not found in hand state")


def parse_response(
    response_text: str,
    hand_state: HandState,
    player_wallet: str,
) -> Action:
    """Parse Claude's JSON response and validate against game rules.

    Args:
        response_text: Raw response text from Claude
        hand_state: Current hand state for validation
        player_wallet: Wallet address of acting player

    Returns:
        Validated Action object

    Validation rules:
    - Can't check if there's a bet to call
    - Raise must be >= min_raise_to
    - Raise can't exceed player's stack
    - All-in is valid at any amount
    - "bet" normalized to "raise"

    Fallback behavior:
    - Malformed JSON -> fold
    - Invalid action type -> fold
    - Check when can't check -> call or fold
    - Invalid raise amount -> clamp to valid range or fold
    """
    player = _get_player_state(hand_state, player_wallet)
    player_stack = player["stack"]
    player_current_bet = player["current_bet"]
    amount_to_call = hand_state.current_bet - player_current_bet

    # Try to extract JSON
    try:
        data = _extract_json(response_text)
    except Exception:
        data = None

    if data is None:
        # Malformed JSON - conservative fallback
        return _fallback_action(hand_state, player_wallet)

    # Get action type
    try:
        action_str = data.get("action", "")
        action_type = _validate_action_type(action_str)
    except ActionParseError:
        return _fallback_action(hand_state, player_wallet)

    # Validate and return action
    if action_type == "fold":
        return Action.fold()

    if action_type == "check":
        if _can_check(hand_state, player_current_bet):
            return Action.check()
        else:
            # Can't check, try call instead
            if amount_to_call <= player_stack:
                return Action.call()
            else:
                return Action.fold()

    if action_type == "call":
        # Call is always valid if there's something to call
        if amount_to_call > 0:
            return Action.call()
        else:
            # Nothing to call, check instead
            return Action.check()

    if action_type == "raise":
        amount = data.get("amount")

        if amount is None:
            # No amount specified - try minimum raise
            amount = hand_state.min_raise_to

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            # Invalid amount - fallback
            return _fallback_action(hand_state, player_wallet)

        # Validate raise amount
        return _validate_raise(
            amount,
            hand_state,
            player_wallet,
            player_stack,
            player_current_bet,
        )

    # Shouldn't reach here
    return _fallback_action(hand_state, player_wallet)


def _validate_raise(
    amount: int,
    hand_state: HandState,
    player_wallet: str,
    player_stack: int,
    player_current_bet: int,
) -> Action:
    """Validate raise amount and return appropriate action.

    Args:
        amount: Requested raise-to amount (total bet size)
        hand_state: Current hand state
        player_wallet: Acting player's wallet
        player_stack: Player's current stack
        player_current_bet: Player's current bet in this round

    Returns:
        Valid raise action, or fallback if invalid
    """
    # Calculate how much player needs to put in
    amount_to_put_in = amount - player_current_bet

    # Check if this would be all-in
    total_available = player_stack + player_current_bet

    if amount >= total_available:
        # All-in is always valid
        return Action.raise_to(total_available)

    if amount_to_put_in > player_stack:
        # Can't afford this raise, go all-in instead
        return Action.raise_to(total_available)

    # Not all-in, check minimum raise
    if amount < hand_state.min_raise_to:
        # Below minimum - clamp to minimum if can afford, else fold
        if hand_state.min_raise_to - player_current_bet <= player_stack:
            return Action.raise_to(hand_state.min_raise_to)
        else:
            # Can't afford minimum raise - call or fold
            amount_to_call = hand_state.current_bet - player_current_bet
            if amount_to_call <= player_stack:
                return Action.call()
            else:
                return Action.fold()

    # Valid raise
    return Action.raise_to(amount)


def _fallback_action(hand_state: HandState, player_wallet: str) -> Action:
    """Return conservative fallback action.

    Strategy: Check if possible, otherwise fold.
    """
    player = _get_player_state(hand_state, player_wallet)
    player_current_bet = player["current_bet"]

    if _can_check(hand_state, player_current_bet):
        return Action.check()

    return Action.fold()
