"""Finalization service for on-chain tournament settlement."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from services.solana_service import SolanaService

logger = logging.getLogger(__name__)


class FinalizationService:
    """Handles on-chain settlement of tournament results."""

    def __init__(
        self,
        solana_service: SolanaService,
        admin_keypair: Keypair,
        points_mint: Pubkey,
    ):
        self.solana = solana_service
        self.admin_keypair = admin_keypair
        self.admin_pubkey = admin_keypair.pubkey()
        self.points_mint = points_mint

    async def generate_results_hash(
        self,
        db: AsyncSession,
        tournament_id: UUID,
    ) -> tuple[bytes, dict[str, Any]]:
        """Generate SHA-256 hash of final tournament standings.

        Returns:
            Tuple of (hash_bytes, standings_dict)
        """
        # Fetch tournament and all registrations
        result = await db.execute(
            select("*")
            .select_from("tournaments")
            .where("id = :id", {"id": str(tournament_id)})
        )
        tournament = result.fetchone()

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        # Fetch registrations with results
        result = await db.execute(
            select("*")
            .select_from("registrations")
            .where("tournament_id = :tid", {"tid": str(tournament_id)})
            .order_by("final_rank")
        )
        registrations = result.fetchall()

        # Build standings JSON
        standings = {
            "tournament_id": str(tournament_id),
            "on_chain_id": tournament.on_chain_id,
            "completed_at": tournament.completed_at.isoformat() if tournament.completed_at else None,
            "players": [
                {
                    "wallet": reg.wallet,
                    "final_rank": reg.final_rank,
                    "points_awarded": reg.points_awarded,
                    "hands_played": reg.hands_played,
                    "eliminations": reg.eliminations,
                }
                for reg in registrations
                if reg.final_rank is not None
            ],
        }

        # Generate deterministic JSON and hash
        standings_json = json.dumps(standings, sort_keys=True, separators=(",", ":"))
        results_hash = hashlib.sha256(standings_json.encode()).digest()

        return results_hash, standings

    async def finalize_tournament_on_chain(
        self,
        db: AsyncSession,
        tournament_id: UUID,
    ) -> str:
        """Call FinalizeTournament instruction on-chain.

        Returns:
            Transaction signature
        """
        # Get tournament info
        result = await db.execute(
            select("*")
            .select_from("tournaments")
            .where("id = :id", {"id": str(tournament_id)})
        )
        tournament = result.fetchone()

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        if tournament.status != "in_progress":
            raise ValueError(f"Tournament {tournament_id} is not in progress")

        # Get winner wallet
        result = await db.execute(
            select("*")
            .select_from("registrations")
            .where("tournament_id = :tid AND final_rank = 1", {"tid": str(tournament_id)})
        )
        winner_reg = result.fetchone()

        if not winner_reg:
            raise ValueError(f"No winner found for tournament {tournament_id}")

        # Generate results hash
        results_hash, _ = await self.generate_results_hash(db, tournament_id)
        winner_pubkey = Pubkey.from_string(winner_reg.wallet)

        # Build instruction
        ix = self.solana.build_finalize_tournament_ix(
            admin=self.admin_pubkey,
            tournament_id=tournament.on_chain_id,
            results_hash=results_hash,
            winner=winner_pubkey,
        )

        # Build and send transaction
        recent_blockhash = await self.solana.get_blockhash()
        message = Message.new_with_blockhash(
            [ix],
            self.admin_pubkey,
            Hash.from_bytes(recent_blockhash),
        )
        tx = Transaction.new_unsigned(message)
        tx.sign([self.admin_keypair], Hash.from_bytes(recent_blockhash))

        signature = await self.solana.send_and_confirm_tx(tx, [self.admin_keypair])

        # Update database
        await db.execute(
            update("tournaments")
            .where("id = :id", {"id": str(tournament_id)})
            .values(
                status="completed",
                results_hash=results_hash,
                finalization_tx=signature,
                completed_at=datetime.now(timezone.utc),
            )
        )

        # Log audit entry
        await self._log_audit(
            db,
            tournament_id=tournament_id,
            action="finalize_tournament",
            wallet=winner_reg.wallet,
            tx_signature=signature,
            details={"results_hash": results_hash.hex()},
        )

        await db.commit()

        logger.info(f"Tournament {tournament_id} finalized: {signature}")
        return signature

    async def record_all_player_results(
        self,
        db: AsyncSession,
        tournament_id: UUID,
    ) -> list[str]:
        """Call RecordPlayerResult for each player in the tournament.

        Returns:
            List of transaction signatures
        """
        # Get tournament info
        result = await db.execute(
            select("*")
            .select_from("tournaments")
            .where("id = :id", {"id": str(tournament_id)})
        )
        tournament = result.fetchone()

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        tournament_pda, _ = self.solana.get_tournament_pda(tournament.on_chain_id)

        # Get all registrations with results
        result = await db.execute(
            select("*")
            .select_from("registrations")
            .where("tournament_id = :tid AND final_rank IS NOT NULL AND result_recorded_at IS NULL",
                   {"tid": str(tournament_id)})
        )
        registrations = result.fetchall()

        signatures = []

        for reg in registrations:
            try:
                player_wallet = Pubkey.from_string(reg.wallet)

                # Build instruction
                ix = self.solana.build_record_player_result_ix(
                    admin=self.admin_pubkey,
                    tournament_id=tournament.on_chain_id,
                    tournament_pubkey=tournament_pda,
                    player_wallet=player_wallet,
                    final_rank=reg.final_rank,
                    points_awarded=reg.points_awarded or 0,
                    hands_played=reg.hands_played or 0,
                    eliminations=reg.eliminations or 0,
                )

                # Build and send transaction
                recent_blockhash = await self.solana.get_blockhash()
                message = Message.new_with_blockhash(
                    [ix],
                    self.admin_pubkey,
                    Hash.from_bytes(recent_blockhash),
                )
                tx = Transaction.new_unsigned(message)
                tx.sign([self.admin_keypair], Hash.from_bytes(recent_blockhash))

                signature = await self.solana.send_and_confirm_tx(tx, [self.admin_keypair])
                signatures.append(signature)

                # Update registration
                await db.execute(
                    update("registrations")
                    .where("id = :id", {"id": str(reg.id)})
                    .values(
                        result_recorded_at=datetime.now(timezone.utc),
                        result_tx=signature,
                    )
                )

                # Log audit entry
                await self._log_audit(
                    db,
                    tournament_id=tournament_id,
                    action="record_player_result",
                    wallet=reg.wallet,
                    tx_signature=signature,
                    details={
                        "final_rank": reg.final_rank,
                        "points_awarded": reg.points_awarded,
                    },
                )

                logger.info(f"Recorded result for player {reg.wallet}: {signature}")

            except Exception as e:
                logger.error(f"Failed to record result for player {reg.wallet}: {e}")
                raise

        await db.commit()
        return signatures

    async def distribute_all_points(
        self,
        db: AsyncSession,
        tournament_id: UUID,
    ) -> list[str]:
        """Call DistributePoints for each player with points to distribute.

        Returns:
            List of transaction signatures
        """
        # Get tournament info
        result = await db.execute(
            select("*")
            .select_from("tournaments")
            .where("id = :id", {"id": str(tournament_id)})
        )
        tournament = result.fetchone()

        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        tournament_pda, _ = self.solana.get_tournament_pda(tournament.on_chain_id)

        # Get registrations with points to distribute
        result = await db.execute(
            select("*")
            .select_from("registrations")
            .where(
                "tournament_id = :tid AND points_awarded > 0 AND points_distributed_at IS NULL",
                {"tid": str(tournament_id)},
            )
        )
        registrations = result.fetchall()

        signatures = []

        for reg in registrations:
            try:
                player_wallet = Pubkey.from_string(reg.wallet)

                # Get or create player token account
                # NOTE: In production, you'd need to handle ATA creation
                player_token_account = self._get_associated_token_account(
                    player_wallet,
                    self.points_mint,
                )

                # Build instruction
                ix = self.solana.build_distribute_points_ix(
                    admin=self.admin_pubkey,
                    tournament_id=tournament.on_chain_id,
                    tournament_pubkey=tournament_pda,
                    player_wallet=player_wallet,
                    points_mint=self.points_mint,
                    player_token_account=player_token_account,
                )

                # Build and send transaction
                recent_blockhash = await self.solana.get_blockhash()
                message = Message.new_with_blockhash(
                    [ix],
                    self.admin_pubkey,
                    Hash.from_bytes(recent_blockhash),
                )
                tx = Transaction.new_unsigned(message)
                tx.sign([self.admin_keypair], Hash.from_bytes(recent_blockhash))

                signature = await self.solana.send_and_confirm_tx(tx, [self.admin_keypair])
                signatures.append(signature)

                # Update registration
                await db.execute(
                    update("registrations")
                    .where("id = :id", {"id": str(reg.id)})
                    .values(
                        points_distributed_at=datetime.now(timezone.utc),
                        distribution_tx=signature,
                    )
                )

                # Log audit entry
                await self._log_audit(
                    db,
                    tournament_id=tournament_id,
                    action="distribute_points",
                    wallet=reg.wallet,
                    tx_signature=signature,
                    details={"points_distributed": reg.points_awarded},
                )

                logger.info(f"Distributed {reg.points_awarded} POINTS to {reg.wallet}: {signature}")

            except Exception as e:
                logger.error(f"Failed to distribute points to {reg.wallet}: {e}")
                raise

        # Mark tournament as fully distributed
        all_distributed = await db.execute(
            select("COUNT(*)")
            .select_from("registrations")
            .where(
                "tournament_id = :tid AND points_awarded > 0 AND points_distributed_at IS NULL",
                {"tid": str(tournament_id)},
            )
        )
        remaining = all_distributed.scalar()

        if remaining == 0:
            await db.execute(
                update("tournaments")
                .where("id = :id", {"id": str(tournament_id)})
                .values(points_distributed=True)
            )

        await db.commit()
        return signatures

    def _get_associated_token_account(
        self,
        owner: Pubkey,
        mint: Pubkey,
    ) -> Pubkey:
        """Derive the associated token account address."""
        # Associated Token Account Program
        ata_program = Pubkey.from_string(
            "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
        )
        token_program = Pubkey.from_string(
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        )

        # Derive ATA address
        ata, _ = Pubkey.find_program_address(
            [bytes(owner), bytes(token_program), bytes(mint)],
            ata_program,
        )
        return ata

    async def _log_audit(
        self,
        db: AsyncSession,
        tournament_id: UUID,
        action: str,
        wallet: str | None,
        tx_signature: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log an audit entry."""
        await db.execute(
            """
            INSERT INTO audit_log (tournament_id, action, wallet, tx_signature, details)
            VALUES (:tournament_id, :action, :wallet, :tx_signature, :details)
            """,
            {
                "tournament_id": str(tournament_id),
                "action": action,
                "wallet": wallet,
                "tx_signature": tx_signature,
                "details": json.dumps(details) if details else None,
            },
        )
