use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token};

use crate::errors::ArenaError;
use crate::state::{ArenaConfig, PointsMintAuthority};

/// Accounts required for creating the POINTS token mint.
#[derive(Accounts)]
pub struct CreatePointsMint<'info> {
    /// Admin wallet - must match arena_config.admin
    #[account(mut)]
    pub admin: Signer<'info>,

    /// Arena config for admin verification
    #[account(
        mut,
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump,
        constraint = arena_config.admin == admin.key() @ ArenaError::Unauthorized
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// The POINTS SPL token mint to be created
    #[account(
        init,
        payer = admin,
        mint::decimals = 9,
        mint::authority = mint_authority,
        mint::freeze_authority = mint_authority
    )]
    pub points_mint: Account<'info, Mint>,

    /// PDA that will hold mint authority
    #[account(
        init,
        payer = admin,
        space = PointsMintAuthority::SIZE,
        seeds = [PointsMintAuthority::SEED_PREFIX],
        bump
    )]
    pub mint_authority: Account<'info, PointsMintAuthority>,

    /// Token program
    pub token_program: Program<'info, Token>,

    /// System program for account creation
    pub system_program: Program<'info, System>,

    /// Rent sysvar
    pub rent: Sysvar<'info, Rent>,
}

/// Create the POINTS SPL token mint (admin only).
///
/// This instruction:
/// 1. Creates a new SPL token mint with 9 decimals
/// 2. Sets the mint authority to a program PDA
/// 3. Stores the mint address in arena_config
pub fn handler(ctx: Context<CreatePointsMint>) -> Result<()> {
    let arena_config = &mut ctx.accounts.arena_config;
    let mint_authority = &mut ctx.accounts.mint_authority;

    // Store the mint address in arena config
    arena_config.points_mint = ctx.accounts.points_mint.key();

    // Store the bump for future PDA derivation
    mint_authority.bump = ctx.bumps.mint_authority;

    msg!("POINTS mint created: {}", ctx.accounts.points_mint.key());
    msg!("Mint authority PDA: {}", ctx.accounts.mint_authority.key());

    Ok(())
}
