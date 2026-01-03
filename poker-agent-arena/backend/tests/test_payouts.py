"""Tests for payout calculator."""

import pytest

from core.tournament.payouts import (
    PointsAward,
    PayoutCalculator,
    PAYOUT_FIXTURES,
)


class TestPointsAward:
    """Tests for PointsAward dataclass."""

    def test_points_award_creation(self):
        """Test creating a points award."""
        award = PointsAward(
            wallet="0x1234567890abcdef",
            rank=1,
            points=5000,
        )
        assert award.wallet == "0x1234567890abcdef"
        assert award.rank == 1
        assert award.points == 5000

    def test_points_award_equality(self):
        """Test points award equality."""
        award1 = PointsAward("0xabc", 1, 5000)
        award2 = PointsAward("0xabc", 1, 5000)
        assert award1 == award2


class TestPayoutCalculator:
    """Tests for PayoutCalculator class."""

    @pytest.fixture
    def standard_payout(self):
        """Create standard payout calculator."""
        return PayoutCalculator(PAYOUT_FIXTURES["standard_27"])

    @pytest.fixture
    def top_heavy_payout(self):
        """Create top-heavy payout calculator."""
        return PayoutCalculator(PAYOUT_FIXTURES["top_heavy_27"])

    @pytest.fixture
    def flat_payout(self):
        """Create flat payout calculator."""
        return PayoutCalculator(PAYOUT_FIXTURES["flat_27"])

    def test_total_points_standard(self, standard_payout):
        """Test total points calculation for standard structure."""
        # 5000 + 3000 + 2000 + 1000 + 500 + 500 = 12000
        assert standard_payout.total_points() == 12000

    def test_total_points_top_heavy(self, top_heavy_payout):
        """Test total points for top-heavy structure."""
        # 8000 + 3000 + 1000 = 12000
        assert top_heavy_payout.total_points() == 12000

    def test_total_points_flat(self, flat_payout):
        """Test total points for flat structure."""
        # 2000 + 1800 + 1600 + 1400 + 1200 + 1000 + 800 + 600 + 600 = 11000
        assert flat_payout.total_points() == 11000

    def test_paying_positions_standard(self, standard_payout):
        """Test paying positions count for standard."""
        assert standard_payout.paying_positions() == 6

    def test_paying_positions_top_heavy(self, top_heavy_payout):
        """Test paying positions count for top-heavy."""
        assert top_heavy_payout.paying_positions() == 3

    def test_paying_positions_flat(self, flat_payout):
        """Test paying positions count for flat."""
        assert flat_payout.paying_positions() == 9

    def test_calculate_all_in_money(self, standard_payout):
        """Test calculate when all players are in paying positions."""
        rankings = [
            ("0xwinner", 1),
            ("0xsecond", 2),
            ("0xthird", 3),
        ]
        awards = standard_payout.calculate(rankings)

        assert len(awards) == 3
        assert awards[0] == PointsAward("0xwinner", 1, 5000)
        assert awards[1] == PointsAward("0xsecond", 2, 3000)
        assert awards[2] == PointsAward("0xthird", 3, 2000)

    def test_calculate_some_out_of_money(self, standard_payout):
        """Test calculate with players outside paying positions."""
        rankings = [
            ("0xwinner", 1),
            ("0xsecond", 2),
            ("0xseventh", 7),  # Out of money
            ("0xeighth", 8),   # Out of money
        ]
        awards = standard_payout.calculate(rankings)

        # Only 2 awards (ranks 1 and 2 are in money)
        assert len(awards) == 2
        assert awards[0].wallet == "0xwinner"
        assert awards[1].wallet == "0xsecond"

    def test_calculate_empty_rankings(self, standard_payout):
        """Test calculate with no rankings."""
        awards = standard_payout.calculate([])
        assert awards == []

    def test_calculate_orders_by_rank(self, standard_payout):
        """Test that results are ordered by rank."""
        # Provide rankings out of order
        rankings = [
            ("0xthird", 3),
            ("0xwinner", 1),
            ("0xsecond", 2),
        ]
        awards = standard_payout.calculate(rankings)

        assert awards[0].rank == 1
        assert awards[1].rank == 2
        assert awards[2].rank == 3

    def test_calculate_full_tournament(self, standard_payout):
        """Test calculate with full tournament results."""
        rankings = [
            ("0xp1", 1),
            ("0xp2", 2),
            ("0xp3", 3),
            ("0xp4", 4),
            ("0xp5", 5),
            ("0xp6", 6),
            ("0xp7", 7),
            ("0xp8", 8),
            ("0xp9", 9),
        ]
        awards = standard_payout.calculate(rankings)

        # Standard pays 6 positions
        assert len(awards) == 6

        # Verify correct points
        assert awards[0].points == 5000
        assert awards[1].points == 3000
        assert awards[2].points == 2000
        assert awards[3].points == 1000
        assert awards[4].points == 500
        assert awards[5].points == 500


