use anchor_lang::prelude::*;

/// Tournament status enum
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, Debug)]
pub enum TournamentStatus {
    /// Admin has created tournament, registration not yet open
    Created,
    /// Open for player registration
    Registration,
    /// Tournament is running
    InProgress,
    /// Tournament has finished
    Completed,
    /// Tournament was cancelled
    Cancelled,
}

impl Default for TournamentStatus {
    fn default() -> Self {
        TournamentStatus::Created
    }
}

/// Tournament account.
/// Stores all tournament configuration and state.
#[account]
pub struct Tournament {
    /// Unique tournament ID (matches tournament_count at creation)
    pub id: u64,

    /// Admin who created the tournament (must match ArenaConfig.admin)
    pub admin: Pubkey,

    /// Current tournament status
    pub status: TournamentStatus,

    /// Unix timestamp when tournament was created
    pub created_at: i64,

    /// Unix timestamp when tournament is scheduled to start
    pub starts_at: i64,

    /// Unix timestamp when tournament completed (None if not completed)
    pub completed_at: Option<i64>,

    /// Maximum number of players allowed
    pub max_players: u16,

    /// Current number of registered players
    pub registered_players: u16,

    /// Starting chip stack for each player
    pub starting_stack: u64,

    /// SHA-256 hash of the blind structure JSON
    pub blind_structure_hash: [u8; 32],

    /// SHA-256 hash of the admin-customized payout structure JSON
    pub payout_structure_hash: [u8; 32],

    /// SHA-256 hash of final tournament results (None until completed)
    pub results_hash: Option<[u8; 32]>,

    /// Winner's wallet address (None until completed)
    pub winner: Option<Pubkey>,

    /// Solana slot used for RNG seed commitment
    pub seed_slot: u64,

    /// Blockhash commitment for provably fair randomness
    pub seed_blockhash: [u8; 32],

    /// PDA bump seed
    pub bump: u8,
}

impl Tournament {
    /// Account size for rent calculation
    /// 8 (discriminator) + 8 + 32 + 1 + 8 + 8 + 9 + 2 + 2 + 8 + 32 + 32 + 33 + 33 + 8 + 32 + 1 = 277 bytes
    pub const SIZE: usize = 8 + 8 + 32 + 1 + 8 + 8 + 9 + 2 + 2 + 8 + 32 + 32 + 33 + 33 + 8 + 32 + 1;

    /// PDA seeds prefix
    pub const SEED_PREFIX: &'static [u8] = b"tournament";

    /// Check if registration is open
    pub fn is_registration_open(&self) -> bool {
        self.status == TournamentStatus::Registration
    }

    /// Check if tournament is full
    pub fn is_full(&self) -> bool {
        self.registered_players >= self.max_players
    }

    /// Check if tournament can start
    pub fn can_start(&self) -> bool {
        self.status == TournamentStatus::Registration && self.registered_players >= 2
    }
}
