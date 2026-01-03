"""WebSocket authentication middleware."""

from __future__ import annotations

import logging
import time
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from solders.pubkey import Pubkey

from config import get_settings
from services.redis_service import RedisService, get_redis

logger = logging.getLogger(__name__)

# Nonce expiry time in seconds
NONCE_EXPIRY = 300  # 5 minutes


async def generate_nonce(wallet: str) -> str:
    """Generate a nonce for wallet authentication."""
    import secrets

    nonce = secrets.token_hex(32)
    timestamp = int(time.time())
    nonce_data = f"{nonce}:{timestamp}"

    redis = get_redis()
    key = f"auth:nonce:{wallet}"
    await redis.set(key, nonce_data, ex=NONCE_EXPIRY)

    return nonce


async def verify_signature(wallet: str, signature: str, message: str) -> bool:
    """
    Verify an Ed25519 signature from a Solana wallet.

    Args:
        wallet: Base58-encoded public key
        signature: Base58-encoded signature
        message: The original message that was signed

    Returns:
        True if signature is valid, False otherwise
    """
    import base58

    try:
        # Decode wallet public key
        pubkey_bytes = base58.b58decode(wallet)
        verify_key = VerifyKey(pubkey_bytes)

        # Decode signature
        signature_bytes = base58.b58decode(signature)

        # Verify the signature
        message_bytes = message.encode("utf-8")
        verify_key.verify(message_bytes, signature_bytes)

        return True
    except (BadSignatureError, ValueError, Exception) as e:
        logger.warning(f"Signature verification failed for {wallet[:8]}...: {e}")
        return False


async def verify_nonce_signature(wallet: str, signature: str) -> bool:
    """
    Verify a signature against the stored nonce.

    Args:
        wallet: Base58-encoded public key
        signature: Base58-encoded signature

    Returns:
        True if valid, False otherwise
    """
    redis = get_redis()
    key = f"auth:nonce:{wallet}"

    # Get stored nonce
    nonce_data = await redis.get(key)
    if not nonce_data:
        logger.warning(f"No nonce found for wallet {wallet[:8]}...")
        return False

    nonce, timestamp_str = nonce_data.split(":")
    timestamp = int(timestamp_str)

    # Check if nonce is expired
    if time.time() - timestamp > NONCE_EXPIRY:
        await redis.delete(key)
        logger.warning(f"Nonce expired for wallet {wallet[:8]}...")
        return False

    # Build the message that was signed
    message = f"Sign this message to authenticate with Poker Agent Arena.\n\nNonce: {nonce}"

    # Verify signature
    is_valid = await verify_signature(wallet, signature, message)

    if is_valid:
        # Delete used nonce
        await redis.delete(key)

    return is_valid


async def check_connection_limit(wallet: str, max_connections: int = 3) -> bool:
    """
    Check if wallet is within connection limit.

    Args:
        wallet: Wallet address
        max_connections: Maximum allowed concurrent connections

    Returns:
        True if within limit, False otherwise
    """
    from websocket.manager import get_socket_manager

    manager = get_socket_manager()
    current_count = manager.get_wallet_connection_count(wallet)
    return current_count < max_connections


def is_admin_wallet(wallet: str) -> bool:
    """Check if a wallet is an admin wallet."""
    settings = get_settings()
    return wallet == settings.ADMIN_WALLET_PUBKEY


async def create_session_token(wallet: str) -> str:
    """
    Create a session token for authenticated user.

    Args:
        wallet: Authenticated wallet address

    Returns:
        Session token string
    """
    import hashlib
    import secrets

    # Generate token
    token = secrets.token_urlsafe(32)

    # Store in Redis with wallet mapping
    redis = get_redis()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    key = f"session:token:{token_hash}"

    session_data = {
        "wallet": wallet,
        "created_at": int(time.time()),
        "is_admin": is_admin_wallet(wallet),
    }

    import json

    await redis.set(key, json.dumps(session_data), ex=86400)  # 24 hour TTL

    return token


async def get_session_from_token(token: str) -> dict[str, Any] | None:
    """
    Get session data from a token.

    Args:
        token: Session token

    Returns:
        Session data dict or None if invalid
    """
    import hashlib
    import json

    redis = get_redis()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    key = f"session:token:{token_hash}"

    data = await redis.get(key)
    return json.loads(data) if data else None


async def invalidate_session(token: str) -> None:
    """Invalidate a session token."""
    import hashlib

    redis = get_redis()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    key = f"session:token:{token_hash}"
    await redis.delete(key)