class TestPayoutCalculatorValidation:
    """Tests for payout validation."""

    def test_validate_valid_structure(self):
        """Test validation passes for valid structure."""
        calc = PayoutCalculator({1: 5000, 2: 3000, 3: 2000})
        assert calc.validate() is True

    def test_validate_empty_structure(self):
        """Test validation fails for empty structure."""
        calc = PayoutCalculator({})
        assert calc.validate() is False

    def test_validate_not_starting_at_1(self):
        """Test validation fails when not starting at rank 1."""
        calc = PayoutCalculator({2: 3000, 3: 2000})
        assert calc.validate() is False

    def test_validate_non_consecutive_ranks(self):
        """Test validation fails for non-consecutive ranks."""
        calc = PayoutCalculator({1: 5000, 2: 3000, 4: 1000})
        assert calc.validate() is False

    def test_validate_negative_points(self):
        """Test validation fails for negative points."""
        calc = PayoutCalculator({1: 5000, 2: -1000})
        assert calc.validate() is False

    def test_validate_increasing_points(self):
        """Test validation fails when lower rank has more points."""
        calc = PayoutCalculator({1: 1000, 2: 5000})  # 2nd > 1st is wrong
        assert calc.validate() is False

    def test_validate_equal_points_allowed(self):
        """Test validation allows equal points for adjacent ranks."""
        calc = PayoutCalculator({1: 5000, 2: 3000, 3: 3000})  # 2nd == 3rd is ok
        assert calc.validate() is True

    def test_validate_single_winner(self):
        """Test validation passes for winner-take-all."""
        calc = PayoutCalculator({1: 10000})
        assert calc.validate() is True

    def test_validate_zero_points_allowed(self):
        """Test validation allows zero points."""
        calc = PayoutCalculator({1: 5000, 2: 3000, 3: 0})
        assert calc.validate() is True


class TestPayoutFixtures:
    """Tests for predefined payout fixtures."""

    def test_standard_27_exists(self):
        """Test standard_27 fixture exists and is valid."""
        calc = PayoutCalculator(PAYOUT_FIXTURES["standard_27"])
        assert calc.validate() is True

    def test_top_heavy_27_exists(self):
        """Test top_heavy_27 fixture exists and is valid."""
        calc = PayoutCalculator(PAYOUT_FIXTURES["top_heavy_27"])
        assert calc.validate() is True

    def test_flat_27_exists(self):
        """Test flat_27 fixture exists and is valid."""
        calc = PayoutCalculator(PAYOUT_FIXTURES["flat_27"])
        assert calc.validate() is True

    def test_all_fixtures_valid(self):
        """Test all fixtures pass validation."""
        for name, structure in PAYOUT_FIXTURES.items():
            calc = PayoutCalculator(structure)
            assert calc.validate() is True, f"Fixture {name} failed validation"
