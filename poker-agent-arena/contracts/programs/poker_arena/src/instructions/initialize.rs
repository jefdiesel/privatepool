use anchor_lang::prelude::*;

use crate::state::ArenaConfig;

/// Accounts required for initializing the arena.
#[derive(Accounts)]
pub struct Initialize<'info> {
    /// Admin wallet that will control the arena
    #[account(mut)]
    pub admin: Signer<'info>,

    /// Arena config PDA to be created
    #[account(
        init,
        payer = admin,
        space = ArenaConfig::SIZE,
        seeds = [ArenaConfig::SEED_PREFIX],
        bump
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Initialize the arena configuration (one-time setup).
///
/// # Arguments
/// * `ctx` - The context containing all accounts
/// * `treasury` - The treasury wallet for collecting fees
/// * `points_mint` - The SPL token mint for POINTS
pub fn handler(ctx: Context<Initialize>, treasury: Pubkey, points_mint: Pubkey) -> Result<()> {
    let arena_config = &mut ctx.accounts.arena_config;

    arena_config.admin = ctx.accounts.admin.key();
    arena_config.treasury = treasury;
    arena_config.points_mint = points_mint;
    arena_config.tournament_count = 0;
    arena_config.bump = ctx.bumps.arena_config;

    msg!("Arena initialized with admin: {}", arena_config.admin);
    msg!("Treasury: {}", treasury);
    msg!("Points mint: {}", points_mint);

    Ok(())
}
