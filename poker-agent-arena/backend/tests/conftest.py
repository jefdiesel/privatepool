"""Pytest configuration and fixtures."""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from main import app


@pytest.fixture
def client():
    """Create test client with mocked services."""
    # Mock the lifespan context manager
    with patch("main.init_db", new_callable=AsyncMock), \
         patch("main.init_redis", new_callable=AsyncMock), \
         patch("main.init_solana", new_callable=AsyncMock), \
         patch("main.close_db", new_callable=AsyncMock), \
         patch("main.close_redis", new_callable=AsyncMock), \
         patch("main.close_solana", new_callable=AsyncMock):
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.check_rate_limit.return_value = True
    return mock


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock = AsyncMock()
    mock.execute.return_value.fetchone.return_value = None
    mock.execute.return_value.fetchall.return_value = []
    mock.execute.return_value.scalar.return_value = None
    return mock


@pytest.fixture
def sample_tournament():
    """Create a sample tournament data structure."""
    return {
        "id": str(uuid4()),
        "on_chain_id": 12345,
        "status": "registration",
        "max_players": 27,
        "starting_stack": 10000,
        "registered_players": 5,
        "blind_structure": {
            "name": "standard",
            "levels": [
                {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 12},
                {"level": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 12},
            ],
        },
        "payout_structure": [
            {"rank": 1, "points": 5000},
            {"rank": 2, "points": 3000},
            {"rank": 3, "points": 2000},
        ],
        "starts_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "registration_opens_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "winner_wallet": None,
        "results_hash": None,
    }


@pytest.fixture
def sample_user_session():
    """Create a sample user session."""
    return {
        "wallet": "TestWallet123abc456def",
        "is_admin": False,
        "created_at": int(datetime.utcnow().timestamp()),
    }


@pytest.fixture
def sample_admin_session():
    """Create a sample admin session."""
    return {
        "wallet": "AdminWallet789xyz",
        "is_admin": True,
        "created_at": int(datetime.utcnow().timestamp()),
    }


@pytest.fixture
def sample_table_state():
    """Create a sample table state for WebSocket events."""
    return {
        "table_id": str(uuid4()),
        "tournament_id": str(uuid4()),
        "seats": [
            {
                "position": i,
                "wallet": f"wallet{i}" if i < 5 else None,
                "agent_name": f"Agent{i}" if i < 5 else None,
                "agent_image": None,
                "stack": 10000 if i < 5 else 0,
                "current_bet": 0,
                "status": "active" if i < 5 else "empty",
                "hole_cards": None,
            }
            for i in range(9)
        ],
        "pot": 75,
        "community_cards": [],
        "betting_round": "preflop",
        "button_position": 0,
        "current_position": 2,
    }


@pytest.fixture
def mock_socket_manager():
    """Create a mock Socket.IO manager."""
    mock = AsyncMock()
    mock.broadcast_to_tournament = AsyncMock()
    mock.broadcast_to_table = AsyncMock()
    mock.send_to_user = AsyncMock()
    mock.send_to_sid = AsyncMock()
    mock.join_tournament = AsyncMock()
    mock.leave_tournament = AsyncMock()
    mock.subscribe_table = AsyncMock()
    mock.unsubscribe_table = AsyncMock()
    mock.register_connection = AsyncMock()
    mock.unregister_connection = AsyncMock()
    mock.get_wallet_connection_count = MagicMock(return_value=0)
    mock.get_room_count = AsyncMock(return_value=0)
    # Track wallet mappings
    mock.wallet_to_sid = {}
    mock.sid_to_wallet = {}
    return mock
