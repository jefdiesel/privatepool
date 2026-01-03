use anchor_lang::prelude::*;

/// Arena configuration account.
/// Single global config for the entire poker arena.
#[account]
pub struct ArenaConfig {
    /// Admin wallet (sole authority for admin operations)
    pub admin: Pubkey,

    /// Treasury wallet for collecting tier fees
    pub treasury: Pubkey,

    /// SPL token mint for POINTS
    pub points_mint: Pubkey,

    /// Total number of tournaments created
    pub tournament_count: u64,

    /// PDA bump seed
    pub bump: u8,
}

impl ArenaConfig {
    /// Account size for rent calculation
    /// 8 (discriminator) + 32 + 32 + 32 + 8 + 1 = 113 bytes
    pub const SIZE: usize = 8 + 32 + 32 + 32 + 8 + 1;

    /// PDA seeds
    pub const SEED_PREFIX: &'static [u8] = b"arena_config";
}
