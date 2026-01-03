"""Leaderboard schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""

    rank: int
    wallet: str
    agent_name: str | None = None
    total_points: int
    tournaments_played: int
    tournaments_won: int
    best_finish: int | None = None


class LeaderboardResponse(BaseModel):
    """Leaderboard response with pagination."""

    entries: list[LeaderboardEntry]
    total: int
    page: int
    per_page: int
    has_more: bool
