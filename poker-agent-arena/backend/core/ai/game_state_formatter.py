"""Game state formatter for Claude-readable poker states.

Converts HandState into a compressed, human-readable format that
efficiently communicates all necessary decision information.
"""

from typing import List, Dict, Optional

from ..poker.hand_controller import HandState, HandPhase


# Position labels based on table size and seat position
POSITION_LABELS_6MAX = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
POSITION_LABELS_9MAX = ["UTG", "UTG+1", "UTG+2", "MP", "HJ", "CO", "BTN", "SB", "BB"]


def _get_position_labels(num_players: int) -> List[str]:
    """Get position labels for table size."""
    if num_players <= 6:
        # For smaller tables, use end positions
        if num_players == 2:
            return ["BTN", "BB"]
        elif num_players == 3:
            return ["BTN", "SB", "BB"]
        elif num_players == 4:
            return ["CO", "BTN", "SB", "BB"]
        elif num_players == 5:
            return ["MP", "CO", "BTN", "SB", "BB"]
        else:
            return POSITION_LABELS_6MAX
    else:
        # 7-9 players
        return POSITION_LABELS_9MAX[-num_players:]


def _get_player_position(
    seat_position: int,
    button_seat: int,
    num_players: int,
    seat_positions: List[int],
) -> str:
    """Get position label for a player based on their seat relative to button."""
    # Calculate positions relative to button
    # Sort seat positions and find button's index
    sorted_seats = sorted(seat_positions)
    button_idx = sorted_seats.index(button_seat)
    player_idx = sorted_seats.index(seat_position)

    # Calculate relative position (0 = button, 1 = SB, 2 = BB, etc.)
    relative_pos = (player_idx - button_idx) % num_players

    labels = _get_position_labels(num_players)

    # Map relative position to label
    # Button is at relative_pos 0, SB at 1, BB at 2
    # We need to reverse map this to our position labels
    if num_players == 2:
        return labels[relative_pos]

    # For 3+ players: BTN is always BTN, SB is +1, BB is +2
    # Earlier positions fill backwards from BTN
    if relative_pos == 0:
        return "BTN"
    elif relative_pos == 1:
        return "SB"
    elif relative_pos == 2:
        return "BB"
    else:
        # Earlier positions (UTG, MP, etc.)
        early_labels = labels[:-3]  # All labels except BTN, SB, BB
        early_idx = relative_pos - 3
        if early_idx < len(early_labels):
            return early_labels[early_idx]
        return f"EP{early_idx}"


def _format_card(card: str) -> str:
    """Format a card string (already in format like 'Ah', 'Kd')."""
    return card


def _format_cards(cards: List[str]) -> str:
    """Format a list of cards."""
    return " ".join(_format_card(c) for c in cards)


def _get_phase_name(phase: HandPhase) -> str:
    """Get readable phase name."""
    return phase.value.upper()


def _format_player_status(
    player: dict,
    current_round_bet: int,
    is_to_act: bool,
    position: str,
    ante_amount: int = 0,
) -> str:
    """Format a single player's status line."""
    wallet_short = player["wallet"][:8]  # Truncate wallet for readability
    stack = player["stack"]

    # Determine status
    if not player["is_active"]:
        status = "(folded)"
    elif player["is_all_in"]:
        status = "(all-in)"
    elif is_to_act:
        status = "(to act)"
    elif player["current_bet"] > 0:
        bet_amount = player["current_bet"]
        if bet_amount == current_round_bet:
            status = f"(bet {bet_amount})"
        else:
            status = f"(bet {bet_amount})"
    else:
        status = "(waiting)"

    # Add ante info for BB if applicable
    ante_info = ""
    if position == "BB" and ante_amount > 0:
        ante_info = f" [posted ante: {ante_amount}]"

    return f"[{position}] {wallet_short}: {stack:,} {status}{ante_info}"


