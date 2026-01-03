"""Leaderboard routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import text

from api.dependencies import DbSession
from api.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: DbSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> LeaderboardResponse:
    """
    Get the global POINTS leaderboard.

    Returns players sorted by total points descending.
    """
    offset = (page - 1) * per_page

    # Get total count
    count_result = await db.execute(
        text("SELECT COUNT(*) FROM player_stats WHERE total_points > 0")
    )
    total = count_result.scalar() or 0

    # Get leaderboard entries
    result = await db.execute(
        text("""
            SELECT
                ps.wallet,
                ps.total_points,
                ps.tournaments_played,
                ps.tournaments_won,
                ps.best_finish,
                (
                    SELECT r.agent_name
                    FROM registrations r
                    WHERE r.wallet = ps.wallet
                    ORDER BY r.registered_at DESC
                    LIMIT 1
                ) as agent_name
            FROM player_stats ps
            WHERE ps.total_points > 0
            ORDER BY ps.total_points DESC
            LIMIT :limit OFFSET :offset
        """),
        {"limit": per_page, "offset": offset},
    )

    entries = []
    for i, row in enumerate(result.fetchall()):
        entries.append(
            LeaderboardEntry(
                rank=offset + i + 1,
                wallet=row.wallet,
                agent_name=row.agent_name,
                total_points=row.total_points,
                tournaments_played=row.tournaments_played,
                tournaments_won=row.tournaments_won,
                best_finish=row.best_finish,
            )
        )

    return LeaderboardResponse(
        entries=entries,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(offset + per_page) < total,
    )


@router.get("/player/{wallet}", response_model=Optional[LeaderboardEntry])
async def get_player_rank(
    wallet: str,
    db: DbSession,
) -> LeaderboardEntry | None:
    """Get a specific player's rank and stats."""
    # Get player stats with rank
    result = await db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    wallet,
                    total_points,
                    tournaments_played,
                    tournaments_won,
                    best_finish,
                    ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank
                FROM player_stats
                WHERE total_points > 0
            )
            SELECT r.*, (
                SELECT reg.agent_name
                FROM registrations reg
                WHERE reg.wallet = r.wallet
                ORDER BY reg.registered_at DESC
                LIMIT 1
            ) as agent_name
            FROM ranked r
            WHERE r.wallet = :wallet
        """),
        {"wallet": wallet},
    )

    row = result.fetchone()
    if not row:
        return None

    return LeaderboardEntry(
        rank=row.rank,
        wallet=row.wallet,
        agent_name=row.agent_name,
        total_points=row.total_points,
        tournaments_played=row.tournaments_played,
        tournaments_won=row.tournaments_won,
        best_finish=row.best_finish,
    )
