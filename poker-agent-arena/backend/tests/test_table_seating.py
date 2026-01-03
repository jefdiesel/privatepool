"""Tests for table and seating management modules."""

import pytest
from core.tournament.table import Table, Seat, TableState
from core.tournament.seating import SeatingManager, SeatAssignment


class TestSeat:
    """Tests for Seat dataclass."""

    def test_seat_defaults(self):
        """Test default seat values."""
        seat = Seat(position=0)
        assert seat.position == 0
        assert seat.player_wallet is None
        assert seat.stack == 0
        assert seat.is_active is False
        assert seat.status == "empty"

    def test_seat_with_player(self):
        """Test seat with player data."""
        seat = Seat(
            position=3,
            player_wallet="wallet123",
            stack=10000,
            is_active=True,
            status="active",
        )
        assert seat.position == 3
        assert seat.player_wallet == "wallet123"
        assert seat.stack == 10000
        assert seat.is_active is True
        assert seat.status == "active"


class TestTable:
    """Tests for Table class."""

    def test_table_initialization(self):
        """Test table initializes with correct defaults."""
        table = Table("table_1")
        assert table.table_id == "table_1"
        assert len(table.seats) == 9
        assert table.button_position == 0
        assert table.state == TableState.WAITING
        assert all(s.status == "empty" for s in table.seats)

    def test_seat_player(self):
        """Test seating a player."""
        table = Table("table_1")
        result = table.seat_player("wallet_1", position=3, stack=10000)
        assert result is True
        seat = table.seats[3]
        assert seat.player_wallet == "wallet_1"
        assert seat.stack == 10000
        assert seat.status == "active"

    def test_seat_player_occupied(self):
        """Test cannot seat player in occupied seat."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=3, stack=10000)
        result = table.seat_player("wallet_2", position=3, stack=10000)
        assert result is False

    def test_seat_player_invalid_position(self):
        """Test cannot seat player at invalid position."""
        table = Table("table_1")
        assert table.seat_player("wallet_1", position=-1, stack=10000) is False
        assert table.seat_player("wallet_1", position=9, stack=10000) is False

    def test_remove_player(self):
        """Test removing a player."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=3, stack=10000)
        result = table.remove_player("wallet_1")
        assert result is True
        assert table.seats[3].status == "empty"
        assert table.seats[3].player_wallet is None

    def test_remove_player_not_found(self):
        """Test removing non-existent player."""
        table = Table("table_1")
        result = table.remove_player("wallet_1")
        assert result is False

    def test_get_player_seat(self):
        """Test getting player seat."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=5, stack=10000)
        seat = table.get_player_seat("wallet_1")
        assert seat is not None
        assert seat.position == 5

    def test_get_player_seat_not_found(self):
        """Test getting seat for non-existent player."""
        table = Table("table_1")
        seat = table.get_player_seat("wallet_1")
        assert seat is None

    def test_get_active_players(self):
        """Test getting active players."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=3, stack=10000)
        table.seat_player("wallet_3", position=7, stack=10000)
        active = table.get_active_players()
        assert len(active) == 3

    def test_player_count(self):
        """Test player count."""
        table = Table("table_1")
        assert table.player_count() == 0
        table.seat_player("wallet_1", position=0, stack=10000)
        assert table.player_count() == 1
        table.seat_player("wallet_2", position=3, stack=10000)
        assert table.player_count() == 2

    def test_advance_button(self):
        """Test button advancement."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=3, stack=10000)
        table.seat_player("wallet_3", position=7, stack=10000)
        table.button_position = 0
        new_pos = table.advance_button()
        assert new_pos == 3
        new_pos = table.advance_button()
        assert new_pos == 7
        new_pos = table.advance_button()
        assert new_pos == 0  # Wraps around

    def test_get_small_blind_seat_3plus_players(self):
        """Test SB seat with 3+ players."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=3, stack=10000)
        table.seat_player("wallet_3", position=7, stack=10000)
        # Mark all as in hand
        for seat in table.get_active_players():
            seat.is_active = True
        table.button_position = 0
        sb_seat = table.get_small_blind_seat()
        assert sb_seat is not None
        assert sb_seat.position == 3  # First active player left of button

    def test_get_small_blind_seat_heads_up(self):
        """Test SB seat in heads-up (button is SB)."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=5, stack=10000)
        table.button_position = 0
        sb_seat = table.get_small_blind_seat()
        assert sb_seat is not None
        assert sb_seat.position == 0  # Button is SB in heads-up

    def test_get_big_blind_seat_3plus_players(self):
        """Test BB seat with 3+ players."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=3, stack=10000)
        table.seat_player("wallet_3", position=7, stack=10000)
        # Mark all as in hand
        for seat in table.get_active_players():
            seat.is_active = True
        table.button_position = 0
        bb_seat = table.get_big_blind_seat()
        assert bb_seat is not None
        assert bb_seat.position == 7  # Second active player left of button

    def test_get_big_blind_seat_heads_up(self):
        """Test BB seat in heads-up (non-button is BB)."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=5, stack=10000)
        table.button_position = 0
        bb_seat = table.get_big_blind_seat()
        assert bb_seat is not None
        assert bb_seat.position == 5  # Non-button is BB in heads-up

    def test_get_available_seats(self):
        """Test getting available seats."""
        table = Table("table_1")
        assert len(table.get_available_seats()) == 9
        table.seat_player("wallet_1", position=3, stack=10000)
        available = table.get_available_seats()
        assert len(available) == 8
        assert 3 not in available

    def test_eliminate_player(self):
        """Test eliminating a player."""
        table = Table("table_1")
        table.seat_player("wallet_1", position=3, stack=10000)
        table.eliminate_player("wallet_1")
        seat = table.seats[3]
        assert seat.status == "eliminated"
        assert seat.stack == 0
        assert seat.is_active is False


class TestSeatingManager:
    """Tests for SeatingManager class."""

    def test_calculate_table_count(self):
        """Test table count calculation."""
        manager = SeatingManager(max_table_size=9)
        assert manager._calculate_table_count(0) == 0
        assert manager._calculate_table_count(1) == 1
        assert manager._calculate_table_count(9) == 1
        assert manager._calculate_table_count(10) == 2
        assert manager._calculate_table_count(18) == 2
        assert manager._calculate_table_count(19) == 3
        assert manager._calculate_table_count(27) == 3

    def test_shuffle_players_deterministic(self):
        """Test shuffle is deterministic with same seed."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(10)]
        seed = b"test_seed_123"

        shuffle1 = manager._shuffle_players(players, seed)
        shuffle2 = manager._shuffle_players(players, seed)
        assert shuffle1 == shuffle2

    def test_shuffle_players_different_seeds(self):
        """Test different seeds produce different shuffles."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(10)]

        shuffle1 = manager._shuffle_players(players, b"seed_1")
        shuffle2 = manager._shuffle_players(players, b"seed_2")
        assert shuffle1 != shuffle2

    def test_create_seating_single_table(self):
        """Test creating seating for single table."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(6)]
        seed = b"test_seed"
        starting_stack = 10000

        tables, assignments = manager.create_seating(players, starting_stack, seed)

        assert len(tables) == 1
        assert len(assignments) == 6
        assert tables[0].player_count() == 6

    def test_create_seating_multiple_tables(self):
        """Test creating seating for multiple tables."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(25)]
        seed = b"test_seed"
        starting_stack = 10000

        tables, assignments = manager.create_seating(players, starting_stack, seed)

        assert len(tables) == 3
        assert len(assignments) == 25
        # Distribution should be 9, 8, 8
        counts = [t.player_count() for t in tables]
        assert sum(counts) == 25
        assert max(counts) <= 9

    def test_create_seating_assignments_correct(self):
        """Test that assignments match table state."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(10)]
        seed = b"test_seed"
        starting_stack = 10000

        tables, assignments = manager.create_seating(players, starting_stack, seed)

        for assignment in assignments:
            table = next(t for t in tables if t.table_id == assignment.table_id)
            seat = table.seats[assignment.seat_position]
            assert seat.player_wallet == assignment.wallet
            assert seat.stack == starting_stack

    def test_create_seating_empty_players(self):
        """Test error on empty players list."""
        manager = SeatingManager()
        with pytest.raises(ValueError):
            manager.create_seating([], 10000, b"seed")

    def test_get_table_distribution(self):
        """Test table distribution preview."""
        manager = SeatingManager(max_table_size=9)
        assert manager.get_table_distribution(27) == [9, 9, 9]
        assert manager.get_table_distribution(25) == [9, 8, 8]
        assert manager.get_table_distribution(10) == [5, 5]
        assert manager.get_table_distribution(9) == [9]
        assert manager.get_table_distribution(0) == []

    def test_seating_provably_fair(self):
        """Test that seating is reproducible with same seed."""
        manager = SeatingManager()
        players = [f"wallet_{i}" for i in range(20)]
        seed = b"provably_fair_seed"
        starting_stack = 10000

        _, assignments1 = manager.create_seating(players, starting_stack, seed)
        _, assignments2 = manager.create_seating(players, starting_stack, seed)

        # Same seed should produce same assignments
        for a1, a2 in zip(assignments1, assignments2):
            assert a1.wallet == a2.wallet
            assert a1.table_id == a2.table_id
            assert a1.seat_position == a2.seat_position


class TestTableState:
    """Tests for TableState enum."""

    def test_table_states(self):
        """Test table state values."""
        assert TableState.WAITING.value == "waiting"
        assert TableState.DEALING.value == "dealing"
        assert TableState.BETTING.value == "betting"
        assert TableState.SHOWDOWN.value == "showdown"
