"""Payout calculation for tournament poker.

Payout structures are fully customizable by tournament admins.
There is no fixed formula - admins define exactly how many positions
pay and how much each position receives.
"""

from dataclasses import dataclass


@dataclass
class PointsAward:
    """Represents points awarded to a player.

    Attributes:
        wallet: Player's wallet address.
        rank: Final rank (1 = winner).
        points: Points awarded.
    """
    wallet: str
    rank: int  # 1 = winner
    points: int


class PayoutCalculator:
    """Calculates POINTS distribution based on admin-customized payout structure.

    Payout structures are configured per tournament by admin.
    There is NO fixed formula - admins define exactly how many positions
    pay and how much each position receives.

    Attributes:
        payout_structure: Mapping of rank to points awarded.
    """

    def __init__(self, payout_structure: dict[int, int]):
        """Initialize with a payout structure.

        Args:
            payout_structure: {rank: points} mapping
                Example: {1: 5000, 2: 3000, 3: 2000, 4: 1000, 5: 500, 6: 500}
        """
        self.payout_structure = payout_structure

    def calculate(
        self,
        final_rankings: list[tuple[str, int]],  # [(wallet, rank), ...]
    ) -> list[PointsAward]:
        """Calculate POINTS for each player based on final rank.

        Args:
            final_rankings: List of (wallet, rank) tuples.

        Returns:
            List of PointsAward for players who finish in paying positions.
        """
        awards = []

        for wallet, rank in final_rankings:
            if rank in self.payout_structure:
                points = self.payout_structure[rank]
                awards.append(PointsAward(
                    wallet=wallet,
                    rank=rank,
                    points=points,
                ))

        # Sort by rank (ascending) for consistent ordering
        awards.sort(key=lambda a: a.rank)
        return awards

    def total_points(self) -> int:
        """Total POINTS in the payout structure.

        Returns:
            Sum of all points in the payout structure.
        """
        return sum(self.payout_structure.values())

    def paying_positions(self) -> int:
        """Number of positions that receive POINTS.

        Returns:
            Count of positions that receive points.
        """
        return len(self.payout_structure)

    def validate(self) -> bool:
        """Validate payout structure.

        Rules:
        - Ranks must start at 1 and be consecutive
        - Higher ranks should have equal or higher points (lower rank = more points)
        - All values must be non-negative

        Returns:
            True if valid, False otherwise.
        """
        if not self.payout_structure:
            return False

        ranks = sorted(self.payout_structure.keys())

        # Check ranks start at 1
        if ranks[0] != 1:
            return False

        # Check ranks are consecutive
        for i, rank in enumerate(ranks):
            if rank != i + 1:
                return False

        # Check all points are non-negative
        for points in self.payout_structure.values():
            if points < 0:
                return False

        # Check higher rank (lower number) has equal or more points
        prev_points = None
        for rank in ranks:
            points = self.payout_structure[rank]
            if prev_points is not None and points > prev_points:
                return False
            prev_points = points

        return True


# Example payout structures for reference
PAYOUT_FIXTURES: dict[str, dict[int, int]] = {
    "standard_27": {1: 5000, 2: 3000, 3: 2000, 4: 1000, 5: 500, 6: 500},
    "top_heavy_27": {1: 8000, 2: 3000, 3: 1000},
    "flat_27": {1: 2000, 2: 1800, 3: 1600, 4: 1400, 5: 1200, 6: 1000, 7: 800, 8: 600, 9: 600},
}
