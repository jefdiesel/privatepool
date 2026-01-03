"""Poker hand evaluator module.

Evaluates 7-card poker hands (2 hole + 5 community) and returns
the best possible 5-card hand with ranking information.
"""

from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations
from typing import Optional


class HandRank(IntEnum):
    """Poker hand rankings from lowest to highest."""
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


@dataclass
class EvaluatedHand:
    """Represents an evaluated poker hand with ranking and comparison info.

    Attributes:
        rank: The hand type (pair, flush, etc.)
        rank_values: Tuple of card values for tiebreakers (highest first)
        cards_used: The 5 cards making up the best hand
        description: Human-readable description (e.g., "Pair of Kings")
    """
    rank: HandRank
    rank_values: tuple[int, ...]
    cards_used: list[str]
    description: str

    def __lt__(self, other: "EvaluatedHand") -> bool:
        """Compare hands for sorting. Lower rank or values means worse hand."""
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.rank_values < other.rank_values

    def __eq__(self, other: object) -> bool:
        """Check if two hands are equal in strength."""
        if not isinstance(other, EvaluatedHand):
            return NotImplemented
        return self.rank == other.rank and self.rank_values == other.rank_values

    def __le__(self, other: "EvaluatedHand") -> bool:
        return self < other or self == other

    def __gt__(self, other: "EvaluatedHand") -> bool:
        return not self <= other

    def __ge__(self, other: "EvaluatedHand") -> bool:
        return not self < other


