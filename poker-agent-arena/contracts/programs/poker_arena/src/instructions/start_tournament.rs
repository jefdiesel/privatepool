use anchor_lang::prelude::*;

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, Tournament, TournamentStatus};

/// Accounts required for starting a tournament.
#[derive(Accounts)]
pub struct StartTournament<'info> {
    /// Admin wallet - must match arena_config.admin
    pub admin: Signer<'info>,

    /// Arena config for admin verification
    #[account(
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament to start - must be in Registration status
    #[account(
        mut,
        seeds = [Tournament::SEED_PREFIX, &tournament.id.to_le_bytes()],
        bump = tournament.bump,
        constraint = tournament.status == TournamentStatus::Registration @ ArenaError::RegistrationNotOpen,
        constraint = tournament.registered_players >= 2 @ ArenaError::TournamentNotStarted
    )]
    pub tournament: Account<'info, Tournament>,

    /// Recent slot hashes sysvar for provably fair RNG seed
    /// CHECK: This is the SlotHashes sysvar, validated by address
    #[account(address = anchor_lang::solana_program::sysvar::slot_hashes::id())]
    pub recent_slothashes: UncheckedAccount<'info>,
}

/// Start a tournament (admin only).
///
/// This instruction:
/// 1. Validates the tournament is in Registration status with >= 2 players
/// 2. Captures the current slot and recent blockhash for provably fair RNG
/// 3. Updates the tournament status to InProgress
pub fn handler(ctx: Context<StartTournament>) -> Result<()> {
    let tournament = &mut ctx.accounts.tournament;

    // Get current slot from Clock sysvar
    let clock = Clock::get()?;
    let current_slot = clock.slot;

    // Extract seed blockhash from recent slot hashes
    // The SlotHashes sysvar contains recent slot hashes we can use for randomness
    let slot_hashes_data = ctx.accounts.recent_slothashes.try_borrow_data()?;

    // SlotHashes structure: [count (8 bytes)][entries...]
    // Each entry: [slot (8 bytes)][hash (32 bytes)]
    // We'll use the most recent hash (first entry after count)
    let mut seed_blockhash = [0u8; 32];
    if slot_hashes_data.len() >= 48 {
        // Skip count (8 bytes), skip first slot (8 bytes), read hash (32 bytes)
        seed_blockhash.copy_from_slice(&slot_hashes_data[16..48]);
    }

    // Update tournament state
    tournament.seed_slot = current_slot;
    tournament.seed_blockhash = seed_blockhash;
    tournament.status = TournamentStatus::InProgress;

    msg!("Tournament {} started", tournament.id);
    msg!("Seed slot: {}", current_slot);
    msg!("Registered players: {}", tournament.registered_players);

    Ok(())
}
