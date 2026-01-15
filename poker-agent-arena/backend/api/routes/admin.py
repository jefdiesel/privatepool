"""Admin routes for tournament management."""

import json
import logging
import random
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from sqlalchemy import text

from api.dependencies import AdminUser, DbSession
from api.schemas.tournament import (
    BlindLevel,
    BlindStructure,
    CreateTournamentRequest,
    PayoutEntry,
    TournamentDetail,
)
from config import get_settings

settings = get_settings()
from services.finalization_service import FinalizationService
from services.solana_service import SolanaService, get_solana

logger = logging.getLogger(__name__)

router = APIRouter()


# Pre-defined blind structure templates
BLIND_TEMPLATES = {
    "turbo": [
        {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 6},
        {"level": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 6},
        {"level": 3, "small_blind": 75, "big_blind": 150, "ante": 0, "duration_minutes": 6},
        {"level": 4, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 6},
        {"level": 5, "small_blind": 150, "big_blind": 300, "ante": 50, "duration_minutes": 6},
        {"level": 6, "small_blind": 200, "big_blind": 400, "ante": 50, "duration_minutes": 6},
        {"level": 7, "small_blind": 300, "big_blind": 600, "ante": 75, "duration_minutes": 6},
        {"level": 8, "small_blind": 400, "big_blind": 800, "ante": 100, "duration_minutes": 6},
        {"level": 9, "small_blind": 600, "big_blind": 1200, "ante": 150, "duration_minutes": 6},
        {"level": 10, "small_blind": 800, "big_blind": 1600, "ante": 200, "duration_minutes": 6},
        {"level": 11, "small_blind": 1000, "big_blind": 2000, "ante": 250, "duration_minutes": 6},
        {"level": 12, "small_blind": 1500, "big_blind": 3000, "ante": 400, "duration_minutes": 6},
    ],
    "standard": [
        {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 12},
        {"level": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 12},
        {"level": 3, "small_blind": 75, "big_blind": 150, "ante": 0, "duration_minutes": 12},
        {"level": 4, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 12},
        {"level": 5, "small_blind": 125, "big_blind": 250, "ante": 25, "duration_minutes": 12},
        {"level": 6, "small_blind": 150, "big_blind": 300, "ante": 50, "duration_minutes": 12},
        {"level": 7, "small_blind": 200, "big_blind": 400, "ante": 50, "duration_minutes": 12},
        {"level": 8, "small_blind": 250, "big_blind": 500, "ante": 75, "duration_minutes": 12},
        {"level": 9, "small_blind": 300, "big_blind": 600, "ante": 75, "duration_minutes": 12},
        {"level": 10, "small_blind": 400, "big_blind": 800, "ante": 100, "duration_minutes": 12},
        {"level": 11, "small_blind": 500, "big_blind": 1000, "ante": 125, "duration_minutes": 12},
        {"level": 12, "small_blind": 600, "big_blind": 1200, "ante": 150, "duration_minutes": 12},
    ],
    "deep_stack": [
        {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 20},
        {"level": 2, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 20},
        {"level": 3, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 20},
        {"level": 4, "small_blind": 75, "big_blind": 150, "ante": 0, "duration_minutes": 20},
        {"level": 5, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 20},
        {"level": 6, "small_blind": 125, "big_blind": 250, "ante": 25, "duration_minutes": 20},
        {"level": 7, "small_blind": 150, "big_blind": 300, "ante": 50, "duration_minutes": 20},
        {"level": 8, "small_blind": 200, "big_blind": 400, "ante": 50, "duration_minutes": 20},
        {"level": 9, "small_blind": 250, "big_blind": 500, "ante": 75, "duration_minutes": 20},
        {"level": 10, "small_blind": 300, "big_blind": 600, "ante": 75, "duration_minutes": 20},
        {"level": 11, "small_blind": 400, "big_blind": 800, "ante": 100, "duration_minutes": 20},
        {"level": 12, "small_blind": 500, "big_blind": 1000, "ante": 125, "duration_minutes": 20},
    ],
}