class HandEvaluator:
    """Evaluates poker hands.

    Takes 7 cards (2 hole + 5 community) and returns
    the best possible 5-card hand with ranking.
    """

    # Rank values for comparison (2=0, 3=1, ..., A=12)
    RANK_VALUES = {
        "2": 0, "3": 1, "4": 2, "5": 3, "6": 4, "7": 5,
        "8": 6, "9": 7, "T": 8, "J": 9, "Q": 10, "K": 11, "A": 12
    }

    # Reverse mapping for descriptions
    RANK_NAMES = {
        0: "2", 1: "3", 2: "4", 3: "5", 4: "6", 5: "7",
        6: "8", 7: "9", 8: "Ten", 9: "Jack", 10: "Queen", 11: "King", 12: "Ace"
    }

    RANK_NAMES_PLURAL = {
        0: "Twos", 1: "Threes", 2: "Fours", 3: "Fives", 4: "Sixes", 5: "Sevens",
        6: "Eights", 7: "Nines", 8: "Tens", 9: "Jacks", 10: "Queens", 11: "Kings", 12: "Aces"
    }

    def evaluate(self, hole_cards: list[str], community: list[str]) -> EvaluatedHand:
        """Find best 5-card hand from 7 cards.

        Args:
            hole_cards: List of 2 hole cards (e.g., ["As", "Kd"])
            community: List of 5 community cards (e.g., ["Qh", "Jc", "Ts", "2d", "3c"])

        Returns:
            EvaluatedHand with the best possible 5-card hand
        """
        all_cards = hole_cards + community

        if len(all_cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(all_cards)}")

        # Check all possible 5-card combinations
        best_hand: Optional[EvaluatedHand] = None

        for five_cards in combinations(all_cards, 5):
            hand = self._evaluate_five_cards(list(five_cards))
            if best_hand is None or hand > best_hand:
                best_hand = hand

        return best_hand

    def compare(self, hand1: EvaluatedHand, hand2: EvaluatedHand) -> int:
        """Compare two hands.

        Args:
            hand1: First evaluated hand
            hand2: Second evaluated hand

        Returns:
            -1 if hand1 loses, 0 if tie, 1 if hand1 wins
        """
        if hand1 < hand2:
            return -1
        elif hand1 > hand2:
            return 1
        return 0

    def _evaluate_five_cards(self, cards: list[str]) -> EvaluatedHand:
        """Evaluate a specific 5-card hand."""
        is_flush, flush_cards = self._is_flush(cards)
        is_straight, straight_cards, straight_high = self._is_straight(cards)
        rank_counts = self._get_rank_counts(cards)

        # Check for straight flush / royal flush
        if is_flush and is_straight:
            if straight_high == 12:  # Ace high
                return EvaluatedHand(
                    rank=HandRank.ROYAL_FLUSH,
                    rank_values=(12, 11, 10, 9, 8),
                    cards_used=straight_cards,
                    description="Royal Flush"
                )
            else:
                return EvaluatedHand(
                    rank=HandRank.STRAIGHT_FLUSH,
                    rank_values=tuple(sorted([self._get_rank_value(c) for c in straight_cards], reverse=True)) if straight_high != 3 else (3, 2, 1, 0, -1),
                    cards_used=straight_cards,
                    description=f"Straight Flush, {self.RANK_NAMES[straight_high]} high"
                )

        # Check four of a kind
        quads = self._find_n_of_a_kind(rank_counts, 4)
        if quads is not None:
            kicker = self._get_kickers(cards, [quads], 1)
            return EvaluatedHand(
                rank=HandRank.FOUR_OF_A_KIND,
                rank_values=(quads, kicker[0]),
                cards_used=self._build_hand_cards(cards, [(quads, 4)] + [(k, 1) for k in kicker]),
                description=f"Four of a Kind, {self.RANK_NAMES_PLURAL[quads]}"
            )

        # Check full house
        trips = self._find_n_of_a_kind(rank_counts, 3)
        pairs = self._find_all_pairs(rank_counts)

        if trips is not None and pairs:
            pair_rank = max(pairs)
            return EvaluatedHand(
                rank=HandRank.FULL_HOUSE,
                rank_values=(trips, pair_rank),
                cards_used=self._build_hand_cards(cards, [(trips, 3), (pair_rank, 2)]),
                description=f"Full House, {self.RANK_NAMES_PLURAL[trips]} full of {self.RANK_NAMES_PLURAL[pair_rank]}"
            )

        # Check flush (but not straight flush)
        if is_flush:
            sorted_values = tuple(sorted([self._get_rank_value(c) for c in cards], reverse=True))
            return EvaluatedHand(
                rank=HandRank.FLUSH,
                rank_values=sorted_values,
                cards_used=cards,
                description=f"Flush, {self.RANK_NAMES[sorted_values[0]]} high"
            )

        # Check straight (but not straight flush)
        if is_straight:
            if straight_high == 3:  # Wheel: A-2-3-4-5
                rank_values = (3, 2, 1, 0, -1)
            else:
                rank_values = tuple(range(straight_high, straight_high - 5, -1))
            return EvaluatedHand(
                rank=HandRank.STRAIGHT,
                rank_values=rank_values,
                cards_used=straight_cards,
                description=f"Straight, {self.RANK_NAMES[straight_high]} high"
            )

        # Check three of a kind (no full house)
        if trips is not None:
            kickers = self._get_kickers(cards, [trips], 2)
            return EvaluatedHand(
                rank=HandRank.THREE_OF_A_KIND,
                rank_values=(trips,) + tuple(kickers),
                cards_used=self._build_hand_cards(cards, [(trips, 3)] + [(k, 1) for k in kickers]),
                description=f"Three of a Kind, {self.RANK_NAMES_PLURAL[trips]}"
            )

        # Check two pair
        if len(pairs) >= 2:
            top_pairs = sorted(pairs, reverse=True)[:2]
            kicker = self._get_kickers(cards, top_pairs, 1)
            return EvaluatedHand(
                rank=HandRank.TWO_PAIR,
                rank_values=(top_pairs[0], top_pairs[1], kicker[0]),
                cards_used=self._build_hand_cards(cards, [(top_pairs[0], 2), (top_pairs[1], 2), (kicker[0], 1)]),
                description=f"Two Pair, {self.RANK_NAMES_PLURAL[top_pairs[0]]} and {self.RANK_NAMES_PLURAL[top_pairs[1]]}"
            )

        # Check pair
        if len(pairs) == 1:
            pair_rank = pairs[0]
            kickers = self._get_kickers(cards, [pair_rank], 3)
            return EvaluatedHand(
                rank=HandRank.PAIR,
                rank_values=(pair_rank,) + tuple(kickers),
                cards_used=self._build_hand_cards(cards, [(pair_rank, 2)] + [(k, 1) for k in kickers]),
                description=f"Pair of {self.RANK_NAMES_PLURAL[pair_rank]}"
            )

        # High card
        sorted_values = tuple(sorted([self._get_rank_value(c) for c in cards], reverse=True))
        return EvaluatedHand(
            rank=HandRank.HIGH_CARD,
            rank_values=sorted_values,
            cards_used=sorted(cards, key=lambda c: self._get_rank_value(c), reverse=True),
            description=f"{self.RANK_NAMES[sorted_values[0]]} high"
        )

    def _is_flush(self, cards: list[str]) -> tuple[bool, list[str]]:
        """Check if cards form a flush.

        Args:
            cards: List of 5 cards

        Returns:
            Tuple of (is_flush, cards if flush else empty list)
        """
        if len(cards) != 5:
            return False, []

        suits = [card[-1] for card in cards]
        if len(set(suits)) == 1:
            return True, cards
        return False, []

    def _is_straight(self, cards: list[str]) -> tuple[bool, list[str], int]:
        """Check if cards form a straight.

        Args:
            cards: List of 5 cards

        Returns:
            Tuple of (is_straight, cards in order, high card value)
            For wheel (A-2-3-4-5), high card is 3 (the 5)
        """
        if len(cards) != 5:
            return False, [], 0

        values = sorted([self._get_rank_value(c) for c in cards])

        # Check for regular straight
        if values == list(range(values[0], values[0] + 5)):
            sorted_cards = sorted(cards, key=lambda c: self._get_rank_value(c), reverse=True)
            return True, sorted_cards, values[-1]

        # Check for wheel (A-2-3-4-5)
        if values == [0, 1, 2, 3, 12]:  # 2, 3, 4, 5, A
            # Reorder cards with 5 as high
            wheel_order = {12: 0, 0: 1, 1: 2, 2: 3, 3: 4}  # A=0, 2=1, 3=2, 4=3, 5=4
            sorted_cards = sorted(cards, key=lambda c: wheel_order.get(self._get_rank_value(c), 0), reverse=True)
            return True, sorted_cards, 3  # 5 is the high card (value 3)

        return False, [], 0

    def _get_rank_counts(self, cards: list[str]) -> dict[int, int]:
        """Get count of each rank in the cards.

        Args:
            cards: List of cards

        Returns:
            Dictionary mapping rank value to count
        """
        counts: dict[int, int] = {}
        for card in cards:
            rank_value = self._get_rank_value(card)
            counts[rank_value] = counts.get(rank_value, 0) + 1
        return counts

    def _get_rank_value(self, card: str) -> int:
        """Get numeric value for a card's rank."""
        return self.RANK_VALUES[card[0]]

    def _find_n_of_a_kind(self, rank_counts: dict[int, int], n: int) -> Optional[int]:
        """Find the highest rank that appears exactly n times."""
        matches = [rank for rank, count in rank_counts.items() if count == n]
        return max(matches) if matches else None

    def _find_all_pairs(self, rank_counts: dict[int, int]) -> list[int]:
        """Find all ranks that appear exactly twice."""
        return [rank for rank, count in rank_counts.items() if count == 2]

    def _get_kickers(self, cards: list[str], exclude_ranks: list[int], count: int) -> list[int]:
        """Get the highest kicker cards excluding specified ranks.

        Args:
            cards: List of cards
            exclude_ranks: Rank values to exclude
            count: Number of kickers needed

        Returns:
            List of kicker rank values, highest first
        """
        kicker_values = [
            self._get_rank_value(c) for c in cards
            if self._get_rank_value(c) not in exclude_ranks
        ]
        return sorted(kicker_values, reverse=True)[:count]

    def _build_hand_cards(self, cards: list[str], requirements: list[tuple[int, int]]) -> list[str]:
        """Build a list of cards matching the required ranks and counts.

        Args:
            cards: Available cards
            requirements: List of (rank_value, count) tuples

        Returns:
            List of cards matching the requirements
        """
        result: list[str] = []
        used_cards: set[str] = set()

        for rank_value, count in requirements:
            matching = [
                c for c in cards
                if self._get_rank_value(c) == rank_value and c not in used_cards
            ]
            for card in matching[:count]:
                result.append(card)
                used_cards.add(card)

        return result
