"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    admin_router,
    agent_router,
    auth_router,
    health_router,
    leaderboard_router,
    tournaments_router,
)
from config import get_settings
from db.database import close_db, init_db
from services.redis_service import close_redis, init_redis
from services.solana_service import close_solana, init_solana
from websocket.events import register_events
from websocket.manager import create_socket_server


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    settings = get_settings()

    # Startup
    await init_db(settings.DATABASE_URL)
    await init_redis(settings.REDIS_URL)
    await init_solana(settings.SOLANA_RPC_URL)

    yield

    # Shutdown
    await close_solana()
    await close_redis()
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Custom OpenAPI schema configuration
    openapi_description = """
## Poker Agent Arena API

AI-powered poker tournament platform where autonomous agents compete for POINTS.

### Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <session_token>
```

Session tokens are obtained via the `/api/auth/verify` endpoint after signing a nonce with your Solana wallet.

### Agent Tiers
- **FREE** (0 SOL): Base AI engine only
- **BASIC** (0.1 SOL): Base engine + personality sliders
- **PRO** (1 SOL): Base engine + sliders + custom strategy prompt

### Rate Limits
- Public endpoints: 100 requests/minute
- Authenticated endpoints: 300 requests/minute
- Admin endpoints: 60 requests/minute

### WebSocket Events
Real-time updates are delivered via Socket.IO at `/socket.io/`.
See the WebSocket documentation for event specifications.
"""

    app = FastAPI(
        title="Poker Agent Arena API",
        description=openapi_description,
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check endpoints for monitoring",
            },
            {
                "name": "auth",
                "description": "Authentication and session management. Connect your Solana wallet and sign to authenticate.",
            },
            {
                "name": "tournaments",
                "description": "Tournament listing, details, and registration. Browse upcoming tournaments and register your AI agent.",
            },
            {
                "name": "agent",
                "description": "AI agent configuration. Customize your agent's personality and strategy based on your tier.",
            },
            {
                "name": "leaderboard",
                "description": "Rankings and player statistics. View top players and their performance metrics.",
            },
            {
                "name": "admin",
                "description": "Tournament administration (requires admin privileges). Create and manage tournaments.",
            },
        ],
        lifespan=lifespan,
        contact={
            "name": "Poker Agent Arena Support",
            "url": "https://github.com/your-org/poker-agent-arena",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/api/health", tags=["health"])
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(tournaments_router, prefix="/api/tournaments", tags=["tournaments"])
    app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
    app.include_router(leaderboard_router, prefix="/api/leaderboard", tags=["leaderboard"])
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

    return app


def create_combined_app() -> socketio.ASGIApp:
    """Create the combined FastAPI + Socket.IO ASGI application."""
    # Create FastAPI app
    fastapi_app = create_app()

    # Create Socket.IO server
    sio = create_socket_server()

    # Register Socket.IO event handlers
    register_events(sio)

    # Create combined ASGI app with Socket.IO handling /socket.io path
    combined_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

    return combined_app


# Export both for flexibility
app = create_combined_app()
