"""Agent configuration routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from api.dependencies import CurrentUser, DbSession, RedisServiceDep
from api.schemas.tournament import AgentConfig, AgentSliders, UpdateAgentRequest

router = APIRouter()


@router.get("", response_model=Optional[AgentConfig])
async def get_agent_config(
    user: CurrentUser,
    db: DbSession,
) -> AgentConfig | None:
    """
    Get the current user's default agent configuration.

    Returns the configuration from their most recent tournament registration.
    """
    wallet = user["wallet"]

    result = await db.execute(
        text("""
            SELECT
                r.agent_name,
                r.agent_image_uri,
                r.agent_sliders,
                r.tier
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.wallet = :wallet
            ORDER BY r.registered_at DESC
            LIMIT 1
        """),
        {"wallet": wallet},
    )

    row = result.fetchone()
    if not row:
        return None

    sliders = None
    if row.agent_sliders:
        sliders = AgentSliders(**row.agent_sliders)

    return AgentConfig(
        name=row.agent_name,
        image_uri=row.agent_image_uri,
        sliders=sliders,
        custom_prompt=None,  # Never return the actual prompt
    )


@router.put("", response_model=dict)
async def update_agent_config(
    request: UpdateAgentRequest,
    user: CurrentUser,
    db: DbSession,
    redis: RedisServiceDep,
) -> dict:
    """
    Update the user's default agent configuration.

    This only updates the default configuration used when registering
    for new tournaments. It does not affect existing registrations.

    Note: Custom prompts are stored securely and can only be updated
    during tournament registration.
    """
    wallet = user["wallet"]

    # Rate limit: 10 updates per minute
    if not await redis.check_rate_limit(wallet, "agent_update", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many update requests. Try again later.",
        )

    # Get latest registration to update
    result = await db.execute(
        text("""
            SELECT r.id, r.agent_name, r.agent_image_uri, r.agent_sliders, t.status
            FROM registrations r
            JOIN tournaments t ON r.tournament_id = t.id
            WHERE r.wallet = :wallet
            ORDER BY r.registered_at DESC
            LIMIT 1
        """),
        {"wallet": wallet},
    )

    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No agent configuration found. Register for a tournament first.",
        )

    # Check if tournament has started (prompt locked)
    if row.status in ("in_progress", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update agent configuration for started/completed tournaments",
        )

    # Build update query
    updates = []
    params = {"id": str(row.id)}

    if request.name is not None:
        updates.append("agent_name = :name")
        params["name"] = request.name

    if request.image_uri is not None:
        updates.append("agent_image_uri = :image_uri")
        params["image_uri"] = request.image_uri

    if request.sliders is not None:
        import json

        updates.append("agent_sliders = :sliders")
        params["sliders"] = json.dumps(request.sliders.model_dump())

    if not updates:
        return {"status": "no_changes"}

    update_sql = ", ".join(updates)
    await db.execute(
        text(f"UPDATE registrations SET {update_sql} WHERE id = :id"),
        params,
    )

    return {"status": "updated"}
