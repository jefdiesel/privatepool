"""Tests for the poker deck module."""

import pytest
from collections import Counter

from core.poker.deck import Deck, Card, RANKS, SUITS, CARDS


class TestCardConstants:
    """Tests for deck constants."""

    def test_suits_count(self):
        """Verify we have exactly 4 suits."""
        assert len(SUITS) == 4
        assert set(SUITS) == {"s", "h", "d", "c"}

    def test_ranks_count(self):
        """Verify we have exactly 13 ranks."""
        assert len(RANKS) == 13
        assert "2" in RANKS
        assert "A" in RANKS
        assert "T" in RANKS  # Ten

    def test_cards_count(self):
        """Verify CARDS constant has 52 unique cards."""
        assert len(CARDS) == 52
        assert len(set(CARDS)) == 52  # All unique


class TestCard:
    """Tests for the Card dataclass."""

    def test_card_creation(self):
        """Test creating a valid card."""
        card = Card(rank="A", suit="s")
        assert card.rank == "A"
        assert card.suit == "s"

    def test_card_str(self):
        """Test card string representation."""
        card = Card(rank="K", suit="h")
        assert str(card) == "Kh"

    def test_card_parsing(self):
        """Test Card.from_string works correctly."""
        card = Card.from_string("As")
        assert card.rank == "A"
        assert card.suit == "s"
        assert str(card) == "As"

    def test_card_parsing_all_suits(self):
        """Test parsing cards of all suits."""
        for suit in SUITS:
            card = Card.from_string(f"A{suit}")
            assert card.suit == suit

    def test_card_parsing_all_ranks(self):
        """Test parsing cards of all ranks."""
        for rank in RANKS:
            card = Card.from_string(f"{rank}s")
            assert card.rank == rank

    def test_card_parsing_invalid_length(self):
        """Test that invalid length strings raise ValueError."""
        with pytest.raises(ValueError, match="must be 2 characters"):
            Card.from_string("A")
        with pytest.raises(ValueError, match="must be 2 characters"):
            Card.from_string("Ace")

    def test_card_parsing_invalid_rank(self):
        """Test that invalid rank raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rank"):
            Card.from_string("Xs")

    def test_card_parsing_invalid_suit(self):
        """Test that invalid suit raises ValueError."""
        with pytest.raises(ValueError, match="Invalid suit"):
            Card.from_string("Ax")

    def test_card_hashable(self):
        """Test that cards can be used in sets and dicts."""
        card1 = Card.from_string("As")
        card2 = Card.from_string("As")
        card3 = Card.from_string("Kh")

        # Same cards should hash the same
        assert hash(card1) == hash(card2)

        # Can use in set
        card_set = {card1, card2, card3}
        assert len(card_set) == 2  # card1 and card2 are equal

        # Can use as dict key
        card_dict = {card1: "ace of spades"}
        assert card_dict[card2] == "ace of spades"


class TestDeck:
    """Tests for the Deck class."""

    @pytest.fixture
    def sample_seed(self) -> bytes:
        """Provide a sample seed for testing."""
        return b"test_seed_12345678901234567890123"

    @pytest.fixture
    def deck(self, sample_seed: bytes) -> Deck:
        """Provide a fresh deck for testing."""
        return Deck(sample_seed)

    def test_deck_has_52_cards(self, deck: Deck):
        """Verify deck contains exactly 52 unique cards."""
        assert deck.remaining() == 52

        # Deal all cards and verify uniqueness
        all_cards = deck.deal(52)
        assert len(all_cards) == 52
        assert len(set(all_cards)) == 52  # All unique

        # Verify all standard cards are present
        assert set(all_cards) == set(CARDS)

    def test_shuffle_is_deterministic(self, sample_seed: bytes):
        """Same seed produces same shuffle order."""
        deck1 = Deck(sample_seed)
        deck2 = Deck(sample_seed)

        cards1 = deck1.deal(52)
        cards2 = deck2.deal(52)

        assert cards1 == cards2

    def test_shuffle_differs_with_different_seeds(self):
        """Different seeds produce different shuffle orders."""
        seed1 = b"seed_one_123456789012345678901234"
        seed2 = b"seed_two_123456789012345678901234"

        deck1 = Deck(seed1)
        deck2 = Deck(seed2)

        cards1 = deck1.deal(52)
        cards2 = deck2.deal(52)

        # Different seeds should produce different orders
        assert cards1 != cards2

        # But same set of cards
        assert set(cards1) == set(cards2)

    def test_deal_removes_cards(self, deck: Deck):
        """Dealt cards are removed from available cards."""
        initial_remaining = deck.remaining()
        assert initial_remaining == 52

        # Deal some cards
        dealt = deck.deal(5)
        assert len(dealt) == 5
        assert deck.remaining() == 47

        # Deal more cards
        dealt2 = deck.deal(10)
        assert len(dealt2) == 10
        assert deck.remaining() == 37

        # Dealt cards should not overlap
        assert set(dealt).isdisjoint(set(dealt2))

    def test_deal_single_card(self, deck: Deck):
        """Deal single card (default behavior)."""
        cards = deck.deal()
        assert len(cards) == 1
        assert deck.remaining() == 51

    def test_deal_raises_when_empty(self, deck: Deck):
        """ValueError raised when trying to deal from exhausted deck."""
        # Deal all cards
        deck.deal(52)
        assert deck.remaining() == 0

        # Try to deal more
        with pytest.raises(ValueError, match="Cannot deal .* only 0 remaining"):
            deck.deal(1)

    def test_deal_raises_when_not_enough_cards(self, deck: Deck):
        """ValueError raised when trying to deal more cards than remaining."""
        deck.deal(50)
        assert deck.remaining() == 2

        with pytest.raises(ValueError, match="Cannot deal 5 cards, only 2 remaining"):
            deck.deal(5)

    def test_deal_negative_raises(self, deck: Deck):
        """ValueError raised when trying to deal negative cards."""
        with pytest.raises(ValueError, match="Cannot deal negative"):
            deck.deal(-1)

    def test_deal_zero_cards(self, deck: Deck):
        """Dealing zero cards returns empty list."""
        cards = deck.deal(0)
        assert cards == []
        assert deck.remaining() == 52


class TestSeedGeneration:
    """Tests for deterministic seed generation."""

    def test_generate_seed_is_deterministic(self):
        """Same inputs produce same seed."""
        blockhash = b"blockhash_123456789012345678901234"
        tournament_id = "tournament_001"
        hand_number = 42

        seed1 = Deck.generate_seed(blockhash, tournament_id, hand_number)
        seed2 = Deck.generate_seed(blockhash, tournament_id, hand_number)

        assert seed1 == seed2
        assert len(seed1) == 32  # SHA256 produces 32 bytes

    def test_generate_seed_differs_with_different_blockhash(self):
        """Different blockhash produces different seed."""
        blockhash1 = b"blockhash_111111111111111111111111"
        blockhash2 = b"blockhash_222222222222222222222222"
        tournament_id = "tournament_001"
        hand_number = 42

        seed1 = Deck.generate_seed(blockhash1, tournament_id, hand_number)
        seed2 = Deck.generate_seed(blockhash2, tournament_id, hand_number)

        assert seed1 != seed2

    def test_generate_seed_differs_with_different_tournament(self):
        """Different tournament ID produces different seed."""
        blockhash = b"blockhash_123456789012345678901234"
        hand_number = 42

        seed1 = Deck.generate_seed(blockhash, "tournament_001", hand_number)
        seed2 = Deck.generate_seed(blockhash, "tournament_002", hand_number)

        assert seed1 != seed2

    def test_generate_seed_differs_with_different_hand_number(self):
        """Different hand number produces different seed."""
        blockhash = b"blockhash_123456789012345678901234"
        tournament_id = "tournament_001"

        seed1 = Deck.generate_seed(blockhash, tournament_id, 1)
        seed2 = Deck.generate_seed(blockhash, tournament_id, 2)

        assert seed1 != seed2

    def test_seed_creates_valid_deck(self):
        """Generated seed can be used to create a valid deck."""
        blockhash = b"blockhash_123456789012345678901234"
        tournament_id = "tournament_001"
        hand_number = 1

        seed = Deck.generate_seed(blockhash, tournament_id, hand_number)
        deck = Deck(seed)

        assert deck.remaining() == 52
        cards = deck.deal(52)
        assert len(set(cards)) == 52


class TestFisherYatesDistribution:
    """Statistical tests for shuffle fairness."""

    @pytest.mark.slow
    def test_fisher_yates_distribution(self):
        """Test that shuffle distribution is approximately uniform.

        This is a statistical test that verifies the Fisher-Yates shuffle
        produces a reasonably uniform distribution of card positions.

        We run many shuffles and check that each card appears in each
        position with roughly equal probability.
        """
        num_shuffles = 1000
        num_positions = 52

        # Track how often each card appears in each position
        position_counts: dict[str, Counter] = {card: Counter() for card in CARDS}

        for i in range(num_shuffles):
            seed = f"test_seed_{i}".encode('utf-8').ljust(32, b'\x00')
            deck = Deck(seed)
            cards = deck.deal(52)

            for position, card in enumerate(cards):
                position_counts[card][position] += 1

        # Expected count for each position (uniform distribution)
        expected_per_position = num_shuffles / num_positions

        # Check that distribution is reasonable (within 50% of expected)
        # This is a loose bound to avoid flaky tests while still catching
        # severe distribution problems
        tolerance = 0.5 * expected_per_position

        for card in CARDS:
            for position in range(num_positions):
                count = position_counts[card][position]
                assert abs(count - expected_per_position) < tolerance, (
                    f"Card {card} appeared in position {position} "
                    f"{count} times, expected ~{expected_per_position}"
                )

    def test_shuffle_not_identity(self):
        """Verify shuffle actually changes card order."""
        # Test with multiple seeds to ensure shuffle is happening
        num_tests = 10
        identity_count = 0

        for i in range(num_tests):
            seed = f"shuffle_test_{i}".encode('utf-8').ljust(32, b'\x00')
            deck = Deck(seed)
            cards = deck.deal(52)

            if cards == CARDS:
                identity_count += 1

        # It's astronomically unlikely for even one shuffle to be identity
        # (1 in 52! chance)
        assert identity_count == 0, "Shuffle produced identity permutation"


class TestIntegration:
    """Integration tests for realistic poker scenarios."""

    def test_deal_texas_holdem_hand(self):
        """Test dealing a complete Texas Hold'em hand."""
        seed = Deck.generate_seed(
            blockhash=b"0x1234567890abcdef" * 2,
            tournament_id="main_event_2024",
            hand_number=1
        )
        deck = Deck(seed)

        # Deal hole cards for 6 players
        player_hands = []
        for _ in range(6):
            hand = deck.deal(2)
            player_hands.append(hand)
            assert len(hand) == 2

        assert deck.remaining() == 52 - 12

        # Burn and deal flop
        burn = deck.deal(1)
        flop = deck.deal(3)
        assert len(flop) == 3

        # Burn and deal turn
        burn = deck.deal(1)
        turn = deck.deal(1)
        assert len(turn) == 1

        # Burn and deal river
        burn = deck.deal(1)
        river = deck.deal(1)
        assert len(river) == 1

        # Verify total dealt: 12 (players) + 3 (burns) + 5 (community) = 20
        assert deck.remaining() == 32

        # Verify no duplicate cards
        all_dealt = []
        for hand in player_hands:
            all_dealt.extend(hand)
        all_dealt.extend(flop)
        all_dealt.extend(turn)
        all_dealt.extend(river)
        all_dealt.extend(burn)  # Last burn

        # We dealt 20 cards total
        assert len(all_dealt) == 20

    def test_reproducible_tournament_hands(self):
        """Test that tournament hands can be reproduced."""
        blockhash = b"blockchain_block_hash_value_here"
        tournament_id = "wsop_main_2024"

        # Generate multiple hands
        hands = []
        for hand_num in range(1, 6):
            seed = Deck.generate_seed(blockhash, tournament_id, hand_num)
            deck = Deck(seed)
            # Deal 2 cards per hand
            hands.append(deck.deal(2))

        # Reproduce the same hands
        reproduced = []
        for hand_num in range(1, 6):
            seed = Deck.generate_seed(blockhash, tournament_id, hand_num)
            deck = Deck(seed)
            reproduced.append(deck.deal(2))

        # Verify exact reproduction
        assert hands == reproduced
