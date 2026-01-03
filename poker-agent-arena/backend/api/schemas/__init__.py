"""API schemas for request/response validation."""

from api.schemas.auth import (
    NonceResponse,
    SessionResponse,
    UserProfileResponse,
    VerifyRequest,
)
from api.schemas.tournament import (
    AgentConfig,
    AgentSliders,
    BlindLevel,
    BlindStructure,
    CreateTournamentRequest,
    PayoutEntry,
    RegistrationRequest,
    RegistrationResponse,
    TournamentDetail,
    TournamentListItem,
    TournamentResultsResponse,
)
from api.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse

__all__ = [
    # Auth
    "NonceResponse",
    "VerifyRequest",
    "SessionResponse",
    "UserProfileResponse",
    # Tournament
    "TournamentListItem",
    "TournamentDetail",
    "CreateTournamentRequest",
    "RegistrationRequest",
    "RegistrationResponse",
    "TournamentResultsResponse",
    "BlindLevel",
    "BlindStructure",
    "PayoutEntry",
    "AgentSliders",
    "AgentConfig",
    # Leaderboard
    "LeaderboardEntry",
    "LeaderboardResponse",
]
