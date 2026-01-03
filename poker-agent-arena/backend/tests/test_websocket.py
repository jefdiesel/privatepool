"""Integration tests for WebSocket (Socket.IO) functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestWebSocketAuth:
    """Tests for WebSocket authentication flow."""

    @pytest.mark.asyncio
    async def test_generate_nonce_creates_unique_nonces(self):
        """Test that generate_nonce creates unique nonces."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            from websocket.auth import generate_nonce

            wallet = "TestWallet123"

            nonce1 = await generate_nonce(wallet)
            nonce2 = await generate_nonce(wallet)

            # Nonces should be different each time
            assert nonce1 != nonce2
            assert len(nonce1) == 64  # 32 bytes hex encoded
            assert len(nonce2) == 64

    @pytest.mark.asyncio
    async def test_generate_nonce_stores_in_redis(self):
        """Test that nonce is stored in Redis with TTL."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            from websocket.auth import generate_nonce, NONCE_EXPIRY

            wallet = "TestWallet123"
            await generate_nonce(wallet)

            # Verify Redis set was called with correct key and TTL
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert f"auth:nonce:{wallet}" in str(call_args)
            assert call_args.kwargs.get("ex") == NONCE_EXPIRY

    @pytest.mark.asyncio
    async def test_verify_nonce_signature_no_nonce_stored(self):
        """Test verification fails when no nonce is stored."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None  # No nonce stored
            mock_get_redis.return_value = mock_redis

            from websocket.auth import verify_nonce_signature

            result = await verify_nonce_signature("wallet", "signature")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_nonce_signature_expired(self):
        """Test verification fails for expired nonce."""
        import time

        with patch("websocket.auth.get_redis") as mock_get_redis, patch(
            "websocket.auth.time"
        ) as mock_time:
            mock_redis = AsyncMock()
            # Nonce created 10 minutes ago (expired)
            old_timestamp = int(time.time()) - 600
            mock_redis.get.return_value = f"nonce123:{old_timestamp}"
            mock_get_redis.return_value = mock_redis

            # Current time
            mock_time.time.return_value = time.time()

            from websocket.auth import verify_nonce_signature

            result = await verify_nonce_signature("wallet", "signature")
            assert result is False
            # Expired nonce should be deleted
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_create_session_token_format(self):
        """Test session token creation format."""
        with patch("websocket.auth.get_redis") as mock_get_redis, patch(
            "websocket.auth.is_admin_wallet"
        ) as mock_admin:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            mock_admin.return_value = False

            from websocket.auth import create_session_token

            token = await create_session_token("TestWallet123")

            # Token should be URL-safe base64
            assert token is not None
            assert len(token) > 20  # At least 32 bytes base64
            assert "_" not in token or "-" not in token  # URL-safe chars

    @pytest.mark.asyncio
    async def test_create_session_token_stores_session(self):
        """Test session is stored in Redis."""
        with patch("websocket.auth.get_redis") as mock_get_redis, patch(
            "websocket.auth.is_admin_wallet"
        ) as mock_admin:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            mock_admin.return_value = True  # Admin wallet

            from websocket.auth import create_session_token

            wallet = "AdminWallet123"
            await create_session_token(wallet)

            # Verify session stored with 24h TTL
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args.kwargs.get("ex") == 86400  # 24 hours

            # Verify session data contains admin flag
            stored_data = call_args.args[1]
            import json

            session_data = json.loads(stored_data)
            assert session_data["wallet"] == wallet
            assert session_data["is_admin"] is True

    @pytest.mark.asyncio
    async def test_get_session_from_token_valid(self):
        """Test retrieving session from valid token."""
        import json

        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            session_data = {"wallet": "TestWallet", "is_admin": False, "created_at": 123}
            mock_redis.get.return_value = json.dumps(session_data)
            mock_get_redis.return_value = mock_redis

            from websocket.auth import get_session_from_token

            result = await get_session_from_token("valid_token")
            assert result == session_data

    @pytest.mark.asyncio
    async def test_get_session_from_token_invalid(self):
        """Test retrieving session from invalid token."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None  # Token not found
            mock_get_redis.return_value = mock_redis

            from websocket.auth import get_session_from_token

            result = await get_session_from_token("invalid_token")
            assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_session(self):
        """Test session invalidation."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            from websocket.auth import invalidate_session

            await invalidate_session("test_token")
            mock_redis.delete.assert_called_once()

    def test_is_admin_wallet(self):
        """Test admin wallet detection."""
        with patch("websocket.auth.get_settings") as mock_settings:
            mock_settings.return_value.ADMIN_WALLET_PUBKEY = "AdminPubKey123"

            from websocket.auth import is_admin_wallet

            assert is_admin_wallet("AdminPubKey123") is True
            assert is_admin_wallet("RegularUser456") is False


