"""WebSocket connection manager using Socket.IO."""

from __future__ import annotations

import json
import logging
from typing import Any

import socketio

from config import get_settings
from services.redis_service import get_redis

logger = logging.getLogger(__name__)

# Global Socket.IO server instance
_sio: socketio.AsyncServer | None = None
_manager: "ConnectionManager | None" = None


def create_socket_server() -> socketio.AsyncServer:
    """Create and configure the Socket.IO server."""
    global _sio

    settings = get_settings()

    # Use Redis for pub/sub in production to support multiple workers
    if settings.is_production:
        mgr = socketio.AsyncRedisManager(settings.REDIS_URL)
        _sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=settings.CORS_ORIGINS,
            client_manager=mgr,
            logger=settings.DEBUG,
            engineio_logger=settings.DEBUG,
        )
    else:
        _sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=settings.CORS_ORIGINS,
            logger=settings.DEBUG,
            engineio_logger=settings.DEBUG,
        )

    return _sio


def get_sio() -> socketio.AsyncServer:
    """Get the Socket.IO server instance."""
    if _sio is None:
        raise RuntimeError("Socket.IO server not initialized")
    return _sio


def get_socket_manager() -> "ConnectionManager":
    """Get the connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager(get_sio())
    return _manager


class ConnectionManager:
    """Manages WebSocket connections and room subscriptions."""

    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        # Track wallet -> sid mappings for direct messaging
        self.wallet_to_sid: dict[str, set[str]] = {}
        # Track sid -> wallet for cleanup
        self.sid_to_wallet: dict[str, str] = {}

    async def register_connection(self, sid: str, wallet: str) -> None:
        """Register a new connection for a wallet."""
        if wallet not in self.wallet_to_sid:
            self.wallet_to_sid[wallet] = set()
        self.wallet_to_sid[wallet].add(sid)
        self.sid_to_wallet[sid] = wallet

        # Store session in Redis for persistence
        redis = get_redis()
        from services.redis_service import RedisService

        redis_service = RedisService(redis)
        await redis_service.set_session(sid, {"wallet": wallet})

        logger.info(f"Registered connection: {sid} for wallet: {wallet[:8]}...")

    async def unregister_connection(self, sid: str) -> None:
        """Unregister a connection."""
        wallet = self.sid_to_wallet.pop(sid, None)
        if wallet and wallet in self.wallet_to_sid:
            self.wallet_to_sid[wallet].discard(sid)
            if not self.wallet_to_sid[wallet]:
                del self.wallet_to_sid[wallet]

        # Clean up Redis session
        redis = get_redis()
        from services.redis_service import RedisService

        redis_service = RedisService(redis)
        await redis_service.delete_session(sid)

        logger.info(f"Unregistered connection: {sid}")

    async def join_tournament(self, sid: str, tournament_id: str) -> None:
        """Subscribe a client to tournament updates."""
        room = f"tournament:{tournament_id}"
        await self.sio.enter_room(sid, room)
        logger.debug(f"Client {sid} joined room {room}")

    async def leave_tournament(self, sid: str, tournament_id: str) -> None:
        """Unsubscribe a client from tournament updates."""
        room = f"tournament:{tournament_id}"
        await self.sio.leave_room(sid, room)
        logger.debug(f"Client {sid} left room {room}")

    async def subscribe_table(self, sid: str, table_id: str) -> None:
        """Subscribe a client to table-specific updates."""
        room = f"table:{table_id}"
        await self.sio.enter_room(sid, room)
        logger.debug(f"Client {sid} subscribed to table {table_id}")

    async def unsubscribe_table(self, sid: str, table_id: str) -> None:
        """Unsubscribe a client from table updates."""
        room = f"table:{table_id}"
        await self.sio.leave_room(sid, room)
        logger.debug(f"Client {sid} unsubscribed from table {table_id}")

    # Broadcasting methods

    async def broadcast_to_tournament(
        self,
        tournament_id: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast an event to all clients in a tournament room."""
        room = f"tournament:{tournament_id}"
        await self.sio.emit(event, data, room=room)
        logger.debug(f"Broadcast {event} to {room}")

    async def broadcast_to_table(
        self,
        table_id: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Broadcast an event to all clients subscribed to a table."""
        room = f"table:{table_id}"
        await self.sio.emit(event, data, room=room)
        logger.debug(f"Broadcast {event} to table {table_id}")

    async def send_to_user(
        self,
        wallet: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Send an event to a specific user by wallet address."""
        sids = self.wallet_to_sid.get(wallet, set())
        for sid in sids:
            await self.sio.emit(event, data, to=sid)
        if sids:
            logger.debug(f"Sent {event} to wallet {wallet[:8]}...")

    async def send_to_sid(
        self,
        sid: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """Send an event to a specific connection."""
        await self.sio.emit(event, data, to=sid)

    # Connection count helpers

    async def get_room_count(self, room: str) -> int:
        """Get the number of clients in a room."""
        # Socket.IO doesn't expose this directly, use manager
        participants = self.sio.manager.get_participants("/", room)
        return len(list(participants))

    def get_wallet_connection_count(self, wallet: str) -> int:
        """Get the number of active connections for a wallet."""
        return len(self.wallet_to_sid.get(wallet, set()))
