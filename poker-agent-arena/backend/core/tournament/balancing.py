"""Table balancing module for poker tournaments.

Handles balancing tables after player eliminations and breaking tables
when player counts allow consolidation.

Rules (from spec):
1. Check table sizes after every elimination
2. If max difference > 1, balance immediately
3. Move the player who will be big blind next (fairest position)
4. Never move during an active hand
5. Table break logic when tables can consolidate
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .table import Table


@dataclass
class TableMove:
    """Represents a player move between tables.

    Attributes:
        player_wallet: Wallet address of the player being moved
        from_table_id: ID of the source table
        from_seat: Seat position at source table
        to_table_id: ID of the destination table
        to_seat: Seat position at destination table
    """

    player_wallet: str
    from_table_id: str
    from_seat: int
    to_table_id: str
    to_seat: int


class TableBalancer:
    """Balances tables after player eliminations.

    Rules (from spec):
    1. Check table sizes after every elimination
    2. If max difference > 1, balance immediately
    3. Move the player who will be big blind next (fairest position)
    4. Never move during an active hand
    5. Table break logic when tables can consolidate
    """

    def check_balance_needed(self, tables: list[Table]) -> bool:
        """Check if tables need balancing.

        Returns True if max table size - min table size > 1.

        Args:
            tables: List of active tables

        Returns:
            True if balancing is needed, False otherwise
        """
        if len(tables) < 2:
            return False

        player_counts = [table.player_count() for table in tables]
        return max(player_counts) - min(player_counts) > 1

    def get_move(self, tables: list[Table]) -> TableMove | None:
        """Determine which player to move and where.

        Returns None if no move needed.

        Algorithm:
        1. Find fullest table (source)
        2. Find emptiest table (destination)
        3. Select player who will be BB next from source
        4. Find best available seat at destination

        Args:
            tables: List of active tables

        Returns:
            TableMove describing the move, or None if no move needed
        """
        if not self.check_balance_needed(tables):
            return None

        # Find fullest and emptiest tables
        source_table = max(tables, key=lambda t: t.player_count())
        dest_table = min(tables, key=lambda t: t.player_count())

        # Get the player who will be BB next (fairest to move)
        player_wallet = source_table.get_next_big_blind_player()
        if player_wallet is None:
            # Fallback: get any active player from source
            active_players = source_table.get_active_players()
            if not active_players:
                return None
            player_wallet = active_players[0].player_wallet

        # Get current seat of player
        player_seat = source_table.get_player_seat(player_wallet)
        if player_seat is None:
            return None

        # Find best available seat at destination
        to_seat = self._get_best_available_seat(dest_table)
        if to_seat is None:
            return None

        return TableMove(
            player_wallet=player_wallet,
            from_table_id=source_table.table_id,
            from_seat=player_seat.position,
            to_table_id=dest_table.table_id,
            to_seat=to_seat,
        )

    def apply_move(self, tables: list[Table], move: TableMove) -> None:
        """Execute the table move.

        Updates both source and destination tables.

        Args:
            tables: List of active tables
            move: The TableMove to execute
        """
        # Find source and destination tables
        source_table = None
        dest_table = None

        for table in tables:
            if table.table_id == move.from_table_id:
                source_table = table
            if table.table_id == move.to_table_id:
                dest_table = table

        if source_table is None or dest_table is None:
            raise ValueError("Could not find source or destination table")

        # Get player's stack before removal
        player_seat = source_table.get_player_seat(move.player_wallet)
        if player_seat is None:
            raise ValueError(f"Player {move.player_wallet} not found at source table")

        stack = player_seat.stack

        # Remove from source
        source_table.remove_player(move.player_wallet)

        # Seat at destination
        dest_table.seat_player(move.player_wallet, move.to_seat, stack)

    def should_break_table(self, tables: list[Table]) -> Table | None:
        """Check if a table should be broken (combined with others).

        Break when remaining players can fit at fewer tables.
        A table breaks when total_players <= (num_tables - 1) * 9.

        Args:
            tables: List of active tables

        Returns:
            Table to break, or None if no break needed

        Example:
            18 players, 3 tables -> keep 3 tables (6 each)
            17 players, 3 tables -> break one table, 2 tables (9, 8)
        """
        if len(tables) <= 1:
            return None

        total_players = sum(table.player_count() for table in tables)
        max_per_table = 9

        optimal_tables = self._calculate_optimal_tables(total_players, max_per_table)

        if optimal_tables < len(tables):
            # Need to break a table - return the one with fewest players
            return min(tables, key=lambda t: t.player_count())

        return None

    def break_table(
        self, tables: list[Table], table_to_break: Table
    ) -> list[TableMove]:
        """Generate moves to break a table and redistribute players.

        Returns list of moves to execute.

        Algorithm:
        1. Get all players from table_to_break
        2. Distribute to remaining tables, filling empty seats
        3. Balance as needed after redistribution

        Args:
            tables: List of all active tables
            table_to_break: The table to break

        Returns:
            List of TableMove objects to execute
        """
        moves: list[TableMove] = []

        # Get remaining tables (excluding the one being broken)
        remaining_tables = [t for t in tables if t.table_id != table_to_break.table_id]

        if not remaining_tables:
            return moves

        # Get all active players from the table being broken
        players_to_move = [
            (seat.player_wallet, seat.position, seat.stack)
            for seat in table_to_break.get_active_players()
            if seat.player_wallet is not None
        ]

        # Distribute players to remaining tables
        for player_wallet, from_seat, _stack in players_to_move:
            # Find table with most available seats (to balance distribution)
            best_table = min(remaining_tables, key=lambda t: t.player_count())

            to_seat = self._get_best_available_seat(best_table)
            if to_seat is None:
                # This shouldn't happen if break logic is correct
                continue

            moves.append(
                TableMove(
                    player_wallet=player_wallet,
                    from_table_id=table_to_break.table_id,
                    from_seat=from_seat,
                    to_table_id=best_table.table_id,
                    to_seat=to_seat,
                )
            )

        return moves

    def _get_best_available_seat(self, table: Table) -> int | None:
        """Get best available seat position at a table.

        Prefer seats that won't immediately be in blinds.

        Args:
            table: The table to find a seat at

        Returns:
            Seat position, or None if no seats available
        """
        available = table.get_available_seats()
        if not available:
            return None

        # Get current blind positions to avoid
        sb_seat = table.get_small_blind_seat()
        bb_seat = table.get_big_blind_seat()

        blind_positions = set()
        if sb_seat:
            blind_positions.add(sb_seat.position)
        if bb_seat:
            blind_positions.add(bb_seat.position)

        # Calculate what would be SB/BB next hand (after button advances)
        # This is an approximation - prefer seats not near current button
        button_pos = table.button_position

        # Positions to avoid: immediately after button (would be blinds)
        positions_to_avoid = set()
        for i in range(1, 3):  # Next 2 positions after button
            pos = (button_pos + i) % 9
            positions_to_avoid.add(pos)

        # First try: find seat not in blind positions
        preferred = [pos for pos in available if pos not in positions_to_avoid]
        if preferred:
            return preferred[0]

        # Fallback: any available seat
        return available[0]

    def _calculate_optimal_tables(
        self, total_players: int, max_per_table: int = 9
    ) -> int:
        """Calculate optimal number of tables for given player count.

        Args:
            total_players: Total number of players
            max_per_table: Maximum players per table (default 9)

        Returns:
            Optimal number of tables

        Examples:
            27 players -> 3 tables (9, 9, 9)
            25 players -> 3 tables (9, 8, 8)
            18 players -> 2 tables (9, 9)
            17 players -> 2 tables (9, 8)
        """
        if total_players <= 0:
            return 0

        # Minimum tables needed is ceiling division
        return (total_players + max_per_table - 1) // max_per_table
