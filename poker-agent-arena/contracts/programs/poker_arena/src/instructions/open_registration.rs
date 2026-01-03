use anchor_lang::prelude::*;

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, Tournament, TournamentStatus};

/// Accounts required for opening tournament registration.
#[derive(Accounts)]
pub struct OpenRegistration<'info> {
    /// Admin wallet (must match arena config admin)
    pub admin: Signer<'info>,

    /// Arena config account (for admin verification)
    #[account(
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament to open registration for
    #[account(
        mut,
        seeds = [
            Tournament::SEED_PREFIX,
            tournament.id.to_le_bytes().as_ref()
        ],
        bump = tournament.bump,
        constraint = tournament.status == TournamentStatus::Created @ ArenaError::TournamentAlreadyStarted
    )]
    pub tournament: Account<'info, Tournament>,
}

/// Open registration for a tournament (admin only).
/// Changes tournament status from Created to Registration.
pub fn handler(ctx: Context<OpenRegistration>) -> Result<()> {
    let tournament = &mut ctx.accounts.tournament;

    // Update status to Registration
    tournament.status = TournamentStatus::Registration;

    msg!(
        "Registration opened for tournament {}",
        tournament.id
    );

    Ok(())
}
