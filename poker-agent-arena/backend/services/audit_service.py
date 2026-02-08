"""Audit logging service for security-relevant events.

Logs important events for security monitoring and compliance:
- Authentication attempts
- Tier upgrades
- Admin actions
- Tournament finalizations
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.logging import get_correlation_id

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication
    AUTH_ATTEMPT = "auth.attempt"
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    SESSION_CREATED = "session.created"
    SESSION_EXPIRED = "session.expired"

    # Agent Management
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    TIER_UPGRADED = "tier.upgraded"
    PROMPT_UPDATED = "prompt.updated"

    # Tournament
    TOURNAMENT_CREATED = "tournament.created"
    TOURNAMENT_STARTED = "tournament.started"
    TOURNAMENT_FINALIZED = "tournament.finalized"
    TOURNAMENT_CANCELLED = "tournament.cancelled"
    REGISTRATION_CREATED = "registration.created"
    REGISTRATION_CANCELLED = "registration.cancelled"

    # Admin
    ADMIN_ACTION = "admin.action"
    SETTINGS_CHANGED = "settings.changed"
    USER_BANNED = "user.banned"
    USER_UNBANNED = "user.unbanned"

    # Financial
    POINTS_DISTRIBUTED = "points.distributed"
    PAYMENT_RECEIVED = "payment.received"
    REFUND_ISSUED = "refund.issued"

    # Security
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    ACCESS_DENIED = "security.access_denied"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit log event."""

    event_type: AuditEventType
    actor: str  # Wallet address or system identifier
    resource: str  # Resource being acted upon (e.g., tournament_id)
    action: str  # Human-readable action description
    severity: AuditSeverity = AuditSeverity.INFO
    metadata: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "correlation_id": self.correlation_id or get_correlation_id(),
        }


class AuditService:
    """Service for logging audit events."""

    def __init__(self, store_to_db: bool = True):
        """Initialize audit service.

        Args:
            store_to_db: Whether to persist events to database
        """
        self.store_to_db = store_to_db

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: Audit event to log
        """
        event_dict = event.to_dict()

        # Always log to structured logger
        log_func = getattr(logger, event.severity.value, logger.info)
        log_func(json.dumps(event_dict))

        # Optionally store to database
        if self.store_to_db:
            await self._store_to_db(event)

    async def _store_to_db(self, event: AuditEvent) -> None:
        """Store audit event to database.

        Args:
            event: Event to store
        """
        # This would insert into an audit_logs table
        # For now, just log - actual DB storage would be implemented
        # when the audit_logs migration is run
        pass

    # Convenience methods for common events

    async def log_auth_attempt(
        self,
        wallet: str,
        success: bool,
        ip_address: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        """Log authentication attempt."""
        event_type = AuditEventType.AUTH_SUCCESS if success else AuditEventType.AUTH_FAILURE
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        await self.log(
            AuditEvent(
                event_type=event_type,
                actor=wallet,
                resource="auth",
                action=f"Authentication {'successful' if success else 'failed'}",
                severity=severity,
                metadata={"failure_reason": failure_reason} if failure_reason else {},
                ip_address=ip_address,
            )
        )

    async def log_tier_upgrade(
        self,
        wallet: str,
        old_tier: str,
        new_tier: str,
        transaction_signature: str | None = None,
    ) -> None:
        """Log tier upgrade."""
        await self.log(
            AuditEvent(
                event_type=AuditEventType.TIER_UPGRADED,
                actor=wallet,
                resource="agent",
                action=f"Upgraded from {old_tier} to {new_tier}",
                metadata={
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "transaction": transaction_signature,
                },
            )
        )

    async def log_admin_action(
        self,
        admin_wallet: str,
        action: str,
        resource: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log admin action."""
        await self.log(
            AuditEvent(
                event_type=AuditEventType.ADMIN_ACTION,
                actor=admin_wallet,
                resource=f"{resource}:{resource_id}",
                action=action,
                severity=AuditSeverity.WARNING,
                metadata=metadata or {},
            )
        )

    async def log_tournament_finalized(
        self,
        tournament_id: str,
        admin_wallet: str,
        winner_wallet: str,
        total_players: int,
        total_points_distributed: int,
    ) -> None:
        """Log tournament finalization."""
        await self.log(
            AuditEvent(
                event_type=AuditEventType.TOURNAMENT_FINALIZED,
                actor=admin_wallet,
                resource=f"tournament:{tournament_id}",
                action="Tournament finalized",
                metadata={
                    "winner": winner_wallet,
                    "total_players": total_players,
                    "total_points": total_points_distributed,
                },
            )
        )

    async def log_points_distributed(
        self,
        tournament_id: str,
        wallet: str,
        points: int,
        rank: int,
    ) -> None:
        """Log points distribution."""
        await self.log(
            AuditEvent(
                event_type=AuditEventType.POINTS_DISTRIBUTED,
                actor="system",
                resource=f"wallet:{wallet}",
                action=f"Distributed {points} POINTS for rank {rank}",
                metadata={
                    "tournament_id": tournament_id,
                    "points": points,
                    "rank": rank,
                },
            )
        )

    async def log_security_event(
        self,
        event_type: AuditEventType,
        actor: str,
        description: str,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log security-related event."""
        await self.log(
            AuditEvent(
                event_type=event_type,
                actor=actor,
                resource="security",
                action=description,
                severity=AuditSeverity.WARNING,
                ip_address=ip_address,
                metadata=metadata or {},
            )
        )


# Global audit service instance
_audit_service: AuditService | None = None


def get_audit_service() -> AuditService:
    """Get global audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
