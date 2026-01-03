use anchor_lang::prelude::*;
use anchor_lang::system_program;

use crate::errors::ArenaError;
use crate::state::{AgentTier, ArenaConfig, PlayerRegistration, Tournament};

/// Accounts required for player registration.
#[derive(Accounts)]
pub struct RegisterPlayer<'info> {
    /// Player wallet registering for the tournament
    #[account(mut)]
    pub player: Signer<'info>,

    /// Arena config account (for treasury address)
    #[account(
        seeds = [ArenaConfig::SEED_PREFIX],
        bump = arena_config.bump
    )]
    pub arena_config: Account<'info, ArenaConfig>,

    /// Tournament to register for
    #[account(
        mut,
        seeds = [
            Tournament::SEED_PREFIX,
            tournament.id.to_le_bytes().as_ref()
        ],
        bump = tournament.bump,
        constraint = tournament.is_registration_open() @ ArenaError::RegistrationNotOpen,
        constraint = !tournament.is_full() @ ArenaError::TournamentFull
    )]
    pub tournament: Account<'info, Tournament>,

    /// Player registration PDA to be created
    #[account(
        init,
        payer = player,
        space = PlayerRegistration::SIZE,
        seeds = [
            PlayerRegistration::SEED_PREFIX,
            tournament.key().as_ref(),
            player.key().as_ref()
        ],
        bump
    )]
    pub registration: Account<'info, PlayerRegistration>,

    /// Treasury wallet to receive tier fees
    /// CHECK: This is verified against arena_config.treasury
    #[account(
        mut,
        constraint = treasury.key() == arena_config.treasury @ ArenaError::InvalidTierPayment
    )]
    pub treasury: AccountInfo<'info>,

    /// System program for account creation and transfers
    pub system_program: Program<'info, System>,
}

/// Register a player for a tournament.
///
/// # Arguments
/// * `ctx` - The context containing all accounts
/// * `tier` - The agent tier (FREE, BASIC, or PRO)
/// * `agent_prompt_hash` - SHA-256 hash of the custom prompt (for verification)
/// * `agent_name` - Display name for the agent (32 bytes, UTF-8)
/// * `agent_image_uri` - URI for agent avatar image (128 bytes)
pub fn handler(
    ctx: Context<RegisterPlayer>,
    tier: AgentTier,
    agent_prompt_hash: [u8; 32],
    agent_name: [u8; 32],
    agent_image_uri: [u8; 128],
) -> Result<()> {
    let tournament = &mut ctx.accounts.tournament;
    let registration = &mut ctx.accounts.registration;
    let player = &ctx.accounts.player;
    let treasury = &ctx.accounts.treasury;

    // Get tier cost
    let tier_cost = tier.cost_lamports();

    // Transfer tier fee to treasury (if not FREE)
    if tier_cost > 0 {
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: player.to_account_info(),
                    to: treasury.to_account_info(),
                },
            ),
            tier_cost,
        )?;
    }

    // Get current timestamp
    let clock = Clock::get()?;

    // Initialize registration
    registration.tournament = tournament.key();
    registration.wallet = player.key();
    registration.tier = tier;
    registration.registered_at = clock.unix_timestamp;
    registration.agent_prompt_hash = agent_prompt_hash;
    registration.agent_name = agent_name;
    registration.agent_image_uri = agent_image_uri;
    registration.final_rank = None;
    registration.points_awarded = None;
    registration.hands_played = None;
    registration.eliminations = None;
    registration.points_distributed = false;
    registration.bump = ctx.bumps.registration;

    // Increment registered players count
    tournament.registered_players += 1;

    msg!(
        "Player {} registered for tournament {} with {:?} tier",
        player.key(),
        tournament.id,
        tier
    );
    msg!(
        "Registered players: {}/{}",
        tournament.registered_players,
        tournament.max_players
    );

    Ok(())
}
