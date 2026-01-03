"""Blind structure management for tournament poker.

Key design decision: Antes are paid by the big blind only.
This simplifies the betting logic and matches modern tournament standards.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BlindLevel:
    """Represents a single blind level in a tournament.

    Attributes:
        level: The level number (1-indexed).
        small_blind: Small blind amount.
        big_blind: Big blind amount.
        ante: Ante amount (paid by big blind ONLY).
        duration_minutes: How long this level lasts.
    """
    level: int
    small_blind: int
    big_blind: int
    ante: int  # Paid by big blind ONLY
    duration_minutes: int

    def total_bb_payment(self) -> int:
        """Big blind pays big_blind + ante.

        Returns:
            Total amount the big blind position must pay.
        """
        return self.big_blind + self.ante


class BlindStructure:
    """Manages blind level progression.

    Key feature: Antes are paid by big blind only.

    Attributes:
        levels: List of BlindLevel objects defining the structure.
        current_level_index: Index of current level (0-indexed).
        level_start_time: When the current level started.
    """

    def __init__(self, levels: list[BlindLevel]):
        """Initialize blind structure with given levels.

        Args:
            levels: List of BlindLevel objects in order.
        """
        if not levels:
            raise ValueError("Blind structure must have at least one level")
        self.levels = levels
        self.current_level_index = 0
        self.level_start_time: datetime | None = None

    @property
    def current_level(self) -> BlindLevel:
        """Get the current blind level.

        Returns:
            The current BlindLevel object.
        """
        return self.levels[self.current_level_index]

    def start_level(self) -> None:
        """Start the timer for current level."""
        self.level_start_time = datetime.now()

    def check_level_up(self) -> bool:
        """Check if it's time to advance to next level.

        Automatically advances if time has elapsed.

        Returns:
            True if level advanced, False otherwise.
        """
        if self.level_start_time is None:
            return False

        if self.is_final_level():
            return False

        elapsed = (datetime.now() - self.level_start_time).total_seconds()
        duration_seconds = self.current_level.duration_minutes * 60

        if elapsed >= duration_seconds:
            self.advance_level()
            return True
        return False

    def advance_level(self) -> BlindLevel | None:
        """Advance to next level.

        Returns:
            New BlindLevel if advanced, None if already at max level.
        """
        if self.is_final_level():
            return None

        self.current_level_index += 1
        self.level_start_time = datetime.now()
        return self.current_level

    def time_remaining(self) -> int:
        """Get seconds remaining in current level.

        Returns:
            Seconds remaining, or full duration if not started.
        """
        if self.level_start_time is None:
            return self.current_level.duration_minutes * 60

        elapsed = (datetime.now() - self.level_start_time).total_seconds()
        duration_seconds = self.current_level.duration_minutes * 60
        remaining = duration_seconds - elapsed

        return max(0, int(remaining))

    def is_final_level(self) -> bool:
        """Check if at final blind level.

        Returns:
            True if at the last level, False otherwise.
        """
        return self.current_level_index >= len(self.levels) - 1


# Predefined blind structure templates
BLIND_TEMPLATES: dict[str, list[BlindLevel]] = {
    "turbo": [
        BlindLevel(1, 25, 50, 0, 6),      # No ante
        BlindLevel(2, 50, 100, 0, 6),
        BlindLevel(3, 75, 150, 0, 6),
        BlindLevel(4, 100, 200, 25, 6),   # BB pays 200+25=225
        BlindLevel(5, 150, 300, 25, 6),   # BB pays 300+25=325
        BlindLevel(6, 200, 400, 50, 6),   # BB pays 400+50=450
        BlindLevel(7, 300, 600, 75, 6),
        BlindLevel(8, 400, 800, 100, 6),
        BlindLevel(9, 500, 1000, 100, 6),
        BlindLevel(10, 700, 1400, 175, 6),
        BlindLevel(11, 1000, 2000, 250, 6),
        BlindLevel(12, 1500, 3000, 375, 6),
    ],

    "standard": [
        BlindLevel(1, 25, 50, 0, 10),
        BlindLevel(2, 50, 100, 0, 10),
        BlindLevel(3, 75, 150, 0, 10),
        BlindLevel(4, 100, 200, 25, 10),
        BlindLevel(5, 150, 300, 25, 10),
        BlindLevel(6, 200, 400, 50, 10),
        BlindLevel(7, 300, 600, 75, 10),
        BlindLevel(8, 400, 800, 100, 10),
    ],

    "deep_stack": [
        BlindLevel(1, 25, 50, 0, 15),
        BlindLevel(2, 50, 100, 0, 15),
        BlindLevel(3, 75, 150, 0, 15),
        BlindLevel(4, 100, 200, 0, 15),  # No ante for first 4 levels
        BlindLevel(5, 150, 300, 25, 15),
        BlindLevel(6, 200, 400, 50, 15),
        BlindLevel(7, 300, 600, 75, 15),
        BlindLevel(8, 400, 800, 100, 15),
    ],
}


def get_blind_structure(name: str) -> BlindStructure:
    """Get blind structure by template name.

    Args:
        name: Template name ('turbo', 'standard', or 'deep_stack').

    Returns:
        A new BlindStructure instance with the specified template.

    Raises:
        ValueError: If template name is not recognized.
    """
    if name not in BLIND_TEMPLATES:
        raise ValueError(f"Unknown blind template: {name}")
    # Create a copy of the levels to avoid modifying the template
    return BlindStructure([level for level in BLIND_TEMPLATES[name]])
