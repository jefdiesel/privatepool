"""Decision logging for AI analytics.

Logs poker decisions for analysis without exposing sensitive information.
Designed for PostgreSQL storage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class DecisionLog:
    """Record of a single AI decision.

    IMPORTANT: Never log:
    - Full prompts (competitive advantage)
    - Hole cards at INFO level
    - Custom instructions
    """
    tournament_id: str
    hand_id: str
    wallet: str
    position: str
    betting_round: str
    action: str
    amount: Optional[int]
    pot_size: int
    to_call: int
    stack_size: int
    decision_time_ms: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_hit: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "tournament_id": self.tournament_id,
            "hand_id": self.hand_id,
            "wallet": self.wallet,
            "position": self.position,
            "betting_round": self.betting_round,
            "action": self.action,
            "amount": self.amount,
            "pot_size": self.pot_size,
            "to_call": self.to_call,
            "stack_size": self.stack_size,
            "decision_time_ms": self.decision_time_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_hit": self.cache_hit,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


class DecisionLogger:
    """Logs AI decisions for analytics.

    Supports batched writes for efficiency and optional
    database persistence.
    """

    def __init__(
        self,
        db=None,
        batch_size: int = 100,
        log_level: int = logging.INFO,
    ):
        """Initialize decision logger.

        Args:
            db: Optional database connection for persistence
            batch_size: Number of logs to batch before writing
            log_level: Python logging level
        """
        self.db = db
        self.batch_size = batch_size
        self.batch: List[DecisionLog] = []
        self.log_level = log_level

        # Configure logger
        self.logger = logging.getLogger(f"{__name__}.decisions")
        self.logger.setLevel(log_level)

    async def log_decision(self, decision: DecisionLog) -> None:
        """Log a decision.

        Args:
            decision: Decision record to log
        """
        # Log to standard logger (minimal info at INFO level)
        if self.log_level <= logging.INFO:
            self.logger.info(
                f"Decision: {decision.hand_id} | "
                f"{decision.position} | "
                f"{decision.action}"
                f"{f' {decision.amount}' if decision.amount else ''} | "
                f"{decision.decision_time_ms}ms"
            )

        # Debug logging includes more details
        if self.log_level <= logging.DEBUG:
            self.logger.debug(
                f"  Tokens: in={decision.input_tokens}, "
                f"out={decision.output_tokens}, "
                f"cache_read={decision.cache_read_tokens} | "
                f"Pot: {decision.pot_size}, To Call: {decision.to_call}"
            )

        # Add to batch
        self.batch.append(decision)

        # Flush if batch full
        if len(self.batch) >= self.batch_size:
            await self.flush()

    async def log_error(
        self,
        tournament_id: str,
        hand_id: str,
        wallet: str,
        error: str,
        decision_time_ms: int = 0,
    ) -> None:
        """Log a decision error.

        Args:
            tournament_id: Tournament identifier
            hand_id: Hand identifier
            wallet: Player wallet
            error: Error message
            decision_time_ms: Time spent before error
        """
        self.logger.error(
            f"Decision Error: {hand_id} | {wallet} | {error} | {decision_time_ms}ms"
        )

        # Create error log entry
        error_log = DecisionLog(
            tournament_id=tournament_id,
            hand_id=hand_id,
            wallet=wallet,
            position="",
            betting_round="",
            action="error",
            amount=None,
            pot_size=0,
            to_call=0,
            stack_size=0,
            decision_time_ms=decision_time_ms,
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
            cache_hit=False,
            error=error,
        )
        self.batch.append(error_log)

    async def flush(self) -> int:
        """Flush batched logs to database.

        Returns:
            Number of records flushed
        """
        if not self.batch:
            return 0

        count = len(self.batch)

        if self.db is not None:
            try:
                # Convert to dicts for insertion
                records = [log.to_dict() for log in self.batch]

                # Insert to database (implementation depends on db type)
                await self._insert_records(records)

                self.logger.debug(f"Flushed {count} decision logs to database")
            except Exception as e:
                self.logger.error(f"Failed to flush logs to database: {e}")
                # Don't lose logs on error - could write to file fallback
                return 0

        # Clear batch
        self.batch = []
        return count

    async def _insert_records(self, records: List[dict]) -> None:
        """Insert records to database.

        Override this method for specific database implementations.
        """
        if self.db is None:
            return

        # Example implementation for PostgreSQL with asyncpg:
        # async with self.db.pool.acquire() as conn:
        #     await conn.executemany(
        #         '''
        #         INSERT INTO decision_logs
        #         (tournament_id, hand_id, wallet, position, betting_round,
        #          action, amount, pot_size, to_call, stack_size,
        #          decision_time_ms, input_tokens, output_tokens,
        #          cache_read_tokens, cache_hit, timestamp, error)
        #         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        #                 $11, $12, $13, $14, $15, $16, $17)
        #         ''',
        #         [
        #             (r['tournament_id'], r['hand_id'], r['wallet'],
        #              r['position'], r['betting_round'], r['action'],
        #              r['amount'], r['pot_size'], r['to_call'],
        #              r['stack_size'], r['decision_time_ms'],
        #              r['input_tokens'], r['output_tokens'],
        #              r['cache_read_tokens'], r['cache_hit'],
        #              r['timestamp'], r['error'])
        #             for r in records
        #         ]
        #     )
        pass

    async def get_tournament_stats(self, tournament_id: str) -> dict:
        """Get aggregated stats for a tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            Dictionary with aggregated statistics
        """
        # Filter logs for this tournament
        tournament_logs = [
            log for log in self.batch
            if log.tournament_id == tournament_id
        ]

        if not tournament_logs:
            return {
                "total_decisions": 0,
                "avg_decision_time_ms": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "cache_hit_rate": 0,
                "errors": 0,
            }

        total = len(tournament_logs)
        errors = sum(1 for log in tournament_logs if log.error)
        cache_hits = sum(1 for log in tournament_logs if log.cache_hit)

        return {
            "total_decisions": total,
            "avg_decision_time_ms": sum(log.decision_time_ms for log in tournament_logs) / total,
            "total_input_tokens": sum(log.input_tokens for log in tournament_logs),
            "total_output_tokens": sum(log.output_tokens for log in tournament_logs),
            "cache_hit_rate": cache_hits / total if total > 0 else 0,
            "errors": errors,
        }
