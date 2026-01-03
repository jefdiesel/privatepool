"""Tests for the poker hand evaluator module.

Provides 100% coverage of all hand types and edge cases.
"""

import pytest
from core.poker.hand_evaluator import HandRank, EvaluatedHand, HandEvaluator


# Test fixtures for all hand types
HAND_FIXTURES = {
    "royal_flush": {
        "hole": ["As", "Ks"],
        "community": ["Qs", "Js", "Ts", "2d", "3c"],
        "expected_rank": HandRank.ROYAL_FLUSH,
        "expected_description": "Royal Flush",
    },
    "straight_flush": {
        "hole": ["9h", "8h"],
        "community": ["7h", "6h", "5h", "2d", "3c"],
        "expected_rank": HandRank.STRAIGHT_FLUSH,
        "expected_high": 7,  # 9 is high (value 7)
    },
    "straight_flush_low": {
        "hole": ["5d", "4d"],
        "community": ["3d", "2d", "Ad", "Kc", "Qh"],
        "expected_rank": HandRank.STRAIGHT_FLUSH,
        "expected_high": 3,  # Wheel straight flush, 5 is high
    },
    "four_of_a_kind": {
        "hole": ["Ah", "Ad"],
        "community": ["As", "Ac", "Kd", "2h", "3c"],
        "expected_rank": HandRank.FOUR_OF_A_KIND,
        "expected_rank_values": (12, 11),  # Aces with King kicker
    },
    "full_house": {
        "hole": ["Kh", "Kd"],
        "community": ["Ks", "2c", "2d", "7h", "8c"],
        "expected_rank": HandRank.FULL_HOUSE,
        "expected_rank_values": (11, 0),  # Kings full of Twos
    },
    "full_house_trips_matter": {
        "hole": ["Qh", "Qd"],
        "community": ["Qs", "Ac", "Ad", "7h", "8c"],
        "expected_rank": HandRank.FULL_HOUSE,
        "expected_rank_values": (10, 12),  # Queens full of Aces
    },
    "flush": {
        "hole": ["Ah", "Kh"],
        "community": ["9h", "5h", "2h", "Jd", "Tc"],
        "expected_rank": HandRank.FLUSH,
        "expected_high": 12,  # Ace high flush
    },
    "straight": {
        "hole": ["9c", "8d"],
        "community": ["7h", "6s", "5c", "2d", "Kh"],
        "expected_rank": HandRank.STRAIGHT,
        "expected_high": 7,  # 9 high straight
    },
    "wheel_straight": {
        "hole": ["Ah", "2d"],
        "community": ["3s", "4c", "5h", "Kd", "Qc"],
        "expected_rank": HandRank.STRAIGHT,
        "expected_high": 3,  # Wheel: A-2-3-4-5, 5 is high (value 3)
    },
    "broadway_straight": {
        "hole": ["Ah", "Kd"],
        "community": ["Qs", "Jc", "Th", "2d", "3c"],
        "expected_rank": HandRank.STRAIGHT,
        "expected_high": 12,  # Broadway: T-J-Q-K-A, A is high
    },
    "three_of_a_kind": {
        "hole": ["Jh", "Jd"],
        "community": ["Js", "Ac", "Kd", "2h", "3c"],
        "expected_rank": HandRank.THREE_OF_A_KIND,
        "expected_rank_values": (9, 12, 11),  # Jacks with A-K kickers
    },
    "two_pair": {
        "hole": ["Ah", "Ad"],
        "community": ["Ks", "Kc", "Qd", "2h", "3c"],
        "expected_rank": HandRank.TWO_PAIR,
        "expected_rank_values": (12, 11, 10),  # Aces and Kings with Queen kicker
    },
    "pair": {
        "hole": ["Kh", "Kd"],
        "community": ["As", "Qc", "Jd", "2h", "3c"],
        "expected_rank": HandRank.PAIR,
        "expected_rank_values": (11, 12, 10, 9),  # Kings with A-Q-J kickers
    },
    "high_card": {
        "hole": ["Ah", "Kd"],
        "community": ["Qs", "Jc", "9d", "2h", "3c"],
        "expected_rank": HandRank.HIGH_CARD,
        "expected_rank_values": (12, 11, 10, 9, 7),  # A-K-Q-J-9
    },
}