@router.post("/tournaments", response_model=TournamentDetail)
async def create_tournament(
    request: CreateTournamentRequest,
    admin: AdminUser,
    db: DbSession,
) -> TournamentDetail:
    """
    Create a new tournament (admin only).

    Validates player count (must be 9, 18, 27, 36, 45, or 54)
    and creates the tournament record.
    """
    # Validate max_players is valid table size
    valid_sizes = {9, 18, 27, 36, 45, 54}
    if request.max_players not in valid_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_players must be one of: {sorted(valid_sizes)}",
        )

    # Generate on-chain ID (in production, this would come from the smart contract)
    on_chain_id = random.randint(1, 2**31)

    # Convert structures to JSON
    blind_structure_json = {
        "name": request.blind_structure.name,
        "levels": [level.model_dump() for level in request.blind_structure.levels],
    }

    payout_structure_json = [
        {"rank": p.rank, "points": p.points} for p in request.payout_structure
    ]

    # Insert tournament
    result = await db.execute(
        text("""
            INSERT INTO tournaments (
                on_chain_id, status, max_players, starting_stack,
                blind_structure, payout_structure,
                registration_opens_at, starts_at
            ) VALUES (
                :on_chain_id, 'created', :max_players, :starting_stack,
                :blind_structure, :payout_structure,
                :registration_opens_at, :starts_at
            )
            RETURNING id, created_at
        """),
        {
            "on_chain_id": on_chain_id,
            "max_players": request.max_players,
            "starting_stack": request.starting_stack,
            "blind_structure": json.dumps(blind_structure_json),
            "payout_structure": json.dumps(payout_structure_json),
            "registration_opens_at": request.registration_opens_at,
            "starts_at": request.starts_at,
        },
    )

    row = result.fetchone()

    return TournamentDetail(
        id=row.id,
        on_chain_id=on_chain_id,
        status="created",
        max_players=request.max_players,
        registered_players=0,
        starting_stack=request.starting_stack,
        blind_structure=request.blind_structure,
        payout_structure=request.payout_structure,
        created_at=row.created_at,
        registration_opens_at=request.registration_opens_at,
        starts_at=request.starts_at,
        completed_at=None,
        user_registered=False,
    )


