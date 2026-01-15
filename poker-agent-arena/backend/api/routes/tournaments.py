"""Tournament routes."""

import hashlib
import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, text

from api.dependencies import CurrentUser, DbSession, OptionalUser, RedisServiceDep
from api.schemas.tournament import (
    BlindLevel,
    BlindStructure,
    PayoutEntry,
    PlayerResult,
    RegistrationRequest,
    RegistrationResponse,
    TournamentDetail,
    TournamentListItem,
    TournamentResultsResponse,
)
from config import get_settings

router = APIRouter()


@router.get("", response_model=list[TournamentListItem])
async def list_tournaments(
    db: DbSession,
    status_filter: Literal["upcoming", "live", "completed", "all"] = Query(
        "all", alias="status"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[TournamentListItem]:
    """
    List tournaments with optional status filter.

    - upcoming: registration or created status, starts_at in future
    - live: in_progress status
    - completed: completed status
    - all: all tournaments
    """
    # Build status condition
    if status_filter == "upcoming":
        status_condition = "t.status IN ('created', 'registration')"
    elif status_filter == "live":
        status_condition = "t.status = 'in_progress'"
    elif status_filter == "completed":
        status_condition = "t.status = 'completed'"
    else:
        status_condition = "1=1"

    result = await db.execute(
        text(f"""
            SELECT
                t.id,
                t.on_chain_id,
                t.status,
                t.max_players,
                t.starting_stack,
                t.starts_at,
                t.blind_structure,
                t.payout_structure,
                COUNT(r.id) as registered_players
            FROM tournaments t
            LEFT JOIN registrations r ON t.id = r.tournament_id
            WHERE {status_condition}
            GROUP BY t.id
            ORDER BY
                CASE
                    WHEN t.status = 'in_progress' THEN 0
                    WHEN t.status IN ('created', 'registration') THEN 1
                    ELSE 2
                END,
                t.starts_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {"limit": limit, "offset": offset},
    )

    rows = result.fetchall()
    tournaments = []

    for row in rows:
        blind_structure = row.blind_structure
        payout_structure = row.payout_structure

        # Calculate total points prize
        total_points = sum(p.get("points", 0) for p in payout_structure)

        tournaments.append(
            TournamentListItem(
                id=row.id,
                on_chain_id=row.on_chain_id,
                status=row.status,
                max_players=row.max_players,
                registered_players=row.registered_players,
                starting_stack=row.starting_stack,
                starts_at=row.starts_at,
                blind_structure_name=blind_structure.get("name", "custom"),
                total_points_prize=total_points,
            )
        )

    return tournaments


@router.get("/{tournament_id}", response_model=TournamentDetail)
async def get_tournament(
    tournament_id: UUID,
    db: DbSession,
    user: OptionalUser = None,
) -> TournamentDetail:
    """Get full tournament details."""
    result = await db.execute(
        text("""
            SELECT
                t.*,
                COUNT(r.id) as registered_players
            FROM tournaments t
            LEFT JOIN registrations r ON t.id = r.tournament_id
            WHERE t.id = :id
            GROUP BY t.id
        """),
        {"id": str(tournament_id)},
    )

    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Parse blind structure
    blind_data = row.blind_structure
    blind_structure = BlindStructure(
        name=blind_data.get("name", "custom"),
        levels=[BlindLevel(**level) for level in blind_data.get("levels", [])],
    )

    # Parse payout structure
    payout_structure = [PayoutEntry(**p) for p in row.payout_structure]

    # Check user registration
    user_registered = False
    user_tier = None
    user_agent_name = None

    if user:
        reg_result = await db.execute(
            text("""
                SELECT tier, agent_name
                FROM registrations
                WHERE tournament_id = :tournament_id AND wallet = :wallet
            """),
            {"tournament_id": str(tournament_id), "wallet": user["wallet"]},
        )
        reg_row = reg_result.fetchone()
        if reg_row:
            user_registered = True
            user_tier = reg_row.tier
            user_agent_name = reg_row.agent_name

    return TournamentDetail(
        id=row.id,
        on_chain_id=row.on_chain_id,
        status=row.status,
        max_players=row.max_players,
        registered_players=row.registered_players,
        starting_stack=row.starting_stack,
        blind_structure=blind_structure,
        payout_structure=payout_structure,
        created_at=row.created_at,
        registration_opens_at=row.registration_opens_at,
        starts_at=row.starts_at,
        completed_at=row.completed_at,
        winner_wallet=row.winner_wallet,
        results_hash=row.results_hash.hex() if row.results_hash else None,
        user_registered=user_registered,
        user_tier=user_tier,
        user_agent_name=user_agent_name,
    )


@router.post("/{tournament_id}/register", response_model=RegistrationResponse)
async def register_for_tournament(
    tournament_id: UUID,
    request: RegistrationRequest,
    user: CurrentUser,
    db: DbSession,
    redis: RedisServiceDep,
) -> RegistrationResponse:
    """
    Register for a tournament.

    Requires wallet authentication and legal acknowledgements.
    """
    wallet = user["wallet"]

    # Rate limit: 5 registrations per minute
    if not await redis.check_rate_limit(wallet, "register", 5, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later.",
        )

    # Validate legal acknowledgements
    if not request.accept_tos or not request.confirm_jurisdiction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must accept Terms of Service and confirm jurisdiction",
        )

    # Get tournament
    result = await db.execute(
        text("""
            SELECT t.*, COUNT(r.id) as registered_count
            FROM tournaments t
            LEFT JOIN registrations r ON t.id = r.tournament_id
            WHERE t.id = :id
            GROUP BY t.id
        """),
        {"id": str(tournament_id)},
    )
    tournament = result.fetchone()

    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Check tournament status
    if tournament.status not in ("created", "registration"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tournament is not open for registration (status: {tournament.status})",
        )

    # Check if tournament is full
    if tournament.registered_count >= tournament.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament is full",
        )

    # Check if user already registered
    existing = await db.execute(
        text("""
            SELECT id FROM registrations
            WHERE tournament_id = :tournament_id AND wallet = :wallet
        """),
        {"tournament_id": str(tournament_id), "wallet": wallet},
    )
    if existing.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this tournament",
        )

    # Validate tier-specific requirements
    tier = request.tier.lower()

    if tier in ("basic", "pro") and not request.payment_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment signature required for {tier} tier",
        )

    # Validate agent config based on tier
    agent = request.agent

    # Custom prompts only allowed for PRO tier
    if tier in ("free", "basic") and agent.custom_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{tier.upper()} tier does not support custom prompts. Custom prompts are PRO tier only.",
        )
    # Note: Sliders are now controlled via live settings during the tournament,
    # not at registration time. BASIC and PRO tiers get slider access during live play.

    # Build prompt for hashing
    prompt_content = ""
    if agent.custom_prompt:
        prompt_content = agent.custom_prompt

    # Hash the prompt
    prompt_hash = hashlib.sha256(prompt_content.encode()).digest()

    # Encrypt prompt if provided
    encrypted_prompt = None
    if prompt_content:
        settings = get_settings()
        if settings.PROMPT_ENCRYPTION_KEY:
            # In production, use proper encryption
            # For now, just base64 encode (placeholder)
            import base64

            encrypted_prompt = base64.b64encode(prompt_content.encode()).decode()
        else:
            encrypted_prompt = prompt_content  # Store plaintext in dev

    # Insert registration
    # Note: agent_sliders is deprecated - sliders are now managed via agent_live_settings
    # table during live tournament play for BASIC/PRO tiers
    result = await db.execute(
        text("""
            INSERT INTO registrations (
                tournament_id, wallet, tier, agent_name, agent_image_uri,
                agent_prompt_encrypted, agent_prompt_hash
            ) VALUES (
                :tournament_id, :wallet, :tier, :agent_name, :agent_image_uri,
                :agent_prompt_encrypted, :agent_prompt_hash
            )
            RETURNING id, registered_at
        """),
        {
            "tournament_id": str(tournament_id),
            "wallet": wallet,
            "tier": tier,
            "agent_name": agent.name,
            "agent_image_uri": agent.image_uri,
            "agent_prompt_encrypted": encrypted_prompt,
            "agent_prompt_hash": prompt_hash,
        },
    )

    reg = result.fetchone()

    return RegistrationResponse(
        registration_id=reg.id,
        tournament_id=tournament_id,
        wallet=wallet,
        tier=tier,
        agent_name=agent.name,
        registered_at=reg.registered_at,
        prompt_hash=prompt_hash.hex(),
    )


@router.get("/{tournament_id}/results", response_model=TournamentResultsResponse)
async def get_tournament_results(
    tournament_id: UUID,
    db: DbSession,
) -> TournamentResultsResponse:
    """Get tournament results."""
    # Get tournament
    result = await db.execute(
        text("""
            SELECT id, status, completed_at, results_hash
            FROM tournaments
            WHERE id = :id
        """),
        {"id": str(tournament_id)},
    )
    tournament = result.fetchone()

    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Get results
    results_query = await db.execute(
        text("""
            SELECT
                r.final_rank,
                r.wallet,
                r.agent_name,
                r.points_awarded,
                r.hands_played,
                r.eliminations
            FROM registrations r
            WHERE r.tournament_id = :tournament_id
                AND r.final_rank IS NOT NULL
            ORDER BY r.final_rank ASC
        """),
        {"tournament_id": str(tournament_id)},
    )

    results = [
        PlayerResult(
            rank=row.final_rank,
            wallet=row.wallet,
            agent_name=row.agent_name,
            points_awarded=row.points_awarded or 0,
            hands_played=row.hands_played or 0,
            eliminations=row.eliminations or 0,
        )
        for row in results_query.fetchall()
    ]

    return TournamentResultsResponse(
        tournament_id=tournament.id,
        status=tournament.status,
        completed_at=tournament.completed_at,
        results_hash=tournament.results_hash.hex() if tournament.results_hash else None,
        results=results,
    )
