"""Tournament manager module for orchestrating complete poker tournaments.

Manages the full lifecycle of a multi-table tournament from registration
through final standings and payout distribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Awaitable, Optional, List, Dict
import asyncio
import hashlib

from .table import Table, TableState
from .blinds import BlindStructure, BlindLevel
from .seating import SeatingManager, SeatAssignment
from .balancing import TableBalancer, TableMove
from .payouts import PayoutCalculator, PointsAward

from ..poker.hand_controller import (
    HandController,
    HandResult,
    HandState,
    PlayerConfig,
    Action,
)
from ..poker.deck import Deck


class TournamentPhase(Enum):
    """Tournament lifecycle phases."""
    CREATED = "created"
    REGISTRATION = "registration"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    FINAL_TABLE = "final_table"
    HEADS_UP = "heads_up"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TournamentConfig:
    """Configuration for a tournament."""
    tournament_id: str
    name: str
    starting_stack: int
    blind_structure: BlindStructure
    payout_structure: Dict[int, int]  # rank -> points
    max_players: int = 54
    min_players: int = 2
    blockhash: bytes = field(default_factory=lambda: b"")  # For provable fairness


@dataclass
class PlayerRegistration:
    """Registered player in a tournament."""
    wallet: str
    registered_at: datetime
    tier: str  # FREE, BASIC, PRO
    agent_config: dict = field(default_factory=dict)


@dataclass
class TournamentState:
    """Current state of the tournament for observation."""
    tournament_id: str
    phase: TournamentPhase
    registered_players: int
    active_players: int
    eliminated_players: int
    tables_active: int
    current_blind_level: BlindLevel
    hands_played: int
    time_elapsed_seconds: int
    prize_pool: int


@dataclass
class EliminationRecord:
    """Record of a player elimination."""
    wallet: str
    eliminated_by: Optional[str]
    final_rank: int
    hand_number: int
    prize_won: int


# Type for decision callback
DecisionCallback = Callable[[str, HandState], Awaitable[Action]]


class TournamentManager:
    """Orchestrates a complete multi-table poker tournament.

    Lifecycle:
    1. CREATED - Tournament initialized
    2. REGISTRATION - Players can register
    3. STARTING - Registration closed, seating players
    4. IN_PROGRESS - Tournament running
    5. FINAL_TABLE - Down to one table
    6. HEADS_UP - Final two players
    7. COMPLETED - Winner determined

    Usage:
        config = TournamentConfig(...)
        manager = TournamentManager(config)

        # Registration phase
        manager.open_registration()
        for player in players:
            manager.register_player(player)

        # Start tournament
        await manager.start()

        # Run until complete
        await manager.run(decision_callback)
    """

    def __init__(self, config: TournamentConfig):
        """Initialize tournament manager.

        Args:
            config: Tournament configuration
        """
        self.config = config
        self.phase = TournamentPhase.CREATED

        # Player tracking
        self.registrations: Dict[str, PlayerRegistration] = {}
        self.eliminations: List[EliminationRecord] = []

        # Table management
        self.tables: List[Table] = []
        self.seat_assignments: List[SeatAssignment] = []

        # Managers
        self.seating_manager = SeatingManager()
        self.balancer = TableBalancer()
        self.payout_calculator = PayoutCalculator(config.payout_structure)

        # Hand tracking
        self.hand_number = 0
        self.hands_history: List[HandResult] = []

        # Timing
        self.started_at: Optional[datetime] = None

        # Active hand controllers per table
        self.active_hands: Dict[str, HandController] = {}

    def open_registration(self) -> None:
        """Open tournament for registration."""
        if self.phase != TournamentPhase.CREATED:
            raise ValueError(f"Cannot open registration in phase {self.phase}")
        self.phase = TournamentPhase.REGISTRATION

    def close_registration(self) -> None:
        """Close registration (no more players can join)."""
        if self.phase != TournamentPhase.REGISTRATION:
            raise ValueError(f"Cannot close registration in phase {self.phase}")
        self.phase = TournamentPhase.STARTING

    def register_player(
        self,
        wallet: str,
        tier: str = "FREE",
        agent_config: Optional[dict] = None,
    ) -> bool:
        """Register a player for the tournament.

        Args:
            wallet: Player's wallet address
            tier: Agent tier (FREE, BASIC, PRO)
            agent_config: Optional agent configuration

        Returns:
            True if registered successfully, False otherwise
        """
        if self.phase != TournamentPhase.REGISTRATION:
            return False

        if wallet in self.registrations:
            return False  # Already registered

        if len(self.registrations) >= self.config.max_players:
            return False  # Full

        self.registrations[wallet] = PlayerRegistration(
            wallet=wallet,
            registered_at=datetime.now(),
            tier=tier,
            agent_config=agent_config or {},
        )
        return True

    def unregister_player(self, wallet: str) -> bool:
        """Unregister a player from the tournament.

        Args:
            wallet: Player's wallet address

        Returns:
            True if unregistered successfully
        """
        if self.phase != TournamentPhase.REGISTRATION:
            return False

        if wallet not in self.registrations:
            return False

        del self.registrations[wallet]
        return True

    def _generate_seating_seed(self) -> bytes:
        """Generate deterministic seed for seating."""
        hasher = hashlib.sha256()
        hasher.update(self.config.blockhash)
        hasher.update(self.config.tournament_id.encode())
        hasher.update(b"seating")
        return hasher.digest()

    def _generate_hand_seed(self, hand_number: int) -> bytes:
        """Generate deterministic seed for a hand."""
        return Deck.generate_seed(
            self.config.blockhash,
            self.config.tournament_id,
            hand_number,
        )

    async def start(self) -> None:
        """Start the tournament (close registration and seat players)."""
        if self.phase == TournamentPhase.REGISTRATION:
            self.close_registration()

        if self.phase != TournamentPhase.STARTING:
            raise ValueError(f"Cannot start tournament in phase {self.phase}")

        if len(self.registrations) < self.config.min_players:
            self.phase = TournamentPhase.CANCELLED
            raise ValueError(
                f"Not enough players: {len(self.registrations)} < {self.config.min_players}"
            )

        # Create seating
        players = list(self.registrations.keys())
        seed = self._generate_seating_seed()

        self.tables, self.seat_assignments = self.seating_manager.create_seating(
            players=players,
            starting_stack=self.config.starting_stack,
            seed=seed,
        )

        # Start blind timer
        self.config.blind_structure.start_level()
        self.started_at = datetime.now()

        # Update phase based on table count
        self._update_phase()

    def _update_phase(self) -> None:
        """Update tournament phase based on current state."""
        active_players = self._count_active_players()
        active_tables = len([t for t in self.tables if t.player_count() > 0])

        if active_players <= 0:
            self.phase = TournamentPhase.COMPLETED
        elif active_players == 1:
            self.phase = TournamentPhase.COMPLETED
        elif active_players == 2:
            self.phase = TournamentPhase.HEADS_UP
        elif active_tables == 1:
            self.phase = TournamentPhase.FINAL_TABLE
        else:
            self.phase = TournamentPhase.IN_PROGRESS

    def _count_active_players(self) -> int:
        """Count total active players across all tables."""
        return sum(table.player_count() for table in self.tables)

    def _get_active_tables(self) -> List[Table]:
        """Get tables with active players."""
        return [t for t in self.tables if t.player_count() >= 2]

    async def run(self, decision_callback: DecisionCallback) -> List[PointsAward]:
        """Run the tournament until completion.

        Args:
            decision_callback: Async function (wallet, HandState) -> Action

        Returns:
            List of PointsAward for all paying positions
        """
        if self.phase in (TournamentPhase.REGISTRATION, TournamentPhase.STARTING):
            await self.start()

        while self.phase not in (TournamentPhase.COMPLETED, TournamentPhase.CANCELLED):
            # Check for blind level advancement
            self.config.blind_structure.check_level_up()

            # Run hands on all active tables
            active_tables = self._get_active_tables()

            if not active_tables:
                self.phase = TournamentPhase.COMPLETED
                break

            # Run one hand on each table concurrently
            hand_tasks = []
            for table in active_tables:
                task = self._run_hand_on_table(table, decision_callback)
                hand_tasks.append(task)

            # Wait for all hands to complete
            results = await asyncio.gather(*hand_tasks, return_exceptions=True)

            # Process results and eliminations
            for result in results:
                if isinstance(result, Exception):
                    # Log error but continue tournament
                    continue
                if isinstance(result, HandResult):
                    self.hands_history.append(result)

            # Check for eliminations and handle table balancing
            await self._process_eliminations()
            await self._balance_tables()

            # Update phase
            self._update_phase()

        # Calculate final standings and payouts
        return self._calculate_payouts()

    async def _run_hand_on_table(
        self,
        table: Table,
        decision_callback: DecisionCallback,
    ) -> Optional[HandResult]:
        """Run a single hand on a table.

        Args:
            table: The table to run the hand on
            decision_callback: Decision callback function

        Returns:
            HandResult or None if hand couldn't run
        """
        active_seats = table.get_active_players()
        if len(active_seats) < 2:
            return None

        self.hand_number += 1
        hand_id = f"{self.config.tournament_id}_hand_{self.hand_number}"

        # Advance button
        table.advance_button()

        # Build player configs
        players = [
            PlayerConfig(
                wallet=seat.player_wallet,
                stack=seat.stack,
                seat_position=seat.position,
            )
            for seat in active_seats
            if seat.player_wallet is not None
        ]

        # Find button position in player list
        button_idx = 0
        for i, p in enumerate(players):
            if p.seat_position == table.button_position:
                button_idx = i
                break

        # Get current blind level
        blind_level = self.config.blind_structure.current_level

        # Create hand controller
        controller = HandController(
            hand_id=hand_id,
            players=players,
            button_position=button_idx,
            small_blind=blind_level.small_blind,
            big_blind=blind_level.big_blind,
            ante=blind_level.ante,
            deck_seed=self._generate_hand_seed(self.hand_number),
        )

        self.active_hands[table.table_id] = controller

        # Create wrapped callback that includes wallet
        async def table_decision_callback(state: HandState) -> Action:
            wallet = state.action_on
            if wallet is None:
                return Action.fold()
            return await decision_callback(wallet, state)

        try:
            result = await controller.run(table_decision_callback)

            # Update table stacks from hand result
            for player in controller.players:
                seat = table.get_player_seat(player.wallet)
                if seat:
                    seat.stack = player.stack
                    if player.stack == 0:
                        table.eliminate_player(player.wallet)

            return result
        finally:
            del self.active_hands[table.table_id]

    async def _process_eliminations(self) -> None:
        """Process any new eliminations."""
        # Count current active to determine rank
        active_count = self._count_active_players()

        for table in self.tables:
            for seat in table.seats:
                if seat.status == "eliminated" and seat.player_wallet:
                    # Check if already recorded
                    if any(e.wallet == seat.player_wallet for e in self.eliminations):
                        continue

                    # Record elimination
                    # Rank = active players remaining + 1
                    # E.g., if 2 players remain, eliminated player gets rank 3
                    final_rank = active_count + 1
                    prize = self.config.payout_structure.get(final_rank, 0)

                    self.eliminations.append(EliminationRecord(
                        wallet=seat.player_wallet,
                        eliminated_by=None,  # Could track from hand history
                        final_rank=final_rank,
                        hand_number=self.hand_number,
                        prize_won=prize,
                    ))

    async def _balance_tables(self) -> None:
        """Balance tables and break tables as needed."""
        active_tables = [t for t in self.tables if t.player_count() > 0]

        if len(active_tables) <= 1:
            return

        # Check if a table should break
        table_to_break = self.balancer.should_break_table(active_tables)
        if table_to_break:
            moves = self.balancer.break_table(active_tables, table_to_break)
            for move in moves:
                self.balancer.apply_move(self.tables, move)
            # Remove broken table from active list
            active_tables = [t for t in active_tables if t.table_id != table_to_break.table_id]

        # Balance remaining tables
        while self.balancer.check_balance_needed(active_tables):
            move = self.balancer.get_move(active_tables)
            if move is None:
                break
            self.balancer.apply_move(self.tables, move)

    def _calculate_payouts(self) -> List[PointsAward]:
        """Calculate final standings and payouts."""
        # Build final rankings
        final_rankings: List[tuple] = []

        # Add eliminations in reverse order (last eliminated = higher rank)
        for elim in reversed(self.eliminations):
            final_rankings.append((elim.wallet, elim.final_rank))

        # Add remaining player(s) as winner(s)
        remaining = []
        for table in self.tables:
            for seat in table.get_active_players():
                if seat.player_wallet:
                    remaining.append((seat.player_wallet, seat.stack))

        # Sort remaining by stack (highest = 1st place)
        remaining.sort(key=lambda x: x[1], reverse=True)
        for i, (wallet, _stack) in enumerate(remaining):
            final_rankings.append((wallet, i + 1))

        return self.payout_calculator.calculate(final_rankings)

    def get_state(self) -> TournamentState:
        """Get current tournament state for observation."""
        active_players = self._count_active_players()
        eliminated = len(self.eliminations)
        active_tables = len([t for t in self.tables if t.player_count() > 0])

        elapsed = 0
        if self.started_at:
            elapsed = int((datetime.now() - self.started_at).total_seconds())

        return TournamentState(
            tournament_id=self.config.tournament_id,
            phase=self.phase,
            registered_players=len(self.registrations),
            active_players=active_players,
            eliminated_players=eliminated,
            tables_active=active_tables,
            current_blind_level=self.config.blind_structure.current_level,
            hands_played=self.hand_number,
            time_elapsed_seconds=elapsed,
            prize_pool=self.payout_calculator.total_points(),
        )

    def get_player_stack(self, wallet: str) -> Optional[int]:
        """Get a player's current stack.

        Args:
            wallet: Player's wallet address

        Returns:
            Stack size or None if player not found/eliminated
        """
        for table in self.tables:
            seat = table.get_player_seat(wallet)
            if seat and seat.status == "active":
                return seat.stack
        return None

    def get_player_table(self, wallet: str) -> Optional[str]:
        """Get the table ID where a player is seated.

        Args:
            wallet: Player's wallet address

        Returns:
            Table ID or None if not found
        """
        for table in self.tables:
            seat = table.get_player_seat(wallet)
            if seat:
                return table.table_id
        return None

    def get_standings(self) -> List[tuple]:
        """Get current standings (wallet, rank, stack/prize).

        Returns:
            List of (wallet, rank, value) tuples
        """
        standings: List[tuple] = []

        # Active players by stack
        active = []
        for table in self.tables:
            for seat in table.get_active_players():
                if seat.player_wallet:
                    active.append((seat.player_wallet, seat.stack))

        active.sort(key=lambda x: x[1], reverse=True)
        for i, (wallet, stack) in enumerate(active):
            standings.append((wallet, i + 1, stack))

        # Eliminated players
        for elim in self.eliminations:
            standings.append((elim.wallet, elim.final_rank, elim.prize_won))

        return standings
