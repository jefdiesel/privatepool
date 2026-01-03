"""Socket.IO event handlers."""

from __future__ import annotations

import logging
from typing import Any

import socketio

from websocket.auth import (
    check_connection_limit,
    get_session_from_token,
    verify_nonce_signature,
)
from websocket.manager import get_socket_manager

logger = logging.getLogger(__name__)


def register_events(sio: socketio.AsyncServer) -> None:
    """Register all Socket.IO event handlers."""

    @sio.event
    async def connect(sid: str, environ: dict, auth: dict | None = None) -> bool:
        """Handle new WebSocket connection."""
        logger.info(f"Connection attempt: {sid}")

        if not auth:
            logger.warning(f"No auth data provided for {sid}")
            return False

        # Check for session token auth (already authenticated via HTTP)
        token = auth.get("token")
        if token:
            session = await get_session_from_token(token)
            if session:
                wallet = session["wallet"]

                # Check connection limit
                if not await check_connection_limit(wallet):
                    logger.warning(f"Connection limit exceeded for {wallet[:8]}...")
                    await sio.emit(
                        "error",
                        {"code": "CONNECTION_LIMIT", "message": "Too many connections"},
                        to=sid,
                    )
                    return False

                # Register the connection
                manager = get_socket_manager()
                await manager.register_connection(sid, wallet)

                await sio.emit(
                    "authenticated",
                    {"wallet": wallet, "is_admin": session.get("is_admin", False)},
                    to=sid,
                )
                return True

        # Check for signature-based auth
        wallet = auth.get("wallet")
        signature = auth.get("signature")

        if not wallet or not signature:
            logger.warning(f"Missing wallet or signature for {sid}")
            return False

        # Verify the signature
        if not await verify_nonce_signature(wallet, signature):
            logger.warning(f"Invalid signature for {wallet[:8]}...")
            await sio.emit(
                "error",
                {"code": "INVALID_SIGNATURE", "message": "Authentication failed"},
                to=sid,
            )
            return False

        # Check connection limit
        if not await check_connection_limit(wallet):
            logger.warning(f"Connection limit exceeded for {wallet[:8]}...")
            await sio.emit(
                "error",
                {"code": "CONNECTION_LIMIT", "message": "Too many connections"},
                to=sid,
            )
            return False

        # Register the connection
        manager = get_socket_manager()
        await manager.register_connection(sid, wallet)

        await sio.emit(
            "authenticated",
            {"wallet": wallet},
            to=sid,
        )

        return True

    @sio.event
    async def disconnect(sid: str) -> None:
        """Handle WebSocket disconnection."""
        manager = get_socket_manager()
        await manager.unregister_connection(sid)
        logger.info(f"Disconnected: {sid}")

    @sio.event
    async def join_tournament(sid: str, data: dict) -> None:
        """Subscribe to tournament updates."""
        tournament_id = data.get("tournament_id")
        if not tournament_id:
            await sio.emit(
                "error",
                {"code": "INVALID_REQUEST", "message": "tournament_id required"},
                to=sid,
            )
            return

        manager = get_socket_manager()
        await manager.join_tournament(sid, tournament_id)

        await sio.emit(
            "joined_tournament",
            {"tournament_id": tournament_id},
            to=sid,
        )

    @sio.event
    async def leave_tournament(sid: str, data: dict) -> None:
        """Unsubscribe from tournament updates."""
        tournament_id = data.get("tournament_id")
        if not tournament_id:
            return

        manager = get_socket_manager()
        await manager.leave_tournament(sid, tournament_id)

        await sio.emit(
            "left_tournament",
            {"tournament_id": tournament_id},
            to=sid,
        )

    @sio.event
    async def subscribe_table(sid: str, data: dict) -> None:
        """Subscribe to table-specific updates."""
        table_id = data.get("table_id")
        if not table_id:
            await sio.emit(
                "error",
                {"code": "INVALID_REQUEST", "message": "table_id required"},
                to=sid,
            )
            return

        manager = get_socket_manager()
        await manager.subscribe_table(sid, table_id)

        await sio.emit(
            "subscribed_table",
            {"table_id": table_id},
            to=sid,
        )

    @sio.event
    async def unsubscribe_table(sid: str, data: dict) -> None:
        """Unsubscribe from table updates."""
        table_id = data.get("table_id")
        if not table_id:
            return

        manager = get_socket_manager()
        await manager.unsubscribe_table(sid, table_id)

        await sio.emit(
            "unsubscribed_table",
            {"table_id": table_id},
            to=sid,
        )

    @sio.event
    async def ping(sid: str, data: dict = None) -> None:
        """Handle ping for keepalive."""
        await sio.emit("pong", {"timestamp": data.get("timestamp") if data else None}, to=sid)