@pytest.fixture
def evaluator():
    """Create a HandEvaluator instance for tests."""
    return HandEvaluator()


class TestHandRank:
    """Tests for HandRank enum."""

    def test_rank_ordering(self):
        """Hand ranks should be properly ordered."""
        assert HandRank.HIGH_CARD < HandRank.PAIR
        assert HandRank.PAIR < HandRank.TWO_PAIR
        assert HandRank.TWO_PAIR < HandRank.THREE_OF_A_KIND
        assert HandRank.THREE_OF_A_KIND < HandRank.STRAIGHT
        assert HandRank.STRAIGHT < HandRank.FLUSH
        assert HandRank.FLUSH < HandRank.FULL_HOUSE
        assert HandRank.FULL_HOUSE < HandRank.FOUR_OF_A_KIND
        assert HandRank.FOUR_OF_A_KIND < HandRank.STRAIGHT_FLUSH
        assert HandRank.STRAIGHT_FLUSH < HandRank.ROYAL_FLUSH

    def test_rank_values(self):
        """Hand ranks should have correct integer values."""
        assert HandRank.HIGH_CARD == 1
        assert HandRank.ROYAL_FLUSH == 10


class TestEvaluatedHand:
    """Tests for EvaluatedHand dataclass."""

    def test_comparison_different_ranks(self):
        """Higher rank should win regardless of rank_values."""
        pair = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(12, 11, 10, 9),
            cards_used=["Ah", "Ad", "Ks", "Qc", "Jd"],
            description="Pair of Aces"
        )
        two_pair = EvaluatedHand(
            rank=HandRank.TWO_PAIR,
            rank_values=(0, 1, 2),
            cards_used=["2h", "2d", "3s", "3c", "4d"],
            description="Two Pair, Threes and Twos"
        )
        assert pair < two_pair
        assert two_pair > pair

    def test_comparison_same_rank_different_values(self):
        """Same rank should compare by rank_values."""
        pair_kings = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Kh", "Kd", "As", "Qc", "Jd"],
            description="Pair of Kings"
        )
        pair_queens = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(10, 12, 11, 9),
            cards_used=["Qh", "Qd", "As", "Kc", "Jd"],
            description="Pair of Queens"
        )
        assert pair_queens < pair_kings
        assert pair_kings > pair_queens

    def test_comparison_equal_hands(self):
        """Equal hands should be equal."""
        hand1 = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Kh", "Kd", "As", "Qc", "Jd"],
            description="Pair of Kings"
        )
        hand2 = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Ks", "Kc", "Ah", "Qd", "Js"],
            description="Pair of Kings"
        )
        assert hand1 == hand2
        assert not hand1 < hand2
        assert not hand1 > hand2

    def test_le_comparison(self):
        """Less than or equal comparison."""
        hand1 = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Kh", "Kd", "As", "Qc", "Jd"],
            description="Pair of Kings"
        )
        hand2 = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Ks", "Kc", "Ah", "Qd", "Js"],
            description="Pair of Kings"
        )
        hand3 = EvaluatedHand(
            rank=HandRank.TWO_PAIR,
            rank_values=(0, 1, 2),
            cards_used=["2h", "2d", "3s", "3c", "4d"],
            description="Two Pair"
        )
        assert hand1 <= hand2
        assert hand1 <= hand3
        assert not hand3 <= hand1

    def test_ge_comparison(self):
        """Greater than or equal comparison."""
        hand1 = EvaluatedHand(
            rank=HandRank.TWO_PAIR,
            rank_values=(12, 11, 10),
            cards_used=["Ah", "Ad", "Ks", "Kc", "Qd"],
            description="Two Pair"
        )
        hand2 = EvaluatedHand(
            rank=HandRank.TWO_PAIR,
            rank_values=(12, 11, 10),
            cards_used=["As", "Ac", "Kh", "Kd", "Qs"],
            description="Two Pair"
        )
        hand3 = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(12, 11, 10, 9),
            cards_used=["Ah", "Ad", "Ks", "Qc", "Jd"],
            description="Pair"
        )
        assert hand1 >= hand2
        assert hand1 >= hand3
        assert not hand3 >= hand1

    def test_eq_with_non_evaluated_hand(self):
        """Equality with non-EvaluatedHand should return NotImplemented."""
        hand = EvaluatedHand(
            rank=HandRank.PAIR,
            rank_values=(11, 12, 10, 9),
            cards_used=["Kh", "Kd", "As", "Qc", "Jd"],
            description="Pair of Kings"
        )
        assert hand.__eq__("not a hand") == NotImplemented
        assert hand.__eq__(123) == NotImplemented


