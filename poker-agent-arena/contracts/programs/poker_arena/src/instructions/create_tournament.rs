use anchor_lang::prelude::*;

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, Tournament, TournamentStatus};

/// Accounts required for creating a tournament.
#[derive(Accounts)]
pub struct CreateTournament<'info> {
    /// Admin wallet (must match arena config admin)
    #[account(mut)]
    pub admin: Signer<'info>,

    /// Arena config account
    #[account(
        mut,
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament PDA to be created
    #[account(
        init,
        payer = admin,
        space = Tournament::SIZE,
        seeds = [
            Tournament::SEED_PREFIX,
            (arena_config.tournament_count + 1).to_le_bytes().as_ref()
        ],
        bump
    )]
    pub tournament: Account<'info, Tournament>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Create a new tournament (admin only).
///
/// # Arguments
/// * `ctx` - The context containing all accounts
/// * `max_players` - Maximum number of players allowed (typically 27 or 54)
/// * `starting_stack` - Starting chip stack for each player
/// * `starts_at` - Unix timestamp when tournament is scheduled to start
/// * `blind_structure_hash` - SHA-256 hash of the blind structure JSON
/// * `payout_structure_hash` - SHA-256 hash of the admin-customized payout table
pub fn handler(
    ctx: Context<CreateTournament>,
    max_players: u16,
    starting_stack: u64,
    starts_at: i64,
    blind_structure_hash: [u8; 32],
    payout_structure_hash: [u8; 32],
) -> Result<()> {
    let arena_config = &mut ctx.accounts.arena_config;
    let tournament = &mut ctx.accounts.tournament;

    // Increment tournament count
    arena_config.tournament_count += 1;

    // Get current timestamp
    let clock = Clock::get()?;

    // Initialize tournament
    tournament.id = arena_config.tournament_count;
    tournament.admin = ctx.accounts.admin.key();
    tournament.status = TournamentStatus::Created;
    tournament.created_at = clock.unix_timestamp;
    tournament.starts_at = starts_at;
    tournament.completed_at = None;
    tournament.max_players = max_players;
    tournament.registered_players = 0;
    tournament.starting_stack = starting_stack;
    tournament.blind_structure_hash = blind_structure_hash;
    tournament.payout_structure_hash = payout_structure_hash;
    tournament.results_hash = None;
    tournament.winner = None;
    tournament.seed_slot = 0;
    tournament.seed_blockhash = [0u8; 32];
    tournament.bump = ctx.bumps.tournament;

    msg!(
        "Tournament {} created with {} max players",
        tournament.id,
        max_players
    );
    msg!("Starting stack: {}", starting_stack);
    msg!("Starts at: {}", starts_at);

    Ok(())
}
