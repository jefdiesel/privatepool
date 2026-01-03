use anchor_lang::prelude::*;

/// PDA account that holds mint authority for POINTS token.
/// This allows the program to mint tokens without external signers.
#[account]
pub struct PointsMintAuthority {
    /// PDA bump seed
    pub bump: u8,
}

impl PointsMintAuthority {
    /// Account size for rent calculation
    /// 8 (discriminator) + 1 = 9 bytes
    pub const SIZE: usize = 8 + 1;

    /// PDA seeds prefix
    pub const SEED_PREFIX: &'static [u8] = b"points_mint_authority";
}
