"""Live settings service for real-time slider control during tournaments."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class LiveSettings:
    """Live slider settings for an agent."""

    aggression: int = 5
    tightness: int = 5


async def get_live_settings(
    db: AsyncSession,
    tournament_id: str,
    wallet: str,
) -> LiveSettings:
    """
    Get the current active live settings for a player in a tournament.

    Returns default settings (5, 5) if:
    - Player is FREE tier (no live settings record)
    - Player hasn't been assigned settings yet

    Args:
        db: Database session
        tournament_id: Tournament ID
        wallet: Player wallet address

    Returns:
        LiveSettings with current active values
    """
    result = await db.execute(
        text("""
            SELECT active_aggression, active_tightness
            FROM agent_live_settings
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {"tournament_id": tournament_id, "wallet": wallet},
    )
    row = result.fetchone()

    if row:
        return LiveSettings(
            aggression=row.active_aggression,
            tightness=row.active_tightness,
        )

    # No live settings record - return defaults (FREE tier or not initialized)
    return LiveSettings()


async def apply_confirmed_settings(
    db: AsyncSession,
    tournament_id: str,
) -> dict[str, tuple[int, int]]:
    """
    Apply all confirmed settings at the start of a new hand.

    This should be called at the START of each new hand, before cards are dealt.
    It finds all players with confirmed settings waiting to be applied,
    copies them to active settings, and clears the confirmed state.

    Args:
        db: Database session
        tournament_id: Tournament ID

    Returns:
        Dict of wallet -> (aggression, tightness) for settings that were applied
    """
    # Find all players with confirmed settings
    result = await db.execute(
        text("""
            SELECT wallet, confirmed_aggression, confirmed_tightness, active_aggression, active_tightness
            FROM agent_live_settings
            WHERE tournament_id = :tournament_id
              AND (confirmed_aggression IS NOT NULL OR confirmed_tightness IS NOT NULL)
        """),
        {"tournament_id": tournament_id},
    )
    rows = result.fetchall()

    if not rows:
        return {}

    applied_settings: dict[str, tuple[int, int]] = {}

    for row in rows:
        # Calculate new active values
        new_aggression = row.confirmed_aggression if row.confirmed_aggression is not None else row.active_aggression
        new_tightness = row.confirmed_tightness if row.confirmed_tightness is not None else row.active_tightness

        # Apply confirmed settings to active settings
        await db.execute(
            text("""
                UPDATE agent_live_settings
                SET
                    active_aggression = COALESCE(confirmed_aggression, active_aggression),
                    active_tightness = COALESCE(confirmed_tightness, active_tightness),
                    confirmed_aggression = NULL,
                    confirmed_tightness = NULL,
                    confirmed_at = NULL,
                    updated_at = NOW()
                WHERE tournament_id = :tournament_id AND wallet = :wallet
            """),
            {"tournament_id": tournament_id, "wallet": row.wallet},
        )

        applied_settings[row.wallet] = (new_aggression, new_tightness)

        logger.info(
            f"Applied live settings for {row.wallet[:8]}...: "
            f"aggression={new_aggression}, tightness={new_tightness}"
        )

    return applied_settings


async def get_all_live_settings(
    db: AsyncSession,
    tournament_id: str,
) -> dict[str, tuple[int, int]]:
    """
    Get all live settings for a tournament.

    Args:
        db: Database session
        tournament_id: Tournament ID

    Returns:
        Dict of wallet -> (aggression, tightness) for all players with live settings
    """
    result = await db.execute(
        text("""
            SELECT wallet, active_aggression, active_tightness
            FROM agent_live_settings
            WHERE tournament_id = :tournament_id
        """),
        {"tournament_id": tournament_id},
    )
    rows = result.fetchall()

    return {
        row.wallet: (row.active_aggression, row.active_tightness)
        for row in rows
    }


async def get_player_tier(
    db: AsyncSession,
    tournament_id: str,
    wallet: str,
) -> Optional[str]:
    """
    Get a player's tier for a tournament.

    Args:
        db: Database session
        tournament_id: Tournament ID
        wallet: Player wallet address

    Returns:
        Tier string ('free', 'basic', 'pro') or None if not registered
    """
    result = await db.execute(
        text("""
            SELECT tier
            FROM registrations
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {"tournament_id": tournament_id, "wallet": wallet},
    )
    row = result.fetchone()
    return row.tier if row else None
