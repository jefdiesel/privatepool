"""API routes package."""

from api.routes.admin import router as admin_router
from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router
from api.routes.health import router as health_router
from api.routes.leaderboard import router as leaderboard_router
from api.routes.tournaments import router as tournaments_router

__all__ = [
    "health_router",
    "auth_router",
    "tournaments_router",
    "agent_router",
    "leaderboard_router",
    "admin_router",
]
