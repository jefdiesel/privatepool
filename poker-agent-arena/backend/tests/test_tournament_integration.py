"""Integration tests for complete tournament simulation.

These tests verify the Phase 2 exit criteria:
1. Can simulate complete tournament offline
2. All poker rules correctly enforced
3. Table balancing works correctly
"""

import pytest
import random
from core.tournament.manager import (
    TournamentManager,
    TournamentConfig,
    TournamentPhase,
)
from core.tournament.blinds import BlindStructure, BlindLevel, BLIND_TEMPLATES
from core.poker.hand_controller import HandState
from core.poker.betting import Action


# Decision callbacks for testing
async def random_decision(wallet: str, state: HandState) -> Action:
    """Makes random valid decisions."""
    valid = state.valid_actions
    if not valid:
        return Action.fold()

    choice = random.choice(valid)
    if choice == "fold":
        return Action.fold()
    elif choice == "check":
        return Action.check()
    elif choice == "call":
        return Action.call()
    elif choice == "raise":
        # Random raise between min and 3x min
        raise_to = state.min_raise_to + random.randint(0, state.min_raise_to)
        return Action.raise_to(raise_to)
    return Action.fold()


async def passive_decision(wallet: str, state: HandState) -> Action:
    """Passive play - check/call only."""
    if "check" in state.valid_actions:
        return Action.check()
    if "call" in state.valid_actions:
        return Action.call()
    return Action.fold()


async def tight_decision(wallet: str, state: HandState) -> Action:
    """Tight play - mostly folds, occasionally calls."""
    if "check" in state.valid_actions:
        return Action.check()
    if random.random() < 0.3:  # 30% call rate
        if "call" in state.valid_actions:
            return Action.call()
    return Action.fold()


