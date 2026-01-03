"""Table management module for poker tournaments.

Handles individual table state, seat management, and position tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class TableState(Enum):
    """Current state of the table."""
    WAITING = "waiting"      # Between hands
    DEALING = "dealing"      # Dealing cards
    BETTING = "betting"      # Active betting round
    SHOWDOWN = "showdown"    # Revealing hands


@dataclass
class Seat:
    """Represents a seat at the poker table.

    Attributes:
        position: Seat position (0-8 for 9-max table)
        player_wallet: Wallet address of player, None if empty
        stack: Current chip stack
        is_active: Whether player is in current hand
        status: Current status of the seat
    """
    position: int  # 0-8 for 9-max table
    player_wallet: str | None = None
    stack: int = 0
    is_active: bool = False  # In current hand
    status: Literal["empty", "active", "eliminated", "sitting_out"] = "empty"


class Table:
    """Manages a single poker table (9-max).

    Handles:
    - Seat management
    - Button position tracking
    - Player count
    - Active players in hand
    """

    MAX_SEATS = 9

    def __init__(self, table_id: str):
        """Initialize a new table.

        Args:
            table_id: Unique identifier for this table
        """
        self.table_id = table_id
        self.seats: list[Seat] = [Seat(position=i) for i in range(self.MAX_SEATS)]
        self.button_position: int = 0
        self.state = TableState.WAITING

    def seat_player(self, wallet: str, position: int, stack: int) -> bool:
        """Seat a player at specific position.

        Args:
            wallet: Player's wallet address
            position: Seat position (0-8)
            stack: Starting chip stack

        Returns:
            True if player was seated, False if position is occupied
        """
        if position < 0 or position >= self.MAX_SEATS:
            return False

        seat = self.seats[position]
        if seat.status != "empty":
            return False

        seat.player_wallet = wallet
        seat.stack = stack
        seat.status = "active"
        seat.is_active = False  # Not yet in a hand
        return True

    def remove_player(self, wallet: str) -> bool:
        """Remove player from table.

        Args:
            wallet: Player's wallet address

        Returns:
            True if player was removed, False if not found
        """
        seat = self.get_player_seat(wallet)
        if seat is None:
            return False

        seat.player_wallet = None
        seat.stack = 0
        seat.status = "empty"
        seat.is_active = False
        return True

    def get_player_seat(self, wallet: str) -> Seat | None:
        """Get seat for a player by wallet.

        Args:
            wallet: Player's wallet address

        Returns:
            Seat object if found, None otherwise
        """
        for seat in self.seats:
            if seat.player_wallet == wallet:
                return seat
        return None

    def get_active_players(self) -> list[Seat]:
        """Get all seats with active players (not eliminated/sitting out).

        Returns:
            List of seats with active players
        """
        return [
            seat for seat in self.seats
            if seat.status == "active"
        ]

    def player_count(self) -> int:
        """Number of active players at table.

        Returns:
            Count of active players
        """
        return len(self.get_active_players())

    def advance_button(self) -> int:
        """Move button to next active player.

        Returns:
            New button position
        """
        active_players = self.get_active_players()
        if not active_players:
            return self.button_position

        # Find next active player after current button
        for i in range(1, self.MAX_SEATS + 1):
            next_pos = (self.button_position + i) % self.MAX_SEATS
            seat = self.seats[next_pos]
            if seat.status == "active":
                self.button_position = next_pos
                return next_pos

        return self.button_position

    def get_small_blind_seat(self) -> Seat | None:
        """Get seat that should post small blind (left of button).

        For heads-up: Button is small blind.
        For 3+ players: First active player left of button.

        Returns:
            Seat for small blind, or None if not enough players
        """
        active_players = self.get_active_players()
        if len(active_players) < 2:
            return None

        # Heads-up: Button is small blind
        if len(active_players) == 2:
            return self.seats[self.button_position]

        # 3+ players: First active player left of button
        return self.get_next_to_act(self.button_position)

    def get_big_blind_seat(self) -> Seat | None:
        """Get seat that should post big blind (left of SB).

        Returns:
            Seat for big blind, or None if not enough players
        """
        active_players = self.get_active_players()
        if len(active_players) < 2:
            return None

        sb_seat = self.get_small_blind_seat()
        if sb_seat is None:
            return None

        # Heads-up: Non-button player is big blind
        if len(active_players) == 2:
            for seat in active_players:
                if seat.position != self.button_position:
                    return seat
            return None

        # 3+ players: First active player left of SB
        return self.get_next_to_act(sb_seat.position)

    def get_next_to_act(self, from_position: int) -> Seat | None:
        """Get next active player from given position.

        Args:
            from_position: Position to start searching from (exclusive)

        Returns:
            Next active seat, or None if no active players
        """
        for i in range(1, self.MAX_SEATS + 1):
            next_pos = (from_position + i) % self.MAX_SEATS
            seat = self.seats[next_pos]
            if seat.status == "active" and seat.is_active:
                return seat
        return None

    def get_next_big_blind_player(self) -> str | None:
        """Get wallet of player who will be BB next hand.

        Used for table balancing - we prefer to move players who are
        about to be big blind to avoid them paying blinds twice.

        Returns:
            Wallet address of next BB player, or None
        """
        # Simulate advancing button and getting BB
        active_players = self.get_active_players()
        if len(active_players) < 2:
            return None

        # Find what would be next button position
        next_button = self.button_position
        for i in range(1, self.MAX_SEATS + 1):
            next_pos = (self.button_position + i) % self.MAX_SEATS
            if self.seats[next_pos].status == "active":
                next_button = next_pos
                break

        # Find BB from that button position
        if len(active_players) == 2:
            # Heads-up: non-button is BB
            for seat in active_players:
                if seat.position != next_button:
                    return seat.player_wallet
        else:
            # 3+ players: two seats left of button
            count = 0
            for i in range(1, self.MAX_SEATS + 1):
                pos = (next_button + i) % self.MAX_SEATS
                if self.seats[pos].status == "active":
                    count += 1
                    if count == 2:  # Second active player is BB
                        return self.seats[pos].player_wallet

        return None

    def get_available_seats(self) -> list[int]:
        """Get list of empty seat positions.

        Returns:
            List of position indices that are empty
        """
        return [
            seat.position for seat in self.seats
            if seat.status == "empty"
        ]

    def eliminate_player(self, wallet: str) -> None:
        """Mark player as eliminated.

        Args:
            wallet: Player's wallet address
        """
        seat = self.get_player_seat(wallet)
        if seat is not None:
            seat.status = "eliminated"
            seat.is_active = False
            seat.stack = 0

    def __repr__(self) -> str:
        """String representation of table state."""
        active = self.player_count()
        return f"Table({self.table_id}, players={active}, button={self.button_position})"
