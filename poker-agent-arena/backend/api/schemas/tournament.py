"""Tournament schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BlindLevel(BaseModel):
    """Single blind level configuration."""

    level: int
    small_blind: int
    big_blind: int
    ante: int = 0  # BB pays only
    duration_minutes: int


class BlindStructure(BaseModel):
    """Complete blind structure."""

    name: str = Field(..., description="Template name: turbo, standard, deep_stack, or custom")
    levels: list[BlindLevel]


class PayoutEntry(BaseModel):
    """Single payout entry."""

    rank: int
    points: int


class AgentSliders(BaseModel):
    """Agent strategy sliders (1-10 scale).

    - aggression: 1 = passive (check/call), 10 = aggressive (bet/raise)
    - tightness: 1 = loose (many hands), 10 = tight (selective)
    """

    aggression: int = Field(5, ge=1, le=10)
    tightness: int = Field(5, ge=1, le=10)


class AgentConfig(BaseModel):
    """Agent configuration for registration."""

    name: str = Field(..., min_length=1, max_length=32)
    image_uri: str | None = Field(None, max_length=256)
    custom_prompt: str | None = Field(None, max_length=2000)


class LiveSettingsResponse(BaseModel):
    """Response for live settings endpoint."""

    tournament_id: str
    wallet: str
    # Active settings (currently used by agent)
    active_aggression: int = Field(5, ge=1, le=10)
    active_tightness: int = Field(5, ge=1, le=10)
    # Pending settings (slider position, not yet confirmed)
    pending_aggression: int | None = None
    pending_tightness: int | None = None
    # Confirmed settings (waiting for next hand)
    confirmed_aggression: int | None = None
    confirmed_tightness: int | None = None
    confirmed_at: str | None = None


class UpdateLiveSettingsRequest(BaseModel):
    """Request to update pending slider values."""

    aggression: int = Field(..., ge=1, le=10)
    tightness: int = Field(..., ge=1, le=10)


class TournamentListItem(BaseModel):
    """Tournament summary for list view."""

    id: UUID
    on_chain_id: int
    status: str
    max_players: int
    registered_players: int
    starting_stack: int
    starts_at: datetime
    blind_structure_name: str
    total_points_prize: int


class TournamentDetail(BaseModel):
    """Full tournament details."""

    id: UUID
    on_chain_id: int
    status: str
    max_players: int
    registered_players: int
    starting_stack: int
    blind_structure: BlindStructure
    payout_structure: list[PayoutEntry]
    created_at: datetime
    registration_opens_at: datetime | None
    starts_at: datetime
    completed_at: datetime | None

    # Results (if completed)
    winner_wallet: str | None = None
    results_hash: str | None = None

    # User's registration status (if authenticated)
    user_registered: bool = False
    user_tier: str | None = None
    user_agent_name: str | None = None


class RegistrationRequest(BaseModel):
    """Tournament registration request."""

    tier: str = Field(..., pattern="^(free|basic|pro)$")
    agent: AgentConfig
    accept_tos: bool = Field(..., description="Accept Terms of Service")
    confirm_jurisdiction: bool = Field(..., description="Confirm not in restricted jurisdiction")

    # Payment proof (for basic/pro tiers)
    payment_signature: str | None = Field(None, description="Solana transaction signature for payment")


class RegistrationResponse(BaseModel):
    """Tournament registration response."""

    registration_id: UUID
    tournament_id: UUID
    wallet: str
    tier: str
    agent_name: str
    registered_at: datetime
    prompt_hash: str


class TournamentResultsResponse(BaseModel):
    """Tournament results response."""

    tournament_id: UUID
    status: str
    completed_at: datetime | None
    results_hash: str | None
    results: list["PlayerResult"]


class PlayerResult(BaseModel):
    """Single player result."""

    rank: int
    wallet: str
    agent_name: str
    points_awarded: int
    hands_played: int
    eliminations: int


class CreateTournamentRequest(BaseModel):
    """Admin request to create tournament."""

    max_players: int = Field(..., ge=9, le=54, description="Must be 9, 18, 27, 36, 45, or 54")
    starting_stack: int = Field(10000, ge=1000)
    blind_structure: BlindStructure
    payout_structure: list[PayoutEntry]
    registration_opens_at: datetime | None = None
    starts_at: datetime


class UpdateAgentRequest(BaseModel):
    """Request to update agent configuration."""

    name: str | None = Field(None, min_length=1, max_length=32)
    image_uri: str | None = Field(None, max_length=256)
    custom_prompt: str | None = Field(None, max_length=2000)


# Fix forward reference
TournamentResultsResponse.model_rebuild()
