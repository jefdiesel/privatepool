"""Poker deck module with provably fair shuffle.

Implements a 52-card deck with deterministic, verifiable randomness
using blockhash commitment for tournament play.
"""

import hashlib
import random
from dataclasses import dataclass

# Standard poker suits and ranks
SUITS = ["s", "h", "d", "c"]  # spades, hearts, diamonds, clubs
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
CARDS = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]  # 52 cards


@dataclass
class Card:
    """Represents a playing card.

    Attributes:
        rank: Card rank ("2"-"9", "T", "J", "Q", "K", "A")
        suit: Card suit ("s", "h", "d", "c")
    """
    rank: str  # "2"-"9", "T", "J", "Q", "K", "A"
    suit: str  # "s", "h", "d", "c"

    def __post_init__(self):
        """Validate card rank and suit."""
        if self.rank not in RANKS:
            raise ValueError(f"Invalid rank: {self.rank}. Must be one of {RANKS}")
        if self.suit not in SUITS:
            raise ValueError(f"Invalid suit: {self.suit}. Must be one of {SUITS}")

    @classmethod
    def from_string(cls, s: str) -> "Card":
        """Parse card from string like 'As' (Ace of spades).

        Args:
            s: Two-character string representing a card (e.g., "As", "Kh", "2d")

        Returns:
            Card instance

        Raises:
            ValueError: If string format is invalid
        """
        if len(s) != 2:
            raise ValueError(f"Card string must be 2 characters, got: '{s}'")
        rank, suit = s[0], s[1]
        return cls(rank=rank, suit=suit)

    def __str__(self) -> str:
        """Return string representation of the card."""
        return f"{self.rank}{self.suit}"

    def __hash__(self) -> int:
        """Make Card hashable for use in sets and dicts."""
        return hash((self.rank, self.suit))


class Deck:
    """52-card deck with provably fair shuffle.

    Uses blockhash commitment for verifiable randomness.
    seed = SHA256(blockhash + tournament_id + hand_number)

    The shuffle algorithm uses Fisher-Yates to ensure uniform distribution.
    """

    def __init__(self, seed: bytes):
        """Initialize deck with deterministic seed.

        Args:
            seed: Bytes used to seed the PRNG for shuffling
        """
        self.rng = self._create_rng(seed)
        self.cards = self._shuffle()
        self._dealt = 0

    def _create_rng(self, seed: bytes) -> random.Random:
        """Create deterministic PRNG from seed.

        Args:
            seed: Bytes to use as seed

        Returns:
            random.Random instance seeded with the provided bytes
        """
        # Convert bytes to integer for seeding
        seed_int = int.from_bytes(seed, 'big')
        rng = random.Random()
        rng.seed(seed_int)
        return rng

    def _shuffle(self) -> list[str]:
        """Fisher-Yates shuffle with PRNG.

        Returns:
            Shuffled list of card strings
        """
        # Create a copy of the standard deck
        cards = CARDS.copy()

        # Fisher-Yates shuffle: iterate backwards, swap with random earlier position
        for i in range(len(cards) - 1, 0, -1):
            j = self.rng.randint(0, i)
            cards[i], cards[j] = cards[j], cards[i]

        return cards

    def deal(self, count: int = 1) -> list[str]:
        """Deal cards from top of deck.

        Args:
            count: Number of cards to deal (default 1)

        Returns:
            List of dealt card strings

        Raises:
            ValueError: If count exceeds remaining cards
        """
        if count < 0:
            raise ValueError(f"Cannot deal negative cards: {count}")
        if count > self.remaining():
            raise ValueError(
                f"Cannot deal {count} cards, only {self.remaining()} remaining"
            )

        dealt_cards = self.cards[self._dealt:self._dealt + count]
        self._dealt += count
        return dealt_cards

    def remaining(self) -> int:
        """Return number of cards remaining in deck.

        Returns:
            Number of undealt cards
        """
        return len(self.cards) - self._dealt

    @staticmethod
    def generate_seed(blockhash: bytes, tournament_id: str, hand_number: int) -> bytes:
        """Generate deterministic seed for a specific hand.

        Combines blockhash, tournament ID, and hand number using SHA256
        to create a verifiable, deterministic seed.

        seed = SHA256(blockhash + tournament_id + hand_number)

        Args:
            blockhash: Blockchain block hash bytes
            tournament_id: Unique tournament identifier
            hand_number: Sequential hand number within tournament

        Returns:
            32-byte SHA256 hash to use as deck seed
        """
        hasher = hashlib.sha256()
        hasher.update(blockhash)
        hasher.update(tournament_id.encode('utf-8'))
        hasher.update(str(hand_number).encode('utf-8'))
        return hasher.digest()
