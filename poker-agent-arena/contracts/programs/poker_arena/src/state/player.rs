use anchor_lang::prelude::*;

/// Agent tier enum
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, Debug)]
pub enum AgentTier {
    /// 0 SOL - Base engine only
    Free,
    /// 0.1 SOL - Base engine + sliders only (no freeform prompt)
    Basic,
    /// 1 SOL - Base engine + sliders + freeform strategy prompt
    Pro,
}

impl AgentTier {
    /// Get the cost in lamports for this tier
    pub fn cost_lamports(&self) -> u64 {
        match self {
            AgentTier::Free => 0,
            AgentTier::Basic => 100_000_000,  // 0.1 SOL
            AgentTier::Pro => 1_000_000_000,  // 1 SOL
        }
    }
}

impl Default for AgentTier {
    fn default() -> Self {
        AgentTier::Free
    }
}

/// Player registration for a specific tournament.
#[account]
pub struct PlayerRegistration {
    /// Tournament this registration is for
    pub tournament: Pubkey,

    /// Player's wallet address
    pub wallet: Pubkey,

    /// Selected agent tier
    pub tier: AgentTier,

    /// Unix timestamp when player registered
    pub registered_at: i64,

    /// SHA-256 hash of custom prompt (for verification)
    pub agent_prompt_hash: [u8; 32],

    /// Agent display name (UTF-8, null-padded)
    pub agent_name: [u8; 32],

    /// JPEG image URI for agent avatar (off-chain storage)
    pub agent_image_uri: [u8; 128],

    /// Final rank in tournament (1 = winner, None if not completed)
    pub final_rank: Option<u16>,

    /// POINTS earned in tournament (None if not completed)
    pub points_awarded: Option<u64>,

    /// Total hands played (None if not completed)
    pub hands_played: Option<u32>,

    /// Number of players eliminated (None if not completed)
    pub eliminations: Option<u8>,

    /// Whether POINTS tokens have been distributed to this player
    pub points_distributed: bool,

    /// PDA bump seed
    pub bump: u8,
}

impl PlayerRegistration {
    /// Account size for rent calculation
    /// 8 (discriminator) + 32 + 32 + 1 + 8 + 32 + 32 + 128 + 3 + 9 + 5 + 2 + 1 + 1 = 294 bytes
    pub const SIZE: usize = 8 + 32 + 32 + 1 + 8 + 32 + 32 + 128 + 3 + 9 + 5 + 2 + 1 + 1;

    /// PDA seeds prefix
    pub const SEED_PREFIX: &'static [u8] = b"registration";
}

/// Lifetime player statistics.
#[account]
pub struct PlayerStats {
    /// Player's wallet address
    pub wallet: Pubkey,

    /// Total tournaments played
    pub tournaments_played: u32,

    /// Total first place finishes
    pub tournaments_won: u32,

    /// Lifetime POINTS earned
    pub total_points: u64,

    /// Best tournament finish (1 = first place)
    pub best_finish: u16,

    /// Lifetime hands played
    pub total_hands_played: u64,

    /// Lifetime eliminations
    pub total_eliminations: u32,

    /// Most recent tournament
    pub last_tournament: Pubkey,

    /// Timestamp of last tournament played
    pub last_played_at: i64,

    /// PDA bump seed
    pub bump: u8,
}

impl PlayerStats {
    /// Account size for rent calculation
    /// 8 (discriminator) + 32 + 4 + 4 + 8 + 2 + 8 + 4 + 32 + 8 + 1 = 111 bytes
    pub const SIZE: usize = 8 + 32 + 4 + 4 + 8 + 2 + 8 + 4 + 32 + 8 + 1;

    /// PDA seeds prefix
    pub const SEED_PREFIX: &'static [u8] = b"player_stats";
}
