"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import CurrentUser, DbSession, RedisServiceDep
from api.schemas.auth import (
    NonceResponse,
    SessionResponse,
    UserProfileResponse,
    VerifyRequest,
)
from websocket.auth import (
    create_session_token,
    generate_nonce,
    is_admin_wallet,
    verify_nonce_signature,
)

router = APIRouter()


@router.get("/nonce", response_model=NonceResponse)
async def get_nonce(
    wallet: str = Query(..., min_length=32, max_length=44),
    redis: RedisServiceDep = None,
) -> NonceResponse:
    """
    Get a nonce for wallet authentication.

    The client should sign the returned message with their wallet
    and submit the signature to /verify.
    """
    # Rate limit: 10 nonce requests per minute
    if redis:
        if not await redis.check_rate_limit(wallet, "nonce", 10, 60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many nonce requests. Try again later.",
            )

    nonce = await generate_nonce(wallet)

    message = f"Sign this message to authenticate with Poker Agent Arena.\n\nNonce: {nonce}"

    return NonceResponse(nonce=nonce, message=message)


@router.post("/verify", response_model=SessionResponse)
async def verify_signature(
    request: VerifyRequest,
    redis: RedisServiceDep = None,
) -> SessionResponse:
    """
    Verify a wallet signature and create a session.

    Returns a session token for authenticated requests.
    """
    # Rate limit: 5 verify attempts per minute
    if redis:
        if not await redis.check_rate_limit(request.wallet, "verify", 5, 60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts. Try again later.",
            )

    # Verify the signature
    is_valid = await verify_nonce_signature(request.wallet, request.signature)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or expired nonce",
        )

    # Create session token
    token = await create_session_token(request.wallet)

    return SessionResponse(
        token=token,
        wallet=request.wallet,
        is_admin=is_admin_wallet(request.wallet),
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_profile(
    user: CurrentUser,
    db: DbSession,
) -> UserProfileResponse:
    """Get the current user's profile."""
    from sqlalchemy import text

    wallet = user["wallet"]

    # Get player stats
    stats_result = await db.execute(
        text("""
            SELECT
                tournaments_played,
                tournaments_won,
                total_points,
                best_finish
            FROM player_stats
            WHERE wallet = :wallet
        """),
        {"wallet": wallet},
    )
    stats_row = stats_result.fetchone()

    # Get latest agent config from most recent registration
    agent_result = await db.execute(
        text("""
            SELECT
                r.tier,
                r.agent_name,
                r.agent_image_uri
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.wallet = :wallet
            ORDER BY r.registered_at DESC
            LIMIT 1
        """),
        {"wallet": wallet},
    )
    agent_row = agent_result.fetchone()

    return UserProfileResponse(
        wallet=wallet,
        is_admin=user.get("is_admin", False),
        agent_name=agent_row.agent_name if agent_row else None,
        agent_image_uri=agent_row.agent_image_uri if agent_row else None,
        agent_tier=agent_row.tier if agent_row else None,
        tournaments_played=stats_row.tournaments_played if stats_row else 0,
        tournaments_won=stats_row.tournaments_won if stats_row else 0,
        total_points=stats_row.total_points if stats_row else 0,
        best_finish=stats_row.best_finish if stats_row else None,
    )


@router.post("/logout")
async def logout(
    user: CurrentUser,
) -> dict:
    """
    Logout and invalidate the current session.

    Note: This is a soft logout - the token is not immediately invalidated
    but will be removed when the user next authenticates.
    """
    return {"status": "logged_out"}
