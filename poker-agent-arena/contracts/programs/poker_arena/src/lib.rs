use anchor_lang::prelude::*;

pub mod errors;
pub mod instructions;
pub mod state;

use instructions::*;
use state::AgentTier;

declare_id!("E6tuNWDutZ7Npsb6UU6GmV5H4B3ucpAwzzGeqJzrUUJz");

#[program]
pub mod poker_arena {
    use super::*;

    /// Initialize the arena configuration (one-time setup).
    ///
    /// # Arguments
    /// * `ctx` - The context containing all accounts
    /// * `treasury` - The treasury wallet for collecting tier fees
    /// * `points_mint` - The SPL token mint for POINTS
    pub fn initialize(ctx: Context<Initialize>, treasury: Pubkey, points_mint: Pubkey) -> Result<()> {
        instructions::initialize::handler(ctx, treasury, points_mint)
    }

    /// Create a new tournament (admin only).
    ///
    /// # Arguments
    /// * `ctx` - The context containing all accounts
    /// * `max_players` - Maximum number of players allowed
    /// * `starting_stack` - Starting chip stack for each player
    /// * `starts_at` - Unix timestamp when tournament is scheduled to start
    /// * `blind_structure_hash` - SHA-256 hash of the blind structure JSON
    /// * `payout_structure_hash` - SHA-256 hash of the admin-customized payout table
    pub fn create_tournament(
        ctx: Context<CreateTournament>,
        max_players: u16,
        starting_stack: u64,
        starts_at: i64,
        blind_structure_hash: [u8; 32],
        payout_structure_hash: [u8; 32],
    ) -> Result<()> {
        instructions::create_tournament::handler(
            ctx,
            max_players,
            starting_stack,
            starts_at,
            blind_structure_hash,
            payout_structure_hash,
        )
    }

    /// Open registration for a tournament (admin only).
    /// Changes tournament status from Created to Registration.
    pub fn open_registration(ctx: Context<OpenRegistration>) -> Result<()> {
        instructions::open_registration::handler(ctx)
    }

    /// Register a player for a tournament.
    ///
    /// # Arguments
    /// * `ctx` - The context containing all accounts
    /// * `tier` - The agent tier (FREE, BASIC, or PRO)
    /// * `agent_prompt_hash` - SHA-256 hash of the custom prompt
    /// * `agent_name` - Display name for the agent (32 bytes)
    /// * `agent_image_uri` - URI for agent avatar image (128 bytes)
    pub fn register_player(
        ctx: Context<RegisterPlayer>,
        tier: AgentTier,
        agent_prompt_hash: [u8; 32],
        agent_name: [u8; 32],
        agent_image_uri: [u8; 128],
    ) -> Result<()> {
        instructions::register_player::handler(ctx, tier, agent_prompt_hash, agent_name, agent_image_uri)
    }

    /// Create the POINTS SPL token mint (admin only, one-time setup).
    /// Creates a new SPL token mint with a PDA as the mint authority.
    pub fn create_points_mint(ctx: Context<CreatePointsMint>) -> Result<()> {
        instructions::create_points_mint::handler(ctx)
    }

    /// Start a tournament (admin only).
    /// Captures RNG seed and changes status to InProgress.
    pub fn start_tournament(ctx: Context<StartTournament>) -> Result<()> {
        instructions::start_tournament::handler(ctx)
    }

    /// Finalize a tournament (admin only).
    /// Records the results hash and winner, changes status to Completed.
    ///
    /// # Arguments
    /// * `ctx` - The context containing all accounts
    /// * `results_hash` - SHA-256 hash of final standings JSON
    /// * `winner` - Winner's wallet address
    pub fn finalize_tournament(
        ctx: Context<FinalizeTournament>,
        results_hash: [u8; 32],
        winner: Pubkey,
    ) -> Result<()> {
        instructions::finalize_tournament::handler(ctx, results_hash, winner)
    }

    /// Record a player's tournament result (admin only).
    /// Updates the player's registration with final rank, points, etc.
    /// Creates or updates the player's lifetime statistics.
    ///
    /// # Arguments
    /// * `ctx` - The context containing all accounts
    /// * `final_rank` - Player's finishing position (1 = winner)
    /// * `points_awarded` - POINTS tokens to award
    /// * `hands_played` - Number of hands played
    /// * `eliminations` - Number of players eliminated
    pub fn record_player_result(
        ctx: Context<RecordPlayerResult>,
        final_rank: u16,
        points_awarded: u64,
        hands_played: u32,
        eliminations: u8,
    ) -> Result<()> {
        instructions::record_player_result::handler(ctx, final_rank, points_awarded, hands_played, eliminations)
    }

    /// Distribute POINTS tokens to a player (admin only).
    /// Mints the awarded POINTS tokens to the player's token account.
    pub fn distribute_points(ctx: Context<DistributePoints>) -> Result<()> {
        instructions::distribute_points::handler(ctx)
    }
}