# Tournament event emitters (called from tournament engine)


async def emit_tournament_started(
    tournament_id: str,
    table_assignments: list[dict],
) -> None:
    """Emit tournament started event with table assignments."""
    manager = get_socket_manager()
    await manager.broadcast_to_tournament(
        tournament_id,
        "tournament:started",
        {
            "tournament_id": tournament_id,
            "table_assignments": table_assignments,
        },
    )


async def emit_tournament_level_up(
    tournament_id: str,
    level: int,
    small_blind: int,
    big_blind: int,
    ante: int,
) -> None:
    """Emit blind level increase event."""
    manager = get_socket_manager()
    await manager.broadcast_to_tournament(
        tournament_id,
        "tournament:level_up",
        {
            "tournament_id": tournament_id,
            "level": level,
            "small_blind": small_blind,
            "big_blind": big_blind,
            "ante": ante,
        },
    )


async def emit_tournament_completed(
    tournament_id: str,
    results: list[dict],
) -> None:
    """Emit tournament completed event with final results."""
    manager = get_socket_manager()
    await manager.broadcast_to_tournament(
        tournament_id,
        "tournament:completed",
        {
            "tournament_id": tournament_id,
            "results": results,
        },
    )


async def emit_player_eliminated(
    tournament_id: str,
    wallet: str,
    position: int,
    eliminator_wallet: str | None,
) -> None:
    """Emit player elimination event."""
    manager = get_socket_manager()
    await manager.broadcast_to_tournament(
        tournament_id,
        "player:eliminated",
        {
            "tournament_id": tournament_id,
            "wallet": wallet,
            "position": position,
            "eliminator_wallet": eliminator_wallet,
        },
    )


async def emit_player_moved(
    tournament_id: str,
    wallet: str,
    from_table_id: str,
    to_table_id: str,
    new_seat: int,
) -> None:
    """Emit player table move event."""
    manager = get_socket_manager()
    await manager.broadcast_to_tournament(
        tournament_id,
        "player:moved",
        {
            "tournament_id": tournament_id,
            "wallet": wallet,
            "from_table_id": from_table_id,
            "to_table_id": to_table_id,
            "new_seat": new_seat,
        },
    )


# Table event emitters


async def emit_table_state(
    table_id: str,
    state: dict,
) -> None:
    """Emit full table state snapshot."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(table_id, "table:state", state)


async def emit_hand_new(
    table_id: str,
    hand_number: int,
    button_seat: int,
    player_stacks: dict[str, int],
) -> None:
    """Emit new hand starting event."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(
        table_id,
        "hand:new",
        {
            "table_id": table_id,
            "hand_number": hand_number,
            "button_seat": button_seat,
            "player_stacks": player_stacks,
        },
    )


async def emit_hand_deal(
    wallet: str,
    table_id: str,
    hole_cards: list[str],
) -> None:
    """Emit hole cards to specific player only."""
    manager = get_socket_manager()
    await manager.send_to_user(
        wallet,
        "hand:deal",
        {
            "table_id": table_id,
            "hole_cards": hole_cards,
        },
    )


async def emit_hand_community(
    table_id: str,
    betting_round: str,
    cards: list[str],
    pot: int,
) -> None:
    """Emit community cards revealed."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(
        table_id,
        "hand:community",
        {
            "table_id": table_id,
            "betting_round": betting_round,
            "cards": cards,
            "pot": pot,
        },
    )


async def emit_hand_action(
    table_id: str,
    wallet: str,
    action: str,
    amount: int | None,
    pot: int,
    stack_remaining: int,
) -> None:
    """Emit player action taken."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(
        table_id,
        "hand:action",
        {
            "table_id": table_id,
            "wallet": wallet,
            "action": action,
            "amount": amount,
            "pot": pot,
            "stack_remaining": stack_remaining,
        },
    )


async def emit_hand_showdown(
    table_id: str,
    showdown_data: list[dict],
    winners: list[dict],
    pot_distribution: dict[str, int],
) -> None:
    """Emit showdown results."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(
        table_id,
        "hand:showdown",
        {
            "table_id": table_id,
            "showdown": showdown_data,
            "winners": winners,
            "pot_distribution": pot_distribution,
        },
    )


async def emit_decision_start(
    table_id: str,
    wallet: str,
    timeout_seconds: int,
    to_call: int,
    min_raise: int,
    pot: int,
) -> None:
    """Emit that a player's decision timer has started."""
    manager = get_socket_manager()
    await manager.broadcast_to_table(
        table_id,
        "decision:start",
        {
            "table_id": table_id,
            "wallet": wallet,
            "timeout_seconds": timeout_seconds,
            "to_call": to_call,
            "min_raise": min_raise,
            "pot": pot,
        },
    )
