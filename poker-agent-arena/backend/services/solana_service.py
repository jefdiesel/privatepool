"""Solana service for blockchain interactions."""

from __future__ import annotations

import hashlib
from typing import Any

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

# Global Solana client
_solana_client: AsyncClient | None = None


async def init_solana(rpc_url: str) -> None:
    """Initialize Solana RPC connection."""
    global _solana_client

    _solana_client = AsyncClient(rpc_url)


async def close_solana() -> None:
    """Close Solana RPC connection."""
    global _solana_client

    if _solana_client:
        await _solana_client.close()
        _solana_client = None


def get_solana() -> AsyncClient:
    """Get Solana client for dependency injection."""
    if _solana_client is None:
        raise RuntimeError("Solana client not initialized")
    return _solana_client


async def check_solana_connection() -> bool:
    """Check if Solana RPC connection is healthy."""
    if _solana_client is None:
        return False

    try:
        result = await _solana_client.is_connected()
        return result
    except Exception:
        return False


class SolanaService:
    """High-level Solana operations for the poker arena."""

    def __init__(self, client: AsyncClient, program_id: str):
        self.client = client
        self.program_id = Pubkey.from_string(program_id)

    # PDA Derivation

    def get_arena_config_pda(self) -> tuple[Pubkey, int]:
        """Derive arena config PDA."""
        return Pubkey.find_program_address(
            [b"arena_config"],
            self.program_id,
        )

    def get_tournament_pda(self, tournament_id: int) -> tuple[Pubkey, int]:
        """Derive tournament PDA."""
        return Pubkey.find_program_address(
            [b"tournament", tournament_id.to_bytes(8, "little")],
            self.program_id,
        )

    def get_registration_pda(
        self,
        tournament_pubkey: Pubkey,
        wallet_pubkey: Pubkey,
    ) -> tuple[Pubkey, int]:
        """Derive player registration PDA."""
        return Pubkey.find_program_address(
            [b"registration", bytes(tournament_pubkey), bytes(wallet_pubkey)],
            self.program_id,
        )

    def get_player_stats_pda(self, wallet_pubkey: Pubkey) -> tuple[Pubkey, int]:
        """Derive player stats PDA."""
        return Pubkey.find_program_address(
            [b"player_stats", bytes(wallet_pubkey)],
            self.program_id,
        )

    def get_points_mint_authority_pda(self) -> tuple[Pubkey, int]:
        """Derive points mint authority PDA."""
        return Pubkey.find_program_address(
            [b"points_mint_authority"],
            self.program_id,
        )

    # Account Fetching

    async def get_slot(self) -> int:
        """Get current slot number."""
        result = await self.client.get_slot()
        return result.value

    async def get_blockhash(self, slot: int | None = None) -> bytes:
        """Get blockhash for a slot (or latest if not specified)."""
        if slot:
            result = await self.client.get_block(slot)
            if result.value and result.value.blockhash:
                return bytes(result.value.blockhash)
            raise ValueError(f"Could not get blockhash for slot {slot}")
        else:
            result = await self.client.get_latest_blockhash()
            return bytes(result.value.blockhash)

    async def get_account_info(self, pubkey: Pubkey) -> bytes | None:
        """Get account data for a pubkey."""
        result = await self.client.get_account_info(pubkey)
        if result.value:
            return result.value.data
        return None

    async def get_balance(self, pubkey: Pubkey) -> int:
        """Get SOL balance in lamports."""
        result = await self.client.get_balance(pubkey)
        return result.value

    # Transaction Helpers

    async def confirm_transaction(self, signature: str, max_retries: int = 30) -> bool:
        """Confirm a transaction with retries."""
        import asyncio

        for _ in range(max_retries):
            result = await self.client.get_signature_statuses([signature])
            if result.value and result.value[0]:
                status = result.value[0]
                if status.confirmation_status in ["confirmed", "finalized"]:
                    return True
                if status.err:
                    return False
            await asyncio.sleep(1)

        return False

    # Transaction Builders for Phase 5

    async def send_and_confirm_tx(
        self,
        transaction: Transaction,
        signers: list[Keypair],
    ) -> str:
        """Submit transaction and wait for confirmation."""
        result = await self.client.send_transaction(
            transaction,
            *signers,
            opts={"skip_preflight": False, "preflight_commitment": Confirmed},
        )
        signature = str(result.value)

        confirmed = await self.confirm_transaction(signature)
        if not confirmed:
            raise RuntimeError(f"Transaction {signature} failed to confirm")

        return signature

    def build_start_tournament_ix(
        self,
        admin: Pubkey,
        tournament_id: int,
    ) -> Instruction:
        """Build StartTournament instruction.

        Accounts:
        - admin: Signer
        - arena_config: PDA
        - tournament: PDA
        - recent_slothashes: Sysvar
        """
        arena_config_pda, _ = self.get_arena_config_pda()
        tournament_pda, _ = self.get_tournament_pda(tournament_id)

        # SlotHashes sysvar address
        slot_hashes_sysvar = Pubkey.from_string(
            "SysvarS1otHashes111111111111111111111111111"
        )

        # Anchor discriminator for start_tournament
        discriminator = hashlib.sha256(b"global:start_tournament").digest()[:8]

        accounts = [
            AccountMeta(pubkey=admin, is_signer=True, is_writable=False),
            AccountMeta(pubkey=arena_config_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=tournament_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=slot_hashes_sysvar, is_signer=False, is_writable=False),
        ]

        return Instruction(
            program_id=self.program_id,
            accounts=accounts,
            data=discriminator,
        )

    def build_finalize_tournament_ix(
        self,
        admin: Pubkey,
        tournament_id: int,
        results_hash: bytes,
        winner: Pubkey,
    ) -> Instruction:
        """Build FinalizeTournament instruction.

        Accounts:
        - admin: Signer
        - arena_config: PDA
        - tournament: PDA

        Args:
        - results_hash: SHA-256 hash of final standings JSON (32 bytes)
        - winner: Winner's wallet address
        """
        arena_config_pda, _ = self.get_arena_config_pda()
        tournament_pda, _ = self.get_tournament_pda(tournament_id)

        # Anchor discriminator for finalize_tournament
        discriminator = hashlib.sha256(b"global:finalize_tournament").digest()[:8]

        # Serialize args: results_hash (32 bytes) + winner (32 bytes)
        data = discriminator + results_hash[:32] + bytes(winner)

        accounts = [
            AccountMeta(pubkey=admin, is_signer=True, is_writable=False),
            AccountMeta(pubkey=arena_config_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=tournament_pda, is_signer=False, is_writable=True),
        ]

        return Instruction(
            program_id=self.program_id,
            accounts=accounts,
            data=data,
        )

    def build_record_player_result_ix(
        self,
        admin: Pubkey,
        tournament_id: int,
        tournament_pubkey: Pubkey,
        player_wallet: Pubkey,
        final_rank: int,
        points_awarded: int,
        hands_played: int,
        eliminations: int,
    ) -> Instruction:
        """Build RecordPlayerResult instruction.

        Accounts:
        - admin: Signer, mut
        - arena_config: PDA
        - tournament: PDA
        - registration: PDA
        - player_stats: PDA (init_if_needed)
        - system_program

        Args:
        - final_rank: u16
        - points_awarded: u64
        - hands_played: u32
        - eliminations: u8
        """
        arena_config_pda, _ = self.get_arena_config_pda()
        tournament_pda, _ = self.get_tournament_pda(tournament_id)
        registration_pda, _ = self.get_registration_pda(tournament_pubkey, player_wallet)
        player_stats_pda, _ = self.get_player_stats_pda(player_wallet)

        system_program = Pubkey.from_string("11111111111111111111111111111111")

        # Anchor discriminator for record_player_result
        discriminator = hashlib.sha256(b"global:record_player_result").digest()[:8]

        # Serialize args
        data = (
            discriminator
            + final_rank.to_bytes(2, "little")
            + points_awarded.to_bytes(8, "little")
            + hands_played.to_bytes(4, "little")
            + eliminations.to_bytes(1, "little")
        )

        accounts = [
            AccountMeta(pubkey=admin, is_signer=True, is_writable=True),
            AccountMeta(pubkey=arena_config_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=tournament_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=registration_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=player_stats_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=system_program, is_signer=False, is_writable=False),
        ]

        return Instruction(
            program_id=self.program_id,
            accounts=accounts,
            data=data,
        )

    def build_distribute_points_ix(
        self,
        admin: Pubkey,
        tournament_id: int,
        tournament_pubkey: Pubkey,
        player_wallet: Pubkey,
        points_mint: Pubkey,
        player_token_account: Pubkey,
    ) -> Instruction:
        """Build DistributePoints instruction.

        Accounts:
        - admin: Signer
        - arena_config: PDA
        - tournament: PDA
        - registration: PDA
        - points_mint: Mint account
        - mint_authority: PDA
        - player_token_account: Token account
        - token_program
        """
        arena_config_pda, _ = self.get_arena_config_pda()
        tournament_pda, _ = self.get_tournament_pda(tournament_id)
        registration_pda, _ = self.get_registration_pda(tournament_pubkey, player_wallet)
        mint_authority_pda, _ = self.get_points_mint_authority_pda()

        token_program = Pubkey.from_string(
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        )

        # Anchor discriminator for distribute_points
        discriminator = hashlib.sha256(b"global:distribute_points").digest()[:8]

        accounts = [
            AccountMeta(pubkey=admin, is_signer=True, is_writable=False),
            AccountMeta(pubkey=arena_config_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=tournament_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=registration_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=points_mint, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint_authority_pda, is_signer=False, is_writable=False),
            AccountMeta(pubkey=player_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=token_program, is_signer=False, is_writable=False),
        ]

        return Instruction(
            program_id=self.program_id,
            accounts=accounts,
            data=discriminator,
        )