def format_game_state(
    hand_state: HandState,
    player_wallet: str,
    hole_cards: List[str],
    button_seat: int,
    ante: int = 0,
    hand_number: int = 0,
    action_history: Optional[List[dict]] = None,
) -> str:
    """Format game state for Claude in compressed format.

    Args:
        hand_state: Current hand state from HandController
        player_wallet: Wallet address of player making decision
        hole_cards: Player's hole cards
        button_seat: Seat position of button
        ante: Current ante amount (paid by BB)
        hand_number: Hand number in tournament
        action_history: List of action records for history display

    Returns:
        Formatted string representation of game state
    """
    # Calculate to-call amount
    current_player = None
    for p in hand_state.players:
        if p["wallet"] == player_wallet:
            current_player = p
            break

    if current_player is None:
        raise ValueError(f"Player {player_wallet} not found in hand state")

    to_call = hand_state.current_bet - current_player["current_bet"]

    # Get seat positions for position calculation
    seat_positions = [p["seat_position"] for p in hand_state.players]
    num_players = len(hand_state.players)

    # Get player's position
    player_position = _get_player_position(
        current_player["seat_position"],
        button_seat,
        num_players,
        seat_positions,
    )

    # Build header
    lines = [
        f"HAND #{hand_number} | {_get_phase_name(hand_state.phase)} | Pot: {hand_state.pot:,} | To Call: {to_call}",
        "",
    ]

    # Board (if any community cards)
    if hand_state.community_cards:
        lines.append(f"Board: {_format_cards(hand_state.community_cards)}")
        lines.append("")

    # Player's cards and info
    lines.append(f"Your Cards: {_format_cards(hole_cards)}")
    lines.append(f"Your Position: {player_position}")
    lines.append(f"Your Stack: {current_player['stack']:,}")
    lines.append("")

    # All players (in seat order)
    lines.append("Players:")
    sorted_players = sorted(hand_state.players, key=lambda p: p["seat_position"])

    for i, p in enumerate(sorted_players, 1):
        position = _get_player_position(
            p["seat_position"],
            button_seat,
            num_players,
            seat_positions,
        )
        is_to_act = p["wallet"] == player_wallet

        # Use "YOU" for current player
        if is_to_act:
            wallet_display = "YOU"
        else:
            wallet_display = p["wallet"][:8]

        if not p["is_active"]:
            status = "(folded)"
        elif p["is_all_in"]:
            status = "(all-in)"
        elif is_to_act:
            status = "(to act)"
        elif p["current_bet"] > 0:
            status = f"(bet {p['current_bet']})"
        else:
            status = ""

        # Add ante info for BB
        ante_info = ""
        if position == "BB" and ante > 0:
            ante_info = f" [posted ante: {ante}]"

        lines.append(f"{i}. [{position}] {wallet_display}: {p['stack']:,} {status}{ante_info}")

    lines.append("")

    # Action history (if provided)
    if action_history:
        lines.append("Action History This Hand:")

        # Group actions by phase
        phases_order = ["POSTING_BLINDS", "PREFLOP", "FLOP", "TURN", "RIVER"]
        actions_by_phase: Dict[str, List[str]] = {phase: [] for phase in phases_order}

        for action in action_history:
            phase = action.get("phase", "PREFLOP").upper()
            action_type = action.get("action_type", "")
            amount = action.get("amount", 0)
            wallet = action.get("player_wallet", "")[:8]

            if action_type in ("post_sb", "post_bb", "post_ante"):
                action_str = f"{wallet} posts {amount}"
            elif action_type == "fold":
                action_str = f"{wallet} fold"
            elif action_type == "check":
                action_str = f"{wallet} check"
            elif action_type == "call":
                action_str = f"{wallet} call"
            elif action_type == "raise":
                action_str = f"{wallet} raise {amount}"
            else:
                action_str = f"{wallet} {action_type}"

            if phase in actions_by_phase:
                actions_by_phase[phase].append(action_str)

        for phase in phases_order:
            if actions_by_phase[phase]:
                phase_display = phase.lower().replace("_", " ").title()
                lines.append(f"- {phase_display}: {', '.join(actions_by_phase[phase])}")

        lines.append("")

    lines.append("Your Action?")

    return "\n".join(lines)