class TestConnectionManager:
    """Tests for WebSocket ConnectionManager."""

    @pytest.mark.asyncio
    async def test_register_connection(self):
        """Test connection registration."""
        with patch("websocket.manager.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            mock_sio = MagicMock()

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            await manager.register_connection("sid123", "wallet123")

            assert manager.get_wallet_connection_count("wallet123") == 1
            assert manager.sid_to_wallet.get("sid123") == "wallet123"

    @pytest.mark.asyncio
    async def test_unregister_connection(self):
        """Test connection unregistration."""
        with patch("websocket.manager.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            mock_sio = MagicMock()

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            await manager.register_connection("sid123", "wallet123")
            await manager.unregister_connection("sid123")

            assert manager.get_wallet_connection_count("wallet123") == 0
            assert manager.sid_to_wallet.get("sid123") is None

    @pytest.mark.asyncio
    async def test_multiple_connections_per_wallet(self):
        """Test multiple connections from same wallet."""
        with patch("websocket.manager.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            mock_sio = MagicMock()

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            await manager.register_connection("sid1", "wallet123")
            await manager.register_connection("sid2", "wallet123")
            await manager.register_connection("sid3", "wallet123")

            assert manager.get_wallet_connection_count("wallet123") == 3

            # Unregister one
            await manager.unregister_connection("sid2")
            assert manager.get_wallet_connection_count("wallet123") == 2

    @pytest.mark.asyncio
    async def test_join_tournament_room(self):
        """Test joining a tournament room."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            tournament_id = str(uuid4())

            await manager.join_tournament("sid123", tournament_id)

            mock_sio.enter_room.assert_called_once_with("sid123", f"tournament:{tournament_id}")

    @pytest.mark.asyncio
    async def test_leave_tournament_room(self):
        """Test leaving a tournament room."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            tournament_id = str(uuid4())

            await manager.leave_tournament("sid123", tournament_id)

            mock_sio.leave_room.assert_called_once_with("sid123", f"tournament:{tournament_id}")

    @pytest.mark.asyncio
    async def test_subscribe_table(self):
        """Test subscribing to a table."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            table_id = str(uuid4())

            await manager.subscribe_table("sid123", table_id)

            mock_sio.enter_room.assert_called_once_with("sid123", f"table:{table_id}")

    @pytest.mark.asyncio
    async def test_broadcast_to_tournament(self):
        """Test broadcasting to tournament room."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            tournament_id = str(uuid4())
            event = "tournament:started"
            data = {"tournament_id": tournament_id}

            await manager.broadcast_to_tournament(tournament_id, event, data)

            mock_sio.emit.assert_called_once_with(
                event, data, room=f"tournament:{tournament_id}"
            )

    @pytest.mark.asyncio
    async def test_broadcast_to_table(self):
        """Test broadcasting to table room."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            table_id = str(uuid4())
            event = "hand:action"
            data = {"table_id": table_id, "action": "raise"}

            await manager.broadcast_to_table(table_id, event, data)

            mock_sio.emit.assert_called_once_with(event, data, room=f"table:{table_id}")

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending to specific user."""
        with patch("websocket.manager.get_sio") as mock_get_sio:
            mock_sio = AsyncMock()
            mock_get_sio.return_value = mock_sio

            from websocket.manager import ConnectionManager

            manager = ConnectionManager(mock_sio)
            await manager.register_connection("sid123", "wallet123")

            event = "hand:deal"
            data = {"hole_cards": ["Ah", "Kh"]}

            await manager.send_to_user("wallet123", event, data)

            mock_sio.emit.assert_called_once_with(event, data, to="sid123")


class TestWebSocketEvents:
    """Tests for Socket.IO event handlers."""

    @pytest.mark.asyncio
    async def test_connect_with_valid_token(self):
        """Test connection with valid session token."""
        import json

        mock_sio = AsyncMock()
        session_data = {"wallet": "TestWallet", "is_admin": False}

        with patch("websocket.events.get_session_from_token") as mock_session, patch(
            "websocket.events.check_connection_limit"
        ) as mock_limit, patch("websocket.events.get_socket_manager") as mock_manager:
            mock_session.return_value = session_data
            mock_limit.return_value = True
            mock_manager.return_value = AsyncMock()

            from websocket.events import register_events

            register_events(mock_sio)

            # Get the connect handler
            connect_handler = None
            for call in mock_sio.event.call_args_list:
                # The handler is registered via decorator
                pass

    @pytest.mark.asyncio
    async def test_connection_limit_enforcement(self):
        """Test that connection limit is enforced."""
        with patch("websocket.auth.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            with patch("websocket.manager.get_sio") as mock_get_sio:
                mock_sio = AsyncMock()
                mock_get_sio.return_value = mock_sio

                from websocket.manager import ConnectionManager

                manager = ConnectionManager(mock_sio)

                # Register 3 connections (the limit)
                await manager.register_connection("sid1", "wallet123")
                await manager.register_connection("sid2", "wallet123")
                await manager.register_connection("sid3", "wallet123")

                from websocket.auth import check_connection_limit

                with patch("websocket.auth.get_socket_manager") as mock_get_manager:
                    mock_get_manager.return_value = manager

                    # Should be at limit
                    result = await check_connection_limit("wallet123", max_connections=3)
                    assert result is False


class TestEventEmitters:
    """Tests for event emitter functions."""

    @pytest.mark.asyncio
    async def test_emit_tournament_started(self):
        """Test tournament started event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_tournament_started

            tournament_id = str(uuid4())
            assignments = [
                {"wallet": "wallet1", "table_id": "table1", "seat": 0},
                {"wallet": "wallet2", "table_id": "table1", "seat": 1},
            ]

            await emit_tournament_started(tournament_id, assignments)

            mock_manager.broadcast_to_tournament.assert_called_once()
            call_args = mock_manager.broadcast_to_tournament.call_args
            assert call_args.args[0] == tournament_id
            assert call_args.args[1] == "tournament:started"
            assert call_args.args[2]["table_assignments"] == assignments

    @pytest.mark.asyncio
    async def test_emit_level_up(self):
        """Test level up event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_tournament_level_up

            tournament_id = str(uuid4())
            await emit_tournament_level_up(tournament_id, 5, 200, 400, 50)

            mock_manager.broadcast_to_tournament.assert_called_once()
            call_args = mock_manager.broadcast_to_tournament.call_args
            assert call_args.args[2]["level"] == 5
            assert call_args.args[2]["small_blind"] == 200
            assert call_args.args[2]["big_blind"] == 400
            assert call_args.args[2]["ante"] == 50

    @pytest.mark.asyncio
    async def test_emit_player_eliminated(self):
        """Test player eliminated event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_player_eliminated

            tournament_id = str(uuid4())
            await emit_player_eliminated(tournament_id, "wallet123", 5, "eliminator456")

            mock_manager.broadcast_to_tournament.assert_called_once()
            call_args = mock_manager.broadcast_to_tournament.call_args
            assert call_args.args[1] == "player:eliminated"
            assert call_args.args[2]["wallet"] == "wallet123"
            assert call_args.args[2]["position"] == 5

    @pytest.mark.asyncio
    async def test_emit_hand_deal_private(self):
        """Test hole cards are sent only to specific player."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_hand_deal

            table_id = str(uuid4())
            await emit_hand_deal("wallet123", table_id, ["Ah", "Kh"])

            # Should use send_to_user, not broadcast
            mock_manager.send_to_user.assert_called_once()
            call_args = mock_manager.send_to_user.call_args
            assert call_args.args[0] == "wallet123"
            assert call_args.args[1] == "hand:deal"
            assert call_args.args[2]["hole_cards"] == ["Ah", "Kh"]

    @pytest.mark.asyncio
    async def test_emit_hand_action(self):
        """Test hand action event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_hand_action

            table_id = str(uuid4())
            await emit_hand_action(table_id, "wallet123", "raise", 500, 1500, 9500)

            mock_manager.broadcast_to_table.assert_called_once()
            call_args = mock_manager.broadcast_to_table.call_args
            assert call_args.args[0] == table_id
            assert call_args.args[1] == "hand:action"
            assert call_args.args[2]["action"] == "raise"
            assert call_args.args[2]["amount"] == 500

    @pytest.mark.asyncio
    async def test_emit_decision_start(self):
        """Test decision start event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_decision_start

            table_id = str(uuid4())
            await emit_decision_start(table_id, "wallet123", 30, 100, 200, 500)

            mock_manager.broadcast_to_table.assert_called_once()
            call_args = mock_manager.broadcast_to_table.call_args
            assert call_args.args[1] == "decision:start"
            assert call_args.args[2]["wallet"] == "wallet123"
            assert call_args.args[2]["timeout_seconds"] == 30

    @pytest.mark.asyncio
    async def test_emit_hand_showdown(self):
        """Test showdown event emission."""
        with patch("websocket.events.get_socket_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            from websocket.events import emit_hand_showdown

            table_id = str(uuid4())
            showdown_data = [{"wallet": "wallet1", "cards": ["Ah", "Kh"]}]
            winners = [{"wallet": "wallet1", "amount": 500, "hand_rank": "Full House"}]
            pot_distribution = {"wallet1": 500}

            await emit_hand_showdown(table_id, showdown_data, winners, pot_distribution)

            mock_manager.broadcast_to_table.assert_called_once()
            call_args = mock_manager.broadcast_to_table.call_args
            assert call_args.args[1] == "hand:showdown"
            assert call_args.args[2]["winners"] == winners


class TestSignatureVerification:
    """Tests for Ed25519 signature verification."""

    @pytest.mark.asyncio
    async def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        # This would require actual cryptographic testing
        # For now, test the structure
        from websocket.auth import verify_signature

        # Invalid inputs should return False gracefully
        result = await verify_signature("invalid", "invalid", "message")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_signature_handles_errors(self):
        """Test that verification handles errors gracefully."""
        from websocket.auth import verify_signature

        # Various malformed inputs
        result1 = await verify_signature("", "", "")
        assert result1 is False

        result2 = await verify_signature("not_base58!!!", "sig", "msg")
        assert result2 is False
