"""Side pot calculation for poker all-in situations."""
from dataclasses import dataclass

from .betting import PlayerInHand


@dataclass
class SidePot:
    """Represents a pot that specific players are eligible to win."""
    amount: int
    eligible_players: list[str]  # Wallet addresses

    def __repr__(self) -> str:
        return f"SidePot({self.amount}, eligible={len(self.eligible_players)})"


class SidePotCalculator:
    """Calculates main pot and side pots for all-in situations.

    Example:
    Player A: 1000 all-in
    Player B: 2000 all-in
    Player C: 5000 calls

    Results:
    - Main pot: 3000 (A, B, C eligible)
    - Side pot 1: 2000 (B, C eligible)
    """

    def calculate(self, players: list[PlayerInHand]) -> list[SidePot]:
        """Calculate all pots including main pot and side pots.

        Returns list of SidePot objects, main pot first.
        """
        # Get all players who have contributed (have a current_bet > 0)
        contributing_players = [p for p in players if p.current_bet > 0]

        if not contributing_players:
            return []

        # Get all-in amounts sorted, plus the maximum bet
        all_in_levels: list[int] = []
        for p in contributing_players:
            if p.is_all_in:
                all_in_levels.append(p.current_bet)

        # Get unique sorted levels
        all_in_levels = sorted(set(all_in_levels))

        # If no all-ins, just return a single pot
        if not all_in_levels:
            total_pot = sum(p.current_bet for p in contributing_players)
            eligible = [p.wallet for p in contributing_players if p.is_active]
            return [SidePot(amount=total_pot, eligible_players=eligible)]

        pots: list[SidePot] = []
        previous_level = 0

        for level in all_in_levels:
            # Calculate pot for this level
            level_contribution = level - previous_level

            # Count how many players contributed at this level
            eligible_wallets: list[str] = []
            pot_amount = 0

            for p in contributing_players:
                if p.current_bet >= level:
                    # Player contributed at least up to this level
                    pot_amount += level_contribution
                    if p.is_active:
                        eligible_wallets.append(p.wallet)
                elif p.current_bet > previous_level:
                    # Player contributed partially at this level
                    pot_amount += p.current_bet - previous_level
                    if p.is_active:
                        eligible_wallets.append(p.wallet)

            if pot_amount > 0 and eligible_wallets:
                pots.append(SidePot(amount=pot_amount, eligible_players=eligible_wallets))

            previous_level = level

        # Handle remaining bets above the highest all-in
        max_all_in = all_in_levels[-1] if all_in_levels else 0
        remaining_pot = 0
        remaining_eligible: list[str] = []

        for p in contributing_players:
            if p.current_bet > max_all_in:
                remaining_pot += p.current_bet - max_all_in
                if p.is_active:
                    remaining_eligible.append(p.wallet)

        if remaining_pot > 0 and remaining_eligible:
            pots.append(SidePot(amount=remaining_pot, eligible_players=remaining_eligible))

        return pots

    def distribute(
        self,
        pots: list[SidePot],
        hand_rankings: dict[str, int]  # wallet -> rank (lower is better)
    ) -> dict[str, int]:
        """Distribute pots to winners.

        Returns: {wallet: amount_won}

        Rules:
        - Each pot goes to the best eligible hand
        - If tie, split equally
        """
        winnings: dict[str, int] = {}

        for pot in pots:
            if not pot.eligible_players:
                continue

            # Find the best rank among eligible players
            eligible_ranks = {
                wallet: hand_rankings.get(wallet, float('inf'))
                for wallet in pot.eligible_players
                if wallet in hand_rankings
            }

            if not eligible_ranks:
                continue

            best_rank = min(eligible_ranks.values())

            # Find all players with the best rank (ties)
            winners = [
                wallet for wallet, rank in eligible_ranks.items()
                if rank == best_rank
            ]

            # Split pot equally among winners
            share = pot.amount // len(winners)
            remainder = pot.amount % len(winners)

            for i, winner in enumerate(winners):
                amount = share
                # Give remainder chips to first winner(s)
                if i < remainder:
                    amount += 1

                if winner not in winnings:
                    winnings[winner] = 0
                winnings[winner] += amount

        return winnings
