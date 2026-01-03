"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NonceResponse(BaseModel):
    """Response with nonce for wallet signature."""

    nonce: str = Field(..., description="Nonce to sign for authentication")
    message: str = Field(..., description="Full message to sign")


class VerifyRequest(BaseModel):
    """Request to verify wallet signature."""

    wallet: str = Field(..., min_length=32, max_length=44, description="Base58 wallet address")
    signature: str = Field(..., description="Base58-encoded signature")


class SessionResponse(BaseModel):
    """Response with session token after verification."""

    token: str = Field(..., description="Session token for authenticated requests")
    wallet: str = Field(..., description="Authenticated wallet address")
    is_admin: bool = Field(default=False, description="Whether wallet has admin privileges")


class UserProfileResponse(BaseModel):
    """User profile response."""

    wallet: str
    is_admin: bool = False

    # Agent config (if exists)
    agent_name: str | None = None
    agent_image_uri: str | None = None
    agent_tier: str | None = None

    # Stats
    tournaments_played: int = 0
    tournaments_won: int = 0
    total_points: int = 0
    best_finish: int | None = None