@router.post("/tournaments/{tournament_id}/start")
async def start_tournament_registration(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> dict:
    """
    Open tournament for registration (admin only).

    Changes status from 'created' to 'registration'.
    """
    result = await db.execute(
        text("SELECT status FROM tournaments WHERE id = :id"),
        {"id": str(tournament_id)},
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    if row.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot open registration for tournament with status: {row.status}",
        )

    await db.execute(
        text("""
            UPDATE tournaments
            SET status = 'registration', registration_opens_at = NOW()
            WHERE id = :id
        """),
        {"id": str(tournament_id)},
    )

    return {"status": "registration_opened", "tournament_id": str(tournament_id)}


@router.post("/tournaments/{tournament_id}/cancel")
async def cancel_tournament(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> dict:
    """
    Cancel a tournament (admin only).

    Can only cancel tournaments that haven't started yet.
    """
    result = await db.execute(
        text("SELECT status FROM tournaments WHERE id = :id"),
        {"id": str(tournament_id)},
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    if row.status in ("in_progress", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel tournament with status: {row.status}",
        )

    await db.execute(
        text("UPDATE tournaments SET status = 'cancelled' WHERE id = :id"),
        {"id": str(tournament_id)},
    )

    return {"status": "cancelled", "tournament_id": str(tournament_id)}


@router.get("/blind-templates")
async def get_blind_templates(
    admin: AdminUser,
) -> dict:
    """Get available blind structure templates."""
    return {
        "templates": {
            name: [BlindLevel(**level) for level in levels]
            for name, levels in BLIND_TEMPLATES.items()
        }
    }


@router.get("/tournaments/{tournament_id}/stats")
async def get_tournament_stats(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> dict:
    """
    Get detailed tournament statistics (admin only).

    Includes registration counts, AI usage stats, etc.
    """
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

    # Get tier breakdown
    tier_result = await db.execute(
        text("""
            SELECT tier, COUNT(*) as count
            FROM registrations
            WHERE tournament_id = :id
            GROUP BY tier
        """),
        {"id": str(tournament_id)},
    )
    tier_breakdown = {row.tier: row.count for row in tier_result.fetchall()}

    # Get hand count
    hands_result = await db.execute(
        text("""
            SELECT COUNT(*) as count
            FROM hands
            WHERE tournament_id = :id
        """),
        {"id": str(tournament_id)},
    )
    hands_count = hands_result.scalar() or 0

    return {
        "tournament_id": str(tournament_id),
        "status": tournament.status,
        "registered_players": tournament.registered_count,
        "max_players": tournament.max_players,
        "tier_breakdown": tier_breakdown,
        "hands_played": hands_count,
        "starts_at": tournament.starts_at.isoformat() if tournament.starts_at else None,
        "completed_at": tournament.completed_at.isoformat() if tournament.completed_at else None,
    }


# ============================================================================
# Phase 5: On-Chain Settlement Endpoints
# ============================================================================


class BeginTournamentResponse(BaseModel):
    """Response for beginning a tournament."""

    status: str
    tournament_id: str
    tx_signature: str


class FinalizeTournamentResponse(BaseModel):
    """Response for finalizing a tournament."""

    status: str
    tournament_id: str
    finalization_tx: str
    results_recorded: int
    points_distributed: int


def _get_finalization_service() -> FinalizationService:
    """Create FinalizationService with admin credentials."""
    solana_client = get_solana()
    solana_service = SolanaService(solana_client, settings.SOLANA_PROGRAM_ID)

    # Load admin keypair from environment
    admin_keypair = Keypair.from_base58_string(settings.ADMIN_PRIVATE_KEY)
    points_mint = Pubkey.from_string(settings.POINTS_MINT_ADDRESS)

    return FinalizationService(
        solana_service=solana_service,
        admin_keypair=admin_keypair,
        points_mint=points_mint,
    )


@router.post("/tournaments/{tournament_id}/begin", response_model=BeginTournamentResponse)
async def begin_tournament(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> BeginTournamentResponse:
    """
    Begin a tournament (admin only).

    This endpoint:
    1. Validates the tournament is in 'registration' status with >= 2 players
    2. Calls StartTournament on-chain to commit the RNG seed
    3. Updates status to 'in_progress'

    The on-chain instruction captures the current slot and blockhash
    for provably fair randomness.
    """
    # Check tournament status
    result = await db.execute(
        text("""
            SELECT t.*, COUNT(r.id) as player_count
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

    if tournament.status != "registration":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot begin tournament with status: {tournament.status}",
        )

    if tournament.player_count < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Need at least 2 players to begin (have {tournament.player_count})",
        )

    # Call StartTournament on-chain
    try:
        finalization_service = _get_finalization_service()
        solana_service = finalization_service.solana
        admin_keypair = finalization_service.admin_keypair

        # Build instruction
        from solders.hash import Hash
        from solders.message import Message
        from solders.transaction import Transaction

        ix = solana_service.build_start_tournament_ix(
            admin=admin_keypair.pubkey(),
            tournament_id=tournament.on_chain_id,
        )

        recent_blockhash = await solana_service.get_blockhash()
        message = Message.new_with_blockhash(
            [ix],
            admin_keypair.pubkey(),
            Hash.from_bytes(recent_blockhash),
        )
        tx = Transaction.new_unsigned(message)
        tx.sign([admin_keypair], Hash.from_bytes(recent_blockhash))

        signature = await solana_service.send_and_confirm_tx(tx, [admin_keypair])

        # Update database
        await db.execute(
            text("""
                UPDATE tournaments
                SET status = 'in_progress', seed_slot = :slot, seed_blockhash = :blockhash
                WHERE id = :id
            """),
            {
                "id": str(tournament_id),
                "slot": await solana_service.get_slot(),
                "blockhash": recent_blockhash,
            },
        )

        # Initialize live settings for BASIC and PRO tier players
        await db.execute(
            text("""
                INSERT INTO agent_live_settings (tournament_id, wallet)
                SELECT :tournament_id, wallet
                FROM registrations
                WHERE tournament_id = :tournament_id AND tier IN ('basic', 'pro')
                ON CONFLICT (tournament_id, wallet) DO NOTHING
            """),
            {"tournament_id": str(tournament_id)},
        )

        logger.info(f"Tournament {tournament_id} started: {signature}")

        return BeginTournamentResponse(
            status="in_progress",
            tournament_id=str(tournament_id),
            tx_signature=signature,
        )

    except Exception as e:
        logger.error(f"Failed to start tournament {tournament_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start tournament on-chain: {str(e)}",
        )


@router.post("/tournaments/{tournament_id}/finalize", response_model=FinalizeTournamentResponse)
async def finalize_tournament(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> FinalizeTournamentResponse:
    """
    Finalize a tournament and distribute points (admin only).

    This endpoint performs the full on-chain settlement:
    1. Calls FinalizeTournament to commit results hash and winner
    2. Calls RecordPlayerResult for each player
    3. Calls DistributePoints to mint POINTS tokens to winners

    This is an atomic operation - if any step fails, the entire
    operation should be rolled back.
    """
    # Check tournament status
    result = await db.execute(
        text("SELECT * FROM tournaments WHERE id = :id"),
        {"id": str(tournament_id)},
    )
    tournament = result.fetchone()

    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    if tournament.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot finalize tournament with status: {tournament.status}",
        )

    # Check that results have been calculated
    result = await db.execute(
        text("""
            SELECT COUNT(*) as count
            FROM registrations
            WHERE tournament_id = :id AND final_rank IS NOT NULL
        """),
        {"id": str(tournament_id)},
    )
    results_count = result.scalar()

    if results_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No results recorded for this tournament. Run the tournament first.",
        )

    try:
        finalization_service = _get_finalization_service()

        # Step 1: Finalize tournament on-chain
        finalization_tx = await finalization_service.finalize_tournament_on_chain(
            db, tournament_id
        )

        # Step 2: Record all player results on-chain
        result_txs = await finalization_service.record_all_player_results(
            db, tournament_id
        )

        # Step 3: Distribute points to winners
        distribution_txs = await finalization_service.distribute_all_points(
            db, tournament_id
        )

        logger.info(
            f"Tournament {tournament_id} finalized: "
            f"{len(result_txs)} results, {len(distribution_txs)} distributions"
        )

        return FinalizeTournamentResponse(
            status="completed",
            tournament_id=str(tournament_id),
            finalization_tx=finalization_tx,
            results_recorded=len(result_txs),
            points_distributed=len(distribution_txs),
        )

    except Exception as e:
        logger.error(f"Failed to finalize tournament {tournament_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize tournament: {str(e)}",
        )


@router.get("/tournaments/{tournament_id}/settlement-status")
async def get_settlement_status(
    tournament_id: UUID,
    admin: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """
    Get the settlement status for a tournament (admin only).

    Shows which players have had their results recorded
    and points distributed.
    """
    # Get tournament
    result = await db.execute(
        text("SELECT * FROM tournaments WHERE id = :id"),
        {"id": str(tournament_id)},
    )
    tournament = result.fetchone()

    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    # Get registration settlement status
    result = await db.execute(
        text("""
            SELECT
                wallet,
                final_rank,
                points_awarded,
                result_recorded_at,
                points_distributed_at,
                result_tx,
                distribution_tx
            FROM registrations
            WHERE tournament_id = :id
            ORDER BY final_rank NULLS LAST
        """),
        {"id": str(tournament_id)},
    )
    registrations = result.fetchall()

    players = [
        {
            "wallet": r.wallet,
            "final_rank": r.final_rank,
            "points_awarded": r.points_awarded,
            "result_recorded": r.result_recorded_at is not None,
            "result_tx": r.result_tx,
            "points_distributed": r.points_distributed_at is not None,
            "distribution_tx": r.distribution_tx,
        }
        for r in registrations
    ]

    return {
        "tournament_id": str(tournament_id),
        "status": tournament.status,
        "finalization_tx": tournament.finalization_tx,
        "points_distributed": tournament.points_distributed,
        "players": players,
        "summary": {
            "total_players": len(players),
            "results_recorded": sum(1 for p in players if p["result_recorded"]),
            "points_distributed": sum(1 for p in players if p["points_distributed"]),
        },
    }
