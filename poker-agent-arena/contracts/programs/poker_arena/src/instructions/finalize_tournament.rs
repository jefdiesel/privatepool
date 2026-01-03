use anchor_lang::prelude::*;

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, Tournament, TournamentStatus};

/// Accounts required for finalizing a tournament.
#[derive(Accounts)]
pub struct FinalizeTournament<'info> {
    /// Admin wallet - must match arena_config.admin
    pub admin: Signer<'info>,

    /// Arena config for admin verification
    #[account(
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament to finalize - must be InProgress
    #[account(
        mut,
        seeds = [Tournament::SEED_PREFIX, &tournament.id.to_le_bytes()],
        bump = tournament.bump,
        constraint = tournament.status == TournamentStatus::InProgress @ ArenaError::TournamentNotInProgress
    )]
    pub tournament: Account<'info, Tournament>,
}

/// Finalize a tournament (admin only).
///
/// This instruction:
/// 1. Validates the tournament is in InProgress status
/// 2. Stores the results hash (SHA-256 of final standings JSON)
/// 3. Records the winner's wallet address
/// 4. Updates status to Completed with timestamp
///
/// # Arguments
/// * `results_hash` - SHA-256 hash of the final standings JSON
/// * `winner` - Winner's wallet address (1st place)
pub fn handler(
    ctx: Context<FinalizeTournament>,
    results_hash: [u8; 32],
    winner: Pubkey,
) -> Result<()> {
    let tournament = &mut ctx.accounts.tournament;
    let clock = Clock::get()?;

    // Update tournament with final results
    tournament.results_hash = Some(results_hash);
    tournament.winner = Some(winner);
    tournament.status = TournamentStatus::Completed;
    tournament.completed_at = Some(clock.unix_timestamp);

    msg!("Tournament {} finalized", tournament.id);
    msg!("Winner: {}", winner);
    msg!("Completed at: {}", clock.unix_timestamp);

    Ok(())
}
