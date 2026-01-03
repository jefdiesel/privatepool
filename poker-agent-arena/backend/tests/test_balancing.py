"""Tests for table balancing module."""

import pytest
from core.tournament.table import Table
from core.tournament.balancing import TableBalancer, TableMove


class TestTableMove:
    """Tests for TableMove dataclass."""

    def test_table_move_creation(self):
        """Test TableMove dataclass creation."""
        move = TableMove(
            player_wallet="wallet_1",
            from_table_id="table_1",
            from_seat=3,
            to_table_id="table_2",
            to_seat=5,
        )
        assert move.player_wallet == "wallet_1"
        assert move.from_table_id == "table_1"
        assert move.from_seat == 3
        assert move.to_table_id == "table_2"
        assert move.to_seat == 5


class TestTableBalancer:
    """Tests for TableBalancer class."""

    def test_balance_not_needed_equal_tables(self):
        """Test no balancing needed when tables are equal."""
        balancer = TableBalancer()

        # Create two tables with equal players
        table1 = Table("table_1")
        table2 = Table("table_2")

        for i in range(5):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)

        tables = [table1, table2]
        assert balancer.check_balance_needed(tables) is False

    def test_balance_not_needed_diff_of_1(self):
        """Test no balancing needed when difference is exactly 1."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        # 5 players on table1, 4 on table2 -> diff is 1, no balance needed
        for i in range(5):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(4):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)

        tables = [table1, table2]
        assert balancer.check_balance_needed(tables) is False

    def test_balance_needed_diff_greater_than_1(self):
        """Test balancing needed when max-min difference > 1."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        # 6 players on table1, 3 on table2 -> diff is 3, balance needed
        for i in range(6):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(3):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)

        tables = [table1, table2]
        assert balancer.check_balance_needed(tables) is True

    def test_balance_not_needed_single_table(self):
        """Test no balancing needed with single table."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        for i in range(5):
            table1.seat_player(f"wallet_{i}", position=i, stack=10000)

        tables = [table1]
        assert balancer.check_balance_needed(tables) is False

    def test_get_move_selects_bb_next_player(self):
        """Test that get_move selects the player who will be BB next."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        # Set up table1 with 6 players
        for i in range(6):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        table1.button_position = 0  # Button at position 0

        # Set up table2 with 3 players
        for i in range(3):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)

        tables = [table1, table2]
        move = balancer.get_move(tables)

        assert move is not None
        assert move.from_table_id == "table_1"
        assert move.to_table_id == "table_2"
        # Should be the player who would be BB next hand
        expected_bb_wallet = table1.get_next_big_blind_player()
        assert move.player_wallet == expected_bb_wallet

    def test_get_move_returns_none_when_balanced(self):
        """Test get_move returns None when no move needed."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        # Equal players
        for i in range(5):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)

        tables = [table1, table2]
        move = balancer.get_move(tables)
        assert move is None

    def test_apply_move(self):
        """Test applying a table move."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        table1.seat_player("wallet_1", position=3, stack=15000)
        table2.seat_player("wallet_2", position=0, stack=10000)

        move = TableMove(
            player_wallet="wallet_1",
            from_table_id="table_1",
            from_seat=3,
            to_table_id="table_2",
            to_seat=5,
        )

        tables = [table1, table2]
        balancer.apply_move(tables, move)

        # Verify player was moved
        assert table1.get_player_seat("wallet_1") is None
        assert table2.get_player_seat("wallet_1") is not None
        assert table2.get_player_seat("wallet_1").position == 5
        assert table2.get_player_seat("wallet_1").stack == 15000

    def test_should_break_table(self):
        """Test should_break_table returns table when consolidation possible."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")
        table3 = Table("table_3")

        # 17 players across 3 tables can fit in 2 tables (9, 8)
        for i in range(6):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(6):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)
        for i in range(5):
            table3.seat_player(f"wallet_t3_{i}", position=i, stack=10000)

        tables = [table1, table2, table3]
        table_to_break = balancer.should_break_table(tables)

        assert table_to_break is not None
        # Should return table with fewest players
        assert table_to_break.table_id == "table_3"

    def test_should_break_table_not_needed(self):
        """Test should_break_table returns None when no break needed."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")
        table3 = Table("table_3")

        # 19 players across 3 tables cannot fit in 2 tables
        for i in range(7):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(6):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)
        for i in range(6):
            table3.seat_player(f"wallet_t3_{i}", position=i, stack=10000)

        tables = [table1, table2, table3]
        table_to_break = balancer.should_break_table(tables)

        assert table_to_break is None

    def test_break_table_redistributes_all_players(self):
        """Test break_table generates moves for all players."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")
        table3 = Table("table_3")

        # Set up 3 tables with few players each
        for i in range(4):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(4):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)
        for i in range(3):
            table3.seat_player(f"wallet_t3_{i}", position=i, stack=10000)

        tables = [table1, table2, table3]
        moves = balancer.break_table(tables, table3)

        # Should have moves for all 3 players from table3
        assert len(moves) == 3

        # All moves should be from table3
        for move in moves:
            assert move.from_table_id == "table_3"

        # All moves should go to remaining tables
        dest_tables = {move.to_table_id for move in moves}
        assert "table_3" not in dest_tables
        assert all(tid in ["table_1", "table_2"] for tid in dest_tables)

    def test_calculate_optimal_tables(self):
        """Test optimal table count calculation."""
        balancer = TableBalancer()

        # Full tables
        assert balancer._calculate_optimal_tables(27) == 3  # 9, 9, 9
        assert balancer._calculate_optimal_tables(18) == 2  # 9, 9
        assert balancer._calculate_optimal_tables(9) == 1   # 9

        # Partial tables
        assert balancer._calculate_optimal_tables(25) == 3  # 9, 8, 8
        assert balancer._calculate_optimal_tables(17) == 2  # 9, 8
        assert balancer._calculate_optimal_tables(10) == 2  # 5, 5

        # Edge cases
        assert balancer._calculate_optimal_tables(0) == 0
        assert balancer._calculate_optimal_tables(1) == 1

    def test_get_best_available_seat_avoids_blinds(self):
        """Test seat selection prefers non-blind positions."""
        balancer = TableBalancer()

        table = Table("table_1")
        # Seat players at positions 0, 3, 5
        table.seat_player("wallet_1", position=0, stack=10000)
        table.seat_player("wallet_2", position=3, stack=10000)
        table.seat_player("wallet_3", position=5, stack=10000)
        table.button_position = 0

        # Available: 1, 2, 4, 6, 7, 8
        # Should avoid positions right after button (1, 2 would be blinds next)
        seat = balancer._get_best_available_seat(table)

        assert seat is not None
        assert seat in [4, 6, 7, 8]  # Positions not immediately after button

    def test_get_best_available_seat_fallback(self):
        """Test seat selection falls back to any available when all would be blinds."""
        balancer = TableBalancer()

        table = Table("table_1")
        # Fill most seats, leaving only blind positions
        for i in [0, 3, 4, 5, 6, 7, 8]:
            table.seat_player(f"wallet_{i}", position=i, stack=10000)
        table.button_position = 0

        # Only positions 1 and 2 available (blind positions)
        seat = balancer._get_best_available_seat(table)

        assert seat is not None
        assert seat in [1, 2]  # Falls back to available seats

    def test_balance_with_three_tables(self):
        """Test balancing across three tables."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")
        table3 = Table("table_3")

        # 8, 8, 5 -> max - min = 3, needs balance
        for i in range(8):
            table1.seat_player(f"wallet_t1_{i}", position=i, stack=10000)
        for i in range(8):
            table2.seat_player(f"wallet_t2_{i}", position=i, stack=10000)
        for i in range(5):
            table3.seat_player(f"wallet_t3_{i}", position=i, stack=10000)

        tables = [table1, table2, table3]
        assert balancer.check_balance_needed(tables) is True

        move = balancer.get_move(tables)
        assert move is not None
        # Should move from one of the full tables to table3
        assert move.from_table_id in ["table_1", "table_2"]
        assert move.to_table_id == "table_3"

    def test_apply_move_invalid_table(self):
        """Test apply_move raises error for invalid table."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table1.seat_player("wallet_1", position=0, stack=10000)

        move = TableMove(
            player_wallet="wallet_1",
            from_table_id="table_1",
            from_seat=0,
            to_table_id="nonexistent",
            to_seat=0,
        )

        with pytest.raises(ValueError):
            balancer.apply_move([table1], move)

    def test_apply_move_player_not_found(self):
        """Test apply_move raises error when player not at source."""
        balancer = TableBalancer()

        table1 = Table("table_1")
        table2 = Table("table_2")

        move = TableMove(
            player_wallet="nonexistent",
            from_table_id="table_1",
            from_seat=0,
            to_table_id="table_2",
            to_seat=0,
        )

        with pytest.raises(ValueError):
            balancer.apply_move([table1, table2], move)