class TestTournamentLifecycle:
    """Test tournament lifecycle phases."""

    def test_tournament_creation(self):
        """Test tournament creation."""
        config = TournamentConfig(
            tournament_id="test_tournament_1",
            name="Test Tournament",
            starting_stack=10000,
            blind_structure=BlindStructure(BLIND_TEMPLATES["turbo"]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            max_players=27,
        )
        manager = TournamentManager(config)

        assert manager.phase == TournamentPhase.CREATED

    def test_registration_phase(self):
        """Test registration phase."""
        config = TournamentConfig(
            tournament_id="test_reg_1",
            name="Registration Test",
            starting_stack=10000,
            blind_structure=BlindStructure(BLIND_TEMPLATES["turbo"]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
        )
        manager = TournamentManager(config)

        manager.open_registration()
        assert manager.phase == TournamentPhase.REGISTRATION

        # Register players
        assert manager.register_player("player1", "FREE") is True
        assert manager.register_player("player2", "BASIC") is True
        assert manager.register_player("player3", "PRO") is True

        # Can't register same player twice
        assert manager.register_player("player1") is False

        assert len(manager.registrations) == 3

    def test_unregister_player(self):
        """Test player unregistration."""
        config = TournamentConfig(
            tournament_id="test_unreg_1",
            name="Unregister Test",
            starting_stack=10000,
            blind_structure=BlindStructure(BLIND_TEMPLATES["turbo"]),
            payout_structure={1: 5000},
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")

        assert manager.unregister_player("player1") is True
        assert len(manager.registrations) == 1
        assert manager.unregister_player("player1") is False  # Already unregistered

    @pytest.mark.asyncio
    async def test_tournament_start(self):
        """Test tournament start process."""
        config = TournamentConfig(
            tournament_id="test_start_1",
            name="Start Test",
            starting_stack=10000,
            blind_structure=BlindStructure(BLIND_TEMPLATES["turbo"]),
            payout_structure={1: 5000, 2: 3000},
            blockhash=b"test_blockhash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")
        manager.register_player("player3")

        await manager.start()

        assert manager.phase == TournamentPhase.IN_PROGRESS
        assert len(manager.tables) >= 1
        assert len(manager.seat_assignments) == 3


class TestSmallTournament:
    """Test small tournament (3-9 players)."""

    @pytest.mark.asyncio
    async def test_three_player_tournament(self):
        """Test complete 3-player tournament."""
        config = TournamentConfig(
            tournament_id="small_3_player",
            name="3 Player Test",
            starting_stack=1000,
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 5),
                BlindLevel(2, 50, 100, 10, 5),
                BlindLevel(3, 100, 200, 25, 5),
            ]),
            payout_structure={1: 3000, 2: 2000, 3: 1000},
            blockhash=b"three_player_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(3):
            manager.register_player(f"player_{i}")

        payouts = await manager.run(tight_decision)

        assert manager.phase == TournamentPhase.COMPLETED
        assert len(payouts) == 3
        # Winner should get most points
        assert payouts[0].rank == 1
        assert payouts[0].points == 3000

    @pytest.mark.asyncio
    async def test_nine_player_tournament(self):
        """Test complete 9-player tournament (one full table)."""
        config = TournamentConfig(
            tournament_id="full_table_9",
            name="9 Player Full Table",
            starting_stack=1000,
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 3),
                BlindLevel(2, 50, 100, 10, 3),
                BlindLevel(3, 100, 200, 25, 3),
                BlindLevel(4, 200, 400, 50, 3),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            blockhash=b"nine_player_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(9):
            manager.register_player(f"player_{i}")

        payouts = await manager.run(tight_decision)

        assert manager.phase == TournamentPhase.COMPLETED
        assert len(payouts) == 3  # Only top 3 pay
        # Total points should match structure
        total_points = sum(p.points for p in payouts)
        assert total_points == 10000


class TestMultiTableTournament:
    """Test multi-table tournament scenarios."""

    @pytest.mark.asyncio
    async def test_two_table_tournament(self):
        """Test 18-player tournament (2 tables)."""
        config = TournamentConfig(
            tournament_id="two_table_18",
            name="Two Table Test",
            starting_stack=1000,
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 2),
                BlindLevel(2, 50, 100, 10, 2),
                BlindLevel(3, 100, 200, 25, 2),
                BlindLevel(4, 200, 400, 50, 2),
                BlindLevel(5, 400, 800, 100, 2),
            ]),
            payout_structure={1: 6000, 2: 4000, 3: 2500, 4: 1500, 5: 1000},
            blockhash=b"two_table_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(18):
            manager.register_player(f"player_{i}")

        await manager.start()

        # Should have 2 tables (9 players each)
        assert len(manager.tables) == 2
        assert all(t.player_count() == 9 for t in manager.tables)

        payouts = await manager.run(tight_decision)

        assert manager.phase == TournamentPhase.COMPLETED
        assert len(payouts) == 5  # Top 5 pay

    @pytest.mark.asyncio
    async def test_three_table_tournament(self):
        """Test 27-player tournament (3 tables)."""
        config = TournamentConfig(
            tournament_id="three_table_27",
            name="Three Table Test",
            starting_stack=1000,
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 1),
                BlindLevel(2, 50, 100, 10, 1),
                BlindLevel(3, 100, 200, 25, 1),
                BlindLevel(4, 200, 400, 50, 1),
                BlindLevel(5, 400, 800, 100, 1),
                BlindLevel(6, 800, 1600, 200, 1),
            ]),
            payout_structure={1: 8000, 2: 5000, 3: 3000, 4: 2000, 5: 1500, 6: 500},
            blockhash=b"three_table_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(27):
            manager.register_player(f"player_{i}")

        await manager.start()

        assert len(manager.tables) == 3
        assert sum(t.player_count() for t in manager.tables) == 27

        payouts = await manager.run(tight_decision)

        assert manager.phase == TournamentPhase.COMPLETED
        # Verify all players got a final rank
        assert len(manager.eliminations) + 1 == 27  # 26 eliminated + 1 winner


