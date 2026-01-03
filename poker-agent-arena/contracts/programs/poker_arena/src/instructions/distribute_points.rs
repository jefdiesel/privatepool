use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, MintTo, Token, TokenAccount};

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, PlayerRegistration, PointsMintAuthority, Tournament, TournamentStatus};

/// Accounts required for distributing POINTS tokens to a player.
#[derive(Accounts)]
pub struct DistributePoints<'info> {
    /// Admin wallet - must match arena_config.admin
    pub admin: Signer<'info>,

    /// Arena config for admin verification and points mint
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
        constraint = tournament.status == TournamentStatus::Completed @ ArenaError::TournamentNotCompleted
    )]
    pub tournament: Account<'info, Tournament>,

    /// Player's registration - must have points awarded
    #[account(
        mut,
        seeds = [PlayerRegistration::SEED_PREFIX, tournament.key().as_ref(), registration.wallet.as_ref()],
        bump = registration.bump,
        constraint = registration.tournament == tournament.key() @ ArenaError::TournamentNotFound,
        constraint = registration.points_awarded.is_some() @ ArenaError::NoPointsToDistribute,
        constraint = !registration.points_distributed @ ArenaError::PointsAlreadyDistributed
    )]
    pub registration: Account<'info, PlayerRegistration>,

    /// POINTS SPL token mint
    #[account(
        mut,
        constraint = points_mint.key() == arena_config.points_mint @ ArenaError::InvalidTierPayment
    )]
    pub points_mint: Account<'info, Mint>,

    /// PDA that holds mint authority
    #[account(
        seeds = [PointsMintAuthority::SEED_PREFIX],
        bump = mint_authority.bump
    )]
    pub mint_authority: Account<'info, PointsMintAuthority>,

    /// Player's token account for POINTS
    #[account(
        mut,
        constraint = player_token_account.mint == points_mint.key() @ ArenaError::InvalidTierPayment,
        constraint = player_token_account.owner == registration.wallet @ ArenaError::Unauthorized
    )]
    pub player_token_account: Account<'info, TokenAccount>,

    /// Token program
    pub token_program: Program<'info, Token>,
}

/// Distribute POINTS tokens to a tournament player (admin only).
///
/// This instruction:
/// 1. Validates the tournament is completed and player has points awarded
/// 2. Mints the awarded POINTS tokens to the player's token account
/// 3. Marks the registration as having received points
pub fn handler(ctx: Context<DistributePoints>) -> Result<()> {
    let registration = &mut ctx.accounts.registration;
    let points_to_mint = registration.points_awarded.unwrap();

    // Skip if no points to mint
    if points_to_mint == 0 {
        registration.points_distributed = true;
        msg!("No points to distribute for player: {}", registration.wallet);
        return Ok(());
    }

    // Build PDA signer seeds
    let seeds = &[
        PointsMintAuthority::SEED_PREFIX,
        &[ctx.accounts.mint_authority.bump],
    ];
    let signer_seeds = &[&seeds[..]];

    // Mint POINTS tokens to player
    token::mint_to(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.points_mint.to_account_info(),
                to: ctx.accounts.player_token_account.to_account_info(),
                authority: ctx.accounts.mint_authority.to_account_info(),
            },
            signer_seeds,
        ),
        points_to_mint,
    )?;

    // Mark as distributed
    registration.points_distributed = true;

    msg!(
        "Distributed {} POINTS to player: {}",
        points_to_mint,
        registration.wallet
    );

    Ok(())
}
