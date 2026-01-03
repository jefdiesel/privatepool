"""Seating management module for poker tournaments.

Handles initial tournament seating using provably fair algorithms.
"""

import hashlib
import random
from dataclasses import dataclass
from math import ceil

from .table import Table


@dataclass
class SeatAssignment:
    """Represents a player's assigned seat in the tournament.

    Attributes:
        wallet: Player's wallet address
        table_id: ID of assigned table
        seat_position: Position at the table (0-8)
        starting_stack: Initial chip stack
    """
    wallet: str
    table_id: str
    seat_position: int
    starting_stack: int


class SeatingManager:
    """Handles initial tournament seating.

    Uses provably fair algorithm:
    1. Shuffle players using RNG seed
    2. Assign to tables round-robin
    3. Random seat position at each table

    The seed should be derived from blockchain data (e.g., blockhash + tournament_id)
    to ensure verifiable fairness.
    """

    def __init__(self, max_table_size: int = 9):
        """Initialize seating manager.

        Args:
            max_table_size: Maximum players per table (default 9)
        """
        self.max_table_size = max_table_size

    def create_seating(
        self,
        players: list[str],  # Wallet addresses
        starting_stack: int,
        seed: bytes,
    ) -> tuple[list[Table], list[SeatAssignment]]:
        """Create initial seating for tournament.

        Args:
            players: List of player wallet addresses
            starting_stack: Starting chip stack for each player
            seed: RNG seed for provably fair shuffling

        Returns:
            Tuple of (list of Table objects, list of SeatAssignment objects)

        Raises:
            ValueError: If no players provided
        """
        if not players:
            raise ValueError("Cannot create seating with no players")

        # Shuffle players deterministically
        shuffled_players = self._shuffle_players(players, seed)

        # Calculate number of tables needed
        table_count = self._calculate_table_count(len(players))

        # Create tables
        tables = [Table(table_id=f"table_{i + 1}") for i in range(table_count)]

        # Create seat position assignments for each table
        # Using seed to randomize seat positions within tables
        table_seat_orders = self._generate_seat_orders(table_count, seed)

        # Track assignments
        assignments: list[SeatAssignment] = []

        # Distribute players round-robin to tables
        table_player_lists: list[list[str]] = [[] for _ in range(table_count)]
        for i, wallet in enumerate(shuffled_players):
            table_idx = i % table_count
            table_player_lists[table_idx].append(wallet)

        # Assign seats at each table
        for table_idx, table in enumerate(tables):
            players_at_table = table_player_lists[table_idx]
            seat_order = table_seat_orders[table_idx]

            for player_idx, wallet in enumerate(players_at_table):
                seat_position = seat_order[player_idx]

                # Seat the player
                table.seat_player(wallet, seat_position, starting_stack)

                # Record assignment
                assignment = SeatAssignment(
                    wallet=wallet,
                    table_id=table.table_id,
                    seat_position=seat_position,
                    starting_stack=starting_stack,
                )
                assignments.append(assignment)

        return tables, assignments

    def _calculate_table_count(self, player_count: int) -> int:
        """Calculate optimal number of tables.

        Goal: Balance tables as evenly as possible.
        Examples:
            27 players = 3 tables of 9
            25 players = 3 tables (9, 8, 8)
            10 players = 2 tables (5, 5)
            9 players = 1 table of 9
            2 players = 1 table (heads-up)

        Args:
            player_count: Total number of players

        Returns:
            Optimal number of tables
        """
        if player_count <= 0:
            return 0

        # Minimum 1 table
        if player_count <= self.max_table_size:
            return 1

        # Need multiple tables
        return ceil(player_count / self.max_table_size)

    def _shuffle_players(self, players: list[str], seed: bytes) -> list[str]:
        """Deterministically shuffle players using seed.

        Uses SHA256 to derive a random seed for the shuffle,
        ensuring the same seed always produces the same ordering.

        Args:
            players: List of player wallet addresses
            seed: RNG seed bytes

        Returns:
            Shuffled copy of players list
        """
        # Create a copy to avoid modifying original
        shuffled = players.copy()

        # Derive integer seed from bytes
        seed_hash = hashlib.sha256(seed).digest()
        seed_int = int.from_bytes(seed_hash[:8], byteorder="big")

        # Use Python's random with seed for deterministic shuffle
        rng = random.Random(seed_int)
        rng.shuffle(shuffled)

        return shuffled

    def _generate_seat_orders(
        self,
        table_count: int,
        seed: bytes,
    ) -> list[list[int]]:
        """Generate randomized seat orderings for each table.

        Each table gets a shuffled list of seat positions,
        so players are randomly distributed around the table.

        Args:
            table_count: Number of tables
            seed: RNG seed bytes

        Returns:
            List of seat order lists, one per table
        """
        seat_orders: list[list[int]] = []

        for table_idx in range(table_count):
            # Create unique seed for each table
            table_seed = hashlib.sha256(
                seed + f"_table_{table_idx}".encode()
            ).digest()
            seed_int = int.from_bytes(table_seed[:8], byteorder="big")

            # Create shuffled seat positions
            positions = list(range(self.max_table_size))
            rng = random.Random(seed_int)
            rng.shuffle(positions)

            seat_orders.append(positions)

        return seat_orders

    def get_table_distribution(self, player_count: int) -> list[int]:
        """Get the distribution of players across tables.

        Useful for previewing how players will be distributed.

        Args:
            player_count: Total number of players

        Returns:
            List of player counts per table

        Example:
            25 players -> [9, 8, 8]
            27 players -> [9, 9, 9]
        """
        if player_count <= 0:
            return []

        table_count = self._calculate_table_count(player_count)
        if table_count == 0:
            return []

        # Base players per table
        base_count = player_count // table_count
        remainder = player_count % table_count

        # Distribute remainder across first tables
        distribution = []
        for i in range(table_count):
            count = base_count + (1 if i < remainder else 0)
            distribution.append(count)

        return distribution