class TestRoyalFlush:
    """Tests for Royal Flush detection."""

    def test_royal_flush(self, evaluator):
        """Should detect royal flush."""
        fixture = HAND_FIXTURES["royal_flush"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.ROYAL_FLUSH
        assert result.description == "Royal Flush"
        assert result.rank_values == (12, 11, 10, 9, 8)

    def test_royal_flush_mixed_community(self, evaluator):
        """Royal flush with suited cards spread across hole and community."""
        result = evaluator.evaluate(
            ["Ad", "Td"],
            ["Kd", "Qd", "Jd", "2c", "3h"]
        )
        assert result.rank == HandRank.ROYAL_FLUSH


class TestStraightFlush:
    """Tests for Straight Flush detection."""

    def test_straight_flush(self, evaluator):
        """Should detect straight flush."""
        fixture = HAND_FIXTURES["straight_flush"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.STRAIGHT_FLUSH
        assert "Straight Flush" in result.description

    def test_straight_flush_wheel(self, evaluator):
        """Wheel straight flush (A-2-3-4-5 suited)."""
        fixture = HAND_FIXTURES["straight_flush_low"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.STRAIGHT_FLUSH
        # 5 is high in wheel, so rank_values should reflect that
        assert result.rank_values == (3, 2, 1, 0, -1)


class TestFourOfAKind:
    """Tests for Four of a Kind detection."""

    def test_four_of_a_kind(self, evaluator):
        """Should detect four of a kind."""
        fixture = HAND_FIXTURES["four_of_a_kind"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.FOUR_OF_A_KIND
        assert result.rank_values == fixture["expected_rank_values"]
        assert "Four of a Kind" in result.description

    def test_four_of_a_kind_kicker_matters(self, evaluator):
        """Kicker should matter for four of a kind comparison."""
        # Quads with Ace kicker
        hand1 = evaluator.evaluate(["Kh", "Kd"], ["Ks", "Kc", "Ad", "2h", "3c"])
        # Quads with Queen kicker
        hand2 = evaluator.evaluate(["Kh", "Kd"], ["Ks", "Kc", "Qd", "2h", "3c"])

        assert hand1 > hand2


class TestFullHouse:
    """Tests for Full House detection."""

    def test_full_house(self, evaluator):
        """Should detect full house."""
        fixture = HAND_FIXTURES["full_house"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.FULL_HOUSE
        assert result.rank_values == fixture["expected_rank_values"]
        assert "Full House" in result.description

    def test_full_house_trips_beat_pair(self, evaluator):
        """Trips rank matters more than pair rank in full house."""
        # Kings full of Twos
        hand1 = evaluator.evaluate(["Kh", "Kd"], ["Ks", "2c", "2d", "7h", "8c"])
        # Queens full of Aces
        hand2 = evaluator.evaluate(["Qh", "Qd"], ["Qs", "Ac", "Ad", "7h", "8c"])

        assert hand1 > hand2  # Kings full beats Queens full


class TestFlush:
    """Tests for Flush detection."""

    def test_flush(self, evaluator):
        """Should detect flush."""
        fixture = HAND_FIXTURES["flush"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.FLUSH
        assert "Flush" in result.description

    def test_flush_tiebreaker(self, evaluator):
        """Flush tiebreaker should compare cards in order."""
        # A-K-Q-J-9 flush
        hand1 = evaluator.evaluate(["Ah", "Kh"], ["Qh", "Jh", "9h", "2c", "3d"])
        # A-K-Q-J-8 flush
        hand2 = evaluator.evaluate(["Ah", "Kh"], ["Qh", "Jh", "8h", "2c", "3d"])

        assert hand1 > hand2


class TestStraight:
    """Tests for Straight detection."""

    def test_straight(self, evaluator):
        """Should detect straight."""
        fixture = HAND_FIXTURES["straight"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.STRAIGHT
        assert "Straight" in result.description

    def test_wheel_straight(self, evaluator):
        """Wheel straight (A-2-3-4-5) should have 5 as high card."""
        fixture = HAND_FIXTURES["wheel_straight"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.STRAIGHT
        # 5 is high (value 3), so rank_values should be (3, 2, 1, 0, -1)
        assert result.rank_values == (3, 2, 1, 0, -1)

    def test_broadway_straight(self, evaluator):
        """Broadway straight (T-J-Q-K-A) should have A as high card."""
        fixture = HAND_FIXTURES["broadway_straight"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.STRAIGHT
        assert result.rank_values == (12, 11, 10, 9, 8)

    def test_wheel_loses_to_regular_straight(self, evaluator):
        """Wheel should lose to any other straight."""
        wheel = evaluator.evaluate(["Ah", "2d"], ["3s", "4c", "5h", "Kd", "Qc"])
        six_high = evaluator.evaluate(["6h", "2d"], ["3s", "4c", "5h", "Kd", "Qc"])

        assert wheel < six_high


class TestThreeOfAKind:
    """Tests for Three of a Kind detection."""

    def test_three_of_a_kind(self, evaluator):
        """Should detect three of a kind."""
        fixture = HAND_FIXTURES["three_of_a_kind"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.THREE_OF_A_KIND
        assert result.rank_values == fixture["expected_rank_values"]
        assert "Three of a Kind" in result.description

    def test_trips_kicker_matters(self, evaluator):
        """Kickers should matter for trips comparison."""
        # Trip Jacks with A-K
        hand1 = evaluator.evaluate(["Jh", "Jd"], ["Js", "Ac", "Kd", "2h", "3c"])
        # Trip Jacks with A-Q
        hand2 = evaluator.evaluate(["Jh", "Jd"], ["Js", "Ac", "Qd", "2h", "3c"])

        assert hand1 > hand2


class TestTwoPair:
    """Tests for Two Pair detection."""

    def test_two_pair(self, evaluator):
        """Should detect two pair."""
        fixture = HAND_FIXTURES["two_pair"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.TWO_PAIR
        assert result.rank_values == fixture["expected_rank_values"]
        assert "Two Pair" in result.description

    def test_two_pair_high_pair_matters(self, evaluator):
        """Higher pair should win in two pair comparison."""
        # Aces and Kings
        hand1 = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Kc", "Qd", "2h", "3c"])
        # Aces and Queens
        hand2 = evaluator.evaluate(["Ah", "Ad"], ["Qs", "Qc", "Kd", "2h", "3c"])

        assert hand1 > hand2

    def test_two_pair_kicker_matters(self, evaluator):
        """Kicker should matter when both pairs are equal."""
        # Aces and Kings with Q kicker
        hand1 = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Kc", "Qd", "2h", "3c"])
        # Aces and Kings with J kicker
        hand2 = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Kc", "Jd", "2h", "3c"])

        assert hand1 > hand2


class TestPair:
    """Tests for Pair detection."""

    def test_pair(self, evaluator):
        """Should detect pair."""
        fixture = HAND_FIXTURES["pair"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.PAIR
        assert result.rank_values == fixture["expected_rank_values"]
        assert "Pair" in result.description

    def test_pair_rank_matters(self, evaluator):
        """Higher pair should win."""
        # Pair of Kings
        hand1 = evaluator.evaluate(["Kh", "Kd"], ["As", "Qc", "Jd", "2h", "3c"])
        # Pair of Queens
        hand2 = evaluator.evaluate(["Qh", "Qd"], ["As", "Kc", "Jd", "2h", "3c"])

        assert hand1 > hand2


class TestHighCard:
    """Tests for High Card detection."""

    def test_high_card(self, evaluator):
        """Should detect high card."""
        fixture = HAND_FIXTURES["high_card"]
        result = evaluator.evaluate(fixture["hole"], fixture["community"])

        assert result.rank == HandRank.HIGH_CARD
        assert result.rank_values == fixture["expected_rank_values"]

    def test_high_card_tiebreaker(self, evaluator):
        """High card hands should compare all cards."""
        # A-K-Q-J-9
        hand1 = evaluator.evaluate(["Ah", "Kd"], ["Qs", "Jc", "9d", "2h", "3c"])
        # A-K-Q-J-8
        hand2 = evaluator.evaluate(["Ah", "Kd"], ["Qs", "Jc", "8d", "2h", "3c"])

        assert hand1 > hand2


class TestTiebreakers:
    """Tests for tiebreaker scenarios."""

    def test_tiebreaker_same_hand_type(self, evaluator):
        """Same hand type should compare by rank values."""
        # Pair of Kings
        hand1 = evaluator.evaluate(["Kh", "Kd"], ["As", "Qc", "Jd", "2h", "3c"])
        # Pair of Queens
        hand2 = evaluator.evaluate(["Qh", "Qd"], ["As", "Kc", "Jd", "2h", "3c"])

        assert evaluator.compare(hand1, hand2) == 1
        assert evaluator.compare(hand2, hand1) == -1

    def test_split_pot_identical_hands(self, evaluator):
        """Identical hands should tie."""
        # Both players have same flush on board
        hand1 = evaluator.evaluate(["2h", "3h"], ["As", "Ks", "Qs", "Js", "9s"])
        hand2 = evaluator.evaluate(["4h", "5h"], ["As", "Ks", "Qs", "Js", "9s"])

        assert evaluator.compare(hand1, hand2) == 0
        assert hand1 == hand2

    def test_kicker_matters_with_pair(self, evaluator):
        """Kicker should determine winner when pairs are equal."""
        # Pair of Aces with King kicker
        hand1 = evaluator.evaluate(["Ah", "Kd"], ["As", "Qc", "Jd", "2h", "3c"])
        # Pair of Aces with Queen kicker
        hand2 = evaluator.evaluate(["Ah", "Qd"], ["As", "Jc", "Td", "2h", "3c"])

        assert hand1 > hand2
        assert evaluator.compare(hand1, hand2) == 1


class TestBest5From7:
    """Tests for selecting best 5 cards from 7."""

    def test_best_5_from_7_ignores_unused(self, evaluator):
        """Unused cards should not affect hand ranking."""
        # Pair of Aces, best hand ignores low cards
        result = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Qc", "Jd", "2h", "3c"])

        assert result.rank == HandRank.PAIR
        assert len(result.cards_used) == 5
        # The 2 and 3 shouldn't be in the final hand
        assert "2h" not in result.cards_used
        assert "3c" not in result.cards_used

    def test_best_5_selects_optimal_combination(self, evaluator):
        """Should find the best possible 5-card hand."""
        # Has potential for both straight and flush, but straight is better here
        result = evaluator.evaluate(["9h", "8h"], ["7h", "6d", "5h", "4c", "3h"])

        # Should find the straight (9-8-7-6-5)
        assert result.rank == HandRank.STRAIGHT

    def test_multiple_pairs_selects_best_two(self, evaluator):
        """With 3 pairs available, should select the best two."""
        # Three pairs: AA, KK, QQ - should use AA and KK
        result = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Kc", "Qs", "Qc", "2d"])

        assert result.rank == HandRank.TWO_PAIR
        assert result.rank_values[0] == 12  # Aces
        assert result.rank_values[1] == 11  # Kings


class TestCompareMethod:
    """Tests for the compare method."""

    def test_compare_hand1_wins(self, evaluator):
        """compare should return 1 when hand1 wins."""
        hand1 = evaluator.evaluate(["Ah", "Ad"], ["As", "Ac", "Kd", "2h", "3c"])
        hand2 = evaluator.evaluate(["Kh", "Kd"], ["Ks", "Kc", "Ad", "2h", "3c"])

        assert evaluator.compare(hand1, hand2) == 1

    def test_compare_hand2_wins(self, evaluator):
        """compare should return -1 when hand2 wins."""
        hand1 = evaluator.evaluate(["Kh", "Kd"], ["Ks", "Kc", "Ad", "2h", "3c"])
        hand2 = evaluator.evaluate(["Ah", "Ad"], ["As", "Ac", "Kd", "2h", "3c"])

        assert evaluator.compare(hand1, hand2) == -1

    def test_compare_tie(self, evaluator):
        """compare should return 0 for tie."""
        # Same board, different hole cards that don't improve hand
        hand1 = evaluator.evaluate(["2h", "3d"], ["As", "Ks", "Qs", "Js", "9s"])
        hand2 = evaluator.evaluate(["4h", "5d"], ["As", "Ks", "Qs", "Js", "9s"])

        assert evaluator.compare(hand1, hand2) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_minimum_cards(self, evaluator):
        """Should work with exactly 5 cards."""
        result = evaluator.evaluate(["Ah", "Kd"], ["Qs", "Jc", "Td"])

        assert result.rank == HandRank.STRAIGHT

    def test_insufficient_cards_raises_error(self, evaluator):
        """Should raise error with fewer than 5 cards."""
        with pytest.raises(ValueError):
            evaluator.evaluate(["Ah", "Kd"], ["Qs", "Jc"])

    def test_all_same_rank(self, evaluator):
        """Should handle multiple cards of same rank correctly."""
        # This shouldn't happen in real poker, but test anyway
        result = evaluator.evaluate(["Ah", "Ad"], ["As", "Ac", "Kd", "Kh", "Ks"])

        assert result.rank == HandRank.FOUR_OF_A_KIND


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_is_flush_true(self, evaluator):
        """_is_flush should detect flush."""
        cards = ["Ah", "Kh", "Qh", "Jh", "9h"]
        is_flush, flush_cards = evaluator._is_flush(cards)

        assert is_flush is True
        assert flush_cards == cards

    def test_is_flush_false(self, evaluator):
        """_is_flush should detect non-flush."""
        cards = ["Ah", "Kh", "Qh", "Jh", "9s"]
        is_flush, flush_cards = evaluator._is_flush(cards)

        assert is_flush is False
        assert flush_cards == []

    def test_is_flush_wrong_count(self, evaluator):
        """_is_flush should return False for non-5 cards."""
        cards = ["Ah", "Kh", "Qh", "Jh"]
        is_flush, flush_cards = evaluator._is_flush(cards)

        assert is_flush is False

    def test_is_straight_true(self, evaluator):
        """_is_straight should detect straight."""
        cards = ["9h", "8d", "7s", "6c", "5h"]
        is_straight, straight_cards, high = evaluator._is_straight(cards)

        assert is_straight is True
        assert high == 7  # 9 high

    def test_is_straight_false(self, evaluator):
        """_is_straight should detect non-straight."""
        cards = ["Ah", "Kd", "Qs", "Jc", "9h"]
        is_straight, straight_cards, high = evaluator._is_straight(cards)

        assert is_straight is False

    def test_is_straight_wheel(self, evaluator):
        """_is_straight should detect wheel with 5 as high."""
        cards = ["Ah", "2d", "3s", "4c", "5h"]
        is_straight, straight_cards, high = evaluator._is_straight(cards)

        assert is_straight is True
        assert high == 3  # 5 is high (value 3)

    def test_is_straight_wrong_count(self, evaluator):
        """_is_straight should return False for non-5 cards."""
        cards = ["9h", "8d", "7s", "6c"]
        is_straight, straight_cards, high = evaluator._is_straight(cards)

        assert is_straight is False

    def test_get_rank_counts(self, evaluator):
        """_get_rank_counts should count ranks correctly."""
        cards = ["Ah", "Ad", "As", "Kc", "Kd"]
        counts = evaluator._get_rank_counts(cards)

        assert counts[12] == 3  # Three Aces
        assert counts[11] == 2  # Two Kings

    def test_get_rank_value(self, evaluator):
        """_get_rank_value should return correct values."""
        assert evaluator._get_rank_value("2h") == 0
        assert evaluator._get_rank_value("Ah") == 12
        assert evaluator._get_rank_value("Td") == 8

    def test_find_n_of_a_kind(self, evaluator):
        """_find_n_of_a_kind should find correct rank."""
        counts = {12: 3, 11: 2}

        assert evaluator._find_n_of_a_kind(counts, 3) == 12
        assert evaluator._find_n_of_a_kind(counts, 2) == 11
        assert evaluator._find_n_of_a_kind(counts, 4) is None

    def test_find_all_pairs(self, evaluator):
        """_find_all_pairs should find all pairs."""
        counts = {12: 2, 11: 2, 10: 1}

        pairs = evaluator._find_all_pairs(counts)
        assert 12 in pairs
        assert 11 in pairs
        assert 10 not in pairs

    def test_get_kickers(self, evaluator):
        """_get_kickers should return correct kickers."""
        cards = ["Ah", "Kd", "Qs", "Kc", "Jh"]
        kickers = evaluator._get_kickers(cards, [11], 3)  # Exclude Kings

        assert kickers == [12, 10, 9]  # A, Q, J

    def test_build_hand_cards(self, evaluator):
        """_build_hand_cards should build correct hand."""
        cards = ["Ah", "Ad", "Ks", "Kc", "Qd"]
        requirements = [(12, 2), (11, 2), (10, 1)]  # 2 Aces, 2 Kings, 1 Queen

        result = evaluator._build_hand_cards(cards, requirements)

        assert len(result) == 5
        # Check we got the right cards
        ace_count = sum(1 for c in result if c[0] == "A")
        king_count = sum(1 for c in result if c[0] == "K")
        queen_count = sum(1 for c in result if c[0] == "Q")

        assert ace_count == 2
        assert king_count == 2
        assert queen_count == 1


class TestDescriptions:
    """Tests for human-readable descriptions."""

    def test_royal_flush_description(self, evaluator):
        result = evaluator.evaluate(["As", "Ks"], ["Qs", "Js", "Ts", "2d", "3c"])
        assert result.description == "Royal Flush"

    def test_straight_flush_description(self, evaluator):
        result = evaluator.evaluate(["9h", "8h"], ["7h", "6h", "5h", "2d", "3c"])
        assert "Straight Flush" in result.description

    def test_four_of_a_kind_description(self, evaluator):
        result = evaluator.evaluate(["Ah", "Ad"], ["As", "Ac", "Kd", "2h", "3c"])
        assert "Four of a Kind" in result.description
        assert "Aces" in result.description

    def test_full_house_description(self, evaluator):
        result = evaluator.evaluate(["Kh", "Kd"], ["Ks", "2c", "2d", "7h", "8c"])
        assert "Full House" in result.description
        assert "Kings" in result.description
        assert "Twos" in result.description

    def test_flush_description(self, evaluator):
        result = evaluator.evaluate(["Ah", "Kh"], ["Qh", "Jh", "9h", "2c", "3d"])
        assert "Flush" in result.description
        assert "Ace" in result.description

    def test_straight_description(self, evaluator):
        result = evaluator.evaluate(["9c", "8d"], ["7h", "6s", "5c", "2d", "Kh"])
        assert "Straight" in result.description

    def test_three_of_a_kind_description(self, evaluator):
        result = evaluator.evaluate(["Jh", "Jd"], ["Js", "Ac", "Kd", "2h", "3c"])
        assert "Three of a Kind" in result.description
        assert "Jacks" in result.description

    def test_two_pair_description(self, evaluator):
        result = evaluator.evaluate(["Ah", "Ad"], ["Ks", "Kc", "Qd", "2h", "3c"])
        assert "Two Pair" in result.description
        assert "Aces" in result.description
        assert "Kings" in result.description

    def test_pair_description(self, evaluator):
        result = evaluator.evaluate(["Kh", "Kd"], ["As", "Qc", "Jd", "2h", "3c"])
        assert "Pair" in result.description
        assert "Kings" in result.description

    def test_high_card_description(self, evaluator):
        result = evaluator.evaluate(["Ah", "Kd"], ["Qs", "Jc", "9d", "2h", "3c"])
        assert "Ace" in result.description
        assert "high" in result.description
