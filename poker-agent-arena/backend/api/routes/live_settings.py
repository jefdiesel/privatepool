"""Live agent settings routes for real-time slider control during tournaments."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from api.dependencies import CurrentUser, DbSession, RedisServiceDep
from api.schemas.tournament import (
    LiveSettingsResponse,
    UpdateLiveSettingsRequest,
)

router = APIRouter()


@router.get("/{tournament_id}/live-settings", response_model=LiveSettingsResponse)
async def get_live_settings(
    tournament_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> LiveSettingsResponse:
    """
    Get the current live slider settings for a user in a tournament.

    Returns both active settings (currently in use) and pending settings
    (if user has moved sliders but not confirmed).
    """
    wallet = user["wallet"]

    # Check registration and tier
    reg_result = await db.execute(
        text("""
            SELECT r.tier, t.status
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.tournament_id = :tournament_id AND r.wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    reg = reg_result.fetchone()

    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not registered for this tournament",
        )

    if reg.tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live settings are only available for BASIC and PRO tier agents",
        )

    if reg.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Live settings are only available during active tournaments",
        )

    # Get or create live settings record
    settings_result = await db.execute(
        text("""
            SELECT
                active_aggression,
                active_tightness,
                pending_aggression,
                pending_tightness,
                confirmed_aggression,
                confirmed_tightness,
                confirmed_at
            FROM agent_live_settings
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    settings = settings_result.fetchone()

    if not settings:
        # Create default settings if not exist
        await db.execute(
            text("""
                INSERT INTO agent_live_settings (tournament_id, wallet)
                VALUES (:tournament_id, :wallet)
                ON CONFLICT (tournament_id, wallet) DO NOTHING
            """),
            {"tournament_id": str(tournament_id), "wallet": wallet},
        )
        return LiveSettingsResponse(
            tournament_id=str(tournament_id),
            wallet=wallet,
            active_aggression=5,
            active_tightness=5,
        )

    return LiveSettingsResponse(
        tournament_id=str(tournament_id),
        wallet=wallet,
        active_aggression=settings.active_aggression,
        active_tightness=settings.active_tightness,
        pending_aggression=settings.pending_aggression,
        pending_tightness=settings.pending_tightness,
        confirmed_aggression=settings.confirmed_aggression,
        confirmed_tightness=settings.confirmed_tightness,
        confirmed_at=settings.confirmed_at.isoformat() if settings.confirmed_at else None,
    )


@router.put("/{tournament_id}/live-settings", response_model=LiveSettingsResponse)
async def update_live_settings(
    tournament_id: UUID,
    request: UpdateLiveSettingsRequest,
    user: CurrentUser,
    db: DbSession,
    redis: RedisServiceDep,
) -> LiveSettingsResponse:
    """
    Update pending slider values.

    This does NOT apply the changes immediately - the user must call
    the confirm endpoint. Changes take effect at the start of the next hand.
    """
    wallet = user["wallet"]

    # Rate limit: 30 updates per minute (users may drag sliders)
    if not await redis.check_rate_limit(wallet, "live_settings_update", 30, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many update requests. Try again later.",
        )

    # Check registration and tier
    reg_result = await db.execute(
        text("""
            SELECT r.tier, t.status
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.tournament_id = :tournament_id AND r.wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    reg = reg_result.fetchone()

    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not registered for this tournament",
        )

    if reg.tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live settings are only available for BASIC and PRO tier agents",
        )

    if reg.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Live settings are only available during active tournaments",
        )

    # Update pending settings
    await db.execute(
        text("""
            INSERT INTO agent_live_settings (tournament_id, wallet, pending_aggression, pending_tightness, updated_at)
            VALUES (:tournament_id, :wallet, :aggression, :tightness, :now)
            ON CONFLICT (tournament_id, wallet)
            DO UPDATE SET
                pending_aggression = :aggression,
                pending_tightness = :tightness,
                updated_at = :now
        """),
        {
            "tournament_id": str(tournament_id),
            "wallet": wallet,
            "aggression": request.aggression,
            "tightness": request.tightness,
            "now": datetime.utcnow(),
        },
    )

    # Fetch updated settings
    return await get_live_settings(tournament_id, user, db)


@router.post("/{tournament_id}/live-settings/confirm", response_model=LiveSettingsResponse)
async def confirm_live_settings(
    tournament_id: UUID,
    user: CurrentUser,
    db: DbSession,
    redis: RedisServiceDep,
) -> LiveSettingsResponse:
    """
    Confirm pending slider changes.

    Once confirmed, the changes will take effect at the START of the next hand.
    The current hand will complete with the previous settings.
    """
    wallet = user["wallet"]

    # Rate limit: 10 confirms per minute
    if not await redis.check_rate_limit(wallet, "live_settings_confirm", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many confirm requests. Try again later.",
        )

    # Check registration and tier
    reg_result = await db.execute(
        text("""
            SELECT r.tier, t.status
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.tournament_id = :tournament_id AND r.wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    reg = reg_result.fetchone()

    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not registered for this tournament",
        )

    if reg.tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live settings are only available for BASIC and PRO tier agents",
        )

    if reg.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Live settings are only available during active tournaments",
        )

    # Get current settings
    settings_result = await db.execute(
        text("""
            SELECT pending_aggression, pending_tightness
            FROM agent_live_settings
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    settings = settings_result.fetchone()

    if not settings or (settings.pending_aggression is None and settings.pending_tightness is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending changes to confirm",
        )

    # Move pending to confirmed
    now = datetime.utcnow()
    await db.execute(
        text("""
            UPDATE agent_live_settings
            SET
                confirmed_aggression = pending_aggression,
                confirmed_tightness = pending_tightness,
                confirmed_at = :now,
                pending_aggression = NULL,
                pending_tightness = NULL,
                updated_at = :now
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {
            "tournament_id": str(tournament_id),
            "wallet": wallet,
            "now": now,
        },
    )

    # Fetch updated settings
    return await get_live_settings(tournament_id, user, db)