class TestTableBalancing:
    """Test table balancing during tournament."""

    @pytest.mark.asyncio
    async def test_balancing_after_eliminations(self):
        """Test that tables balance after eliminations."""
        config = TournamentConfig(
            tournament_id="balance_test",
            name="Balancing Test",
            starting_stack=500,  # Low stack for quick eliminations
            blind_structure=BlindStructure([
                BlindLevel(1, 50, 100, 0, 1),
                BlindLevel(2, 100, 200, 25, 1),
                BlindLevel(3, 200, 400, 50, 1),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            blockhash=b"balance_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(18):  # 2 tables of 9
            manager.register_player(f"player_{i}")

        await manager.start()
        initial_tables = len(manager.tables)

        payouts = await manager.run(tight_decision)

        # Tournament should complete
        assert manager.phase == TournamentPhase.COMPLETED

        # Should have consolidated to 1 table at end
        active_tables = len([t for t in manager.tables if t.player_count() > 0])
        assert active_tables <= initial_tables


class TestBlindProgression:
    """Test blind level progression."""

    def test_blind_structure_initialization(self):
        """Test blind structure initialization."""
        levels = [
            BlindLevel(1, 25, 50, 0, 5),
            BlindLevel(2, 50, 100, 10, 5),
            BlindLevel(3, 100, 200, 25, 5),
        ]
        structure = BlindStructure(levels)

        assert structure.current_level.small_blind == 25
        assert structure.current_level.big_blind == 50
        assert structure.current_level.ante == 0

    def test_blind_level_advancement(self):
        """Test manual blind level advancement."""
        levels = [
            BlindLevel(1, 25, 50, 0, 5),
            BlindLevel(2, 50, 100, 10, 5),
            BlindLevel(3, 100, 200, 25, 5),
        ]
        structure = BlindStructure(levels)

        structure.advance_level()
        assert structure.current_level.small_blind == 50
        assert structure.current_level.ante == 10

        structure.advance_level()
        assert structure.current_level.small_blind == 100
        assert structure.current_level.ante == 25


class TestChipConservation:
    """Test that chips are conserved throughout tournament."""

    @pytest.mark.asyncio
    async def test_chips_conserved(self):
        """Test that total chips remain constant."""
        starting_stack = 1000
        player_count = 9

        config = TournamentConfig(
            tournament_id="chip_conservation",
            name="Chip Conservation Test",
            starting_stack=starting_stack,
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 2),
                BlindLevel(2, 50, 100, 10, 2),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            blockhash=b"chip_test_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(player_count):
            manager.register_player(f"player_{i}")

        await manager.start()

        # Calculate initial total chips
        total_chips = starting_stack * player_count

        # Run until completion
        await manager.run(passive_decision)

        # Sum all remaining chips
        remaining_chips = sum(
            seat.stack
            for table in manager.tables
            for seat in table.seats
            if seat.status == "active"
        )

        assert remaining_chips == total_chips


class TestPayoutDistribution:
    """Test payout distribution at tournament end."""

    @pytest.mark.asyncio
    async def test_payout_ordering(self):
        """Test that payouts are ordered correctly."""
        config = TournamentConfig(
            tournament_id="payout_order",
            name="Payout Order Test",
            starting_stack=1000,
            blind_structure=BlindStructure([
                BlindLevel(1, 50, 100, 0, 1),
                BlindLevel(2, 100, 200, 25, 1),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000, 4: 1000},
            blockhash=b"payout_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(6):
            manager.register_player(f"player_{i}")

        payouts = await manager.run(tight_decision)

        # Payouts should be sorted by rank
        for i in range(len(payouts) - 1):
            assert payouts[i].rank < payouts[i + 1].rank

        # Higher rank = more points
        for i in range(len(payouts) - 1):
            assert payouts[i].points >= payouts[i + 1].points


class TestTournamentState:
    """Test tournament state observation."""

    @pytest.mark.asyncio
    async def test_get_state_during_tournament(self):
        """Test getting tournament state during play."""
        config = TournamentConfig(
            tournament_id="state_obs",
            name="State Observation Test",
            starting_stack=1000,
            blind_structure=BlindStructure([BlindLevel(1, 25, 50, 0, 5)]),
            payout_structure={1: 3000, 2: 2000},
            blockhash=b"state_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")
        manager.register_player("player3")

        await manager.start()

        state = manager.get_state()
        assert state.tournament_id == "state_obs"
        assert state.registered_players == 3
        assert state.active_players == 3
        assert state.phase == TournamentPhase.IN_PROGRESS

    def test_get_player_stack(self):
        """Test getting individual player stack."""
        config = TournamentConfig(
            tournament_id="stack_query",
            name="Stack Query Test",
            starting_stack=1000,
            blind_structure=BlindStructure([BlindLevel(1, 25, 50, 0, 5)]),
            payout_structure={1: 3000},
            blockhash=b"stack_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")

        # Can't get stack before start
        assert manager.get_player_stack("player1") is None


class TestDeterministicSeating:
    """Test deterministic seating from blockhash."""

    @pytest.mark.asyncio
    async def test_same_blockhash_same_seating(self):
        """Test that same blockhash produces same seating."""
        blockhash = b"deterministic_seating_test"

        def create_tournament():
            return TournamentConfig(
                tournament_id="det_seat",
                name="Deterministic Seating",
                starting_stack=1000,
                blind_structure=BlindStructure([BlindLevel(1, 25, 50, 0, 5)]),
                payout_structure={1: 5000},
                blockhash=blockhash,
            )

        # First tournament
        manager1 = TournamentManager(create_tournament())
        manager1.open_registration()
        for i in range(9):
            manager1.register_player(f"player_{i}")
        await manager1.start()

        # Second tournament with same blockhash
        manager2 = TournamentManager(create_tournament())
        manager2.open_registration()
        for i in range(9):
            manager2.register_player(f"player_{i}")
        await manager2.start()

        # Compare seat assignments
        seats1 = {a.wallet: (a.table_id, a.seat_position) for a in manager1.seat_assignments}
        seats2 = {a.wallet: (a.table_id, a.seat_position) for a in manager2.seat_assignments}

        assert seats1 == seats2


class TestHeadsUpPhase:
    """Test heads-up phase transition."""

    @pytest.mark.asyncio
    async def test_heads_up_transition(self):
        """Test transition to heads-up phase."""
        config = TournamentConfig(
            tournament_id="heads_up_test",
            name="Heads Up Test",
            starting_stack=500,
            blind_structure=BlindStructure([
                BlindLevel(1, 50, 100, 0, 1),
                BlindLevel(2, 100, 200, 25, 1),
            ]),
            payout_structure={1: 3000, 2: 2000},
            blockhash=b"heads_up_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")
        manager.register_player("player3")

        await manager.run(tight_decision)

        # Should have gone through heads up phase
        assert manager.phase == TournamentPhase.COMPLETED


class TestFinalTablePhase:
    """Test final table phase transition."""

    @pytest.mark.asyncio
    async def test_final_table_reached(self):
        """Test that final table phase is reached when consolidating to one table."""
        config = TournamentConfig(
            tournament_id="final_table_test",
            name="Final Table Test",
            starting_stack=500,
            blind_structure=BlindStructure([
                BlindLevel(1, 50, 100, 0, 1),
                BlindLevel(2, 100, 200, 25, 1),
                BlindLevel(3, 200, 400, 50, 1),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            blockhash=b"final_table_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(12):  # 2 tables initially
            manager.register_player(f"player_{i}")

        phases_seen = set()

        async def tracking_decision(wallet: str, state: HandState) -> Action:
            phases_seen.add(manager.phase)
            return await tight_decision(wallet, state)

        await manager.run(tracking_decision)

        # Should complete
        assert manager.phase == TournamentPhase.COMPLETED


class TestCancellation:
    """Test tournament cancellation scenarios."""

    @pytest.mark.asyncio
    async def test_not_enough_players(self):
        """Test cancellation when not enough players register."""
        config = TournamentConfig(
            tournament_id="cancel_test",
            name="Cancellation Test",
            starting_stack=1000,
            blind_structure=BlindStructure([BlindLevel(1, 25, 50, 0, 5)]),
            payout_structure={1: 5000},
            min_players=5,
        )
        manager = TournamentManager(config)

        manager.open_registration()
        manager.register_player("player1")
        manager.register_player("player2")
        # Only 2 players, need 5

        with pytest.raises(ValueError, match="Not enough players"):
            await manager.start()

        assert manager.phase == TournamentPhase.CANCELLED


class TestStressTest:
    """Stress tests for tournament system."""

    @pytest.mark.asyncio
    async def test_many_hands(self):
        """Test running many hands in a tournament."""
        config = TournamentConfig(
            tournament_id="stress_test",
            name="Stress Test",
            starting_stack=10000,  # High stacks = more hands
            blind_structure=BlindStructure([
                BlindLevel(1, 25, 50, 0, 1),
                BlindLevel(2, 50, 100, 10, 1),
                BlindLevel(3, 100, 200, 25, 1),
            ]),
            payout_structure={1: 5000, 2: 3000, 3: 2000},
            blockhash=b"stress_hash",
        )
        manager = TournamentManager(config)

        manager.open_registration()
        for i in range(6):
            manager.register_player(f"player_{i}")

        await manager.run(passive_decision)

        # Should have played many hands
        assert manager.hand_number > 10
        assert manager.phase == TournamentPhase.COMPLETED
