use anchor_lang::prelude::*;

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, PlayerRegistration, PlayerStats, Tournament, TournamentStatus};

/// Accounts required for recording a player's tournament result.
#[derive(Accounts)]
pub struct RecordPlayerResult<'info> {
    /// Admin wallet - must match arena_config.admin
    #[account(mut)]
    pub admin: Signer<'info>,

    /// Arena config for admin verification
    #[account(
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament - must be Completed
    #[account(
        seeds = [Tournament::SEED_PREFIX, &tournament.id.to_le_bytes()],
        bump = tournament.bump,
        constraint = tournament.status == TournamentStatus::Completed @ ArenaError::TournamentNotInProgress
    )]
    pub tournament: Account<'info, Tournament>,

    /// Player's registration for this tournament
    #[account(
        mut,
        seeds = [PlayerRegistration::SEED_PREFIX, tournament.key().as_ref(), registration.wallet.as_ref()],
        bump = registration.bump,
        constraint = registration.tournament == tournament.key() @ ArenaError::TournamentNotFound
    )]
    pub registration: Account<'info, PlayerRegistration>,

    /// Player's lifetime stats (created if doesn't exist)
    #[account(
        init_if_needed,
        payer = admin,
        space = PlayerStats::SIZE,
        seeds = [PlayerStats::SEED_PREFIX, registration.wallet.as_ref()],
        bump
    )]
    pub player_stats: Account<'info, PlayerStats>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Record a player's tournament result (admin only).
///
/// This instruction:
/// 1. Records the player's final rank, points, hands played, and eliminations
/// 2. Creates or updates the player's lifetime statistics
///
/// # Arguments
/// * `final_rank` - Player's finishing position (1 = winner)
/// * `points_awarded` - POINTS tokens to award
/// * `hands_played` - Number of hands the player participated in
/// * `eliminations` - Number of other players eliminated
pub fn handler(
    ctx: Context<RecordPlayerResult>,
    final_rank: u16,
    points_awarded: u64,
    hands_played: u32,
    eliminations: u8,
) -> Result<()> {
    let registration = &mut ctx.accounts.registration;
    let player_stats = &mut ctx.accounts.player_stats;
    let tournament = &ctx.accounts.tournament;

    // Check if result already recorded
    require!(
        registration.final_rank.is_none(),
        ArenaError::AlreadyRegistered
    );

    // Update registration with tournament result
    registration.final_rank = Some(final_rank);
    registration.points_awarded = Some(points_awarded);
    registration.hands_played = Some(hands_played);
    registration.eliminations = Some(eliminations);

    // Initialize or update player stats
    let is_new_stats = player_stats.wallet == Pubkey::default();

    if is_new_stats {
        // First time this player has stats recorded
        player_stats.wallet = registration.wallet;
        player_stats.tournaments_played = 1;
        player_stats.tournaments_won = if final_rank == 1 { 1 } else { 0 };
        player_stats.total_points = points_awarded;
        player_stats.best_finish = final_rank;
        player_stats.total_hands_played = hands_played as u64;
        player_stats.total_eliminations = eliminations as u32;
        player_stats.last_tournament = tournament.key();
        player_stats.last_played_at = Clock::get()?.unix_timestamp;
        player_stats.bump = ctx.bumps.player_stats;
    } else {
        // Update existing stats
        player_stats.tournaments_played = player_stats.tournaments_played.saturating_add(1);
        if final_rank == 1 {
            player_stats.tournaments_won = player_stats.tournaments_won.saturating_add(1);
        }
        player_stats.total_points = player_stats.total_points.saturating_add(points_awarded);
        if final_rank < player_stats.best_finish || player_stats.best_finish == 0 {
            player_stats.best_finish = final_rank;
        }
        player_stats.total_hands_played = player_stats.total_hands_played.saturating_add(hands_played as u64);
        player_stats.total_eliminations = player_stats.total_eliminations.saturating_add(eliminations as u32);
        player_stats.last_tournament = tournament.key();
        player_stats.last_played_at = Clock::get()?.unix_timestamp;
    }

    msg!("Recorded result for player: {}", registration.wallet);
    msg!("Rank: {}, Points: {}", final_rank, points_awarded);

    Ok(())
}
