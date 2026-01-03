# Smart Contract Specification

This document covers the Anchor program specification for the Poker Agent Arena on Solana.

---

## Table of Contents

1. [Program Overview](#program-overview)
2. [Account Structures](#account-structures)
3. [Instructions](#instructions)
4. [PDA Seeds](#pda-seeds)
5. [Error Codes](#error-codes)
6. [Key Addresses](#key-addresses)

---

## Program Overview

The Anchor program manages tournament lifecycle, player registration, and POINTS distribution.

### Key Responsibilities

- Tournament creation and configuration (admin only)
- Player registration with tier-based payments
- Blockhash commitment for provably fair RNG
- Results finalization and on-chain storage
- POINTS (SPL token) distribution

---

## Account Structures

### ArenaConfig

```rust
// programs/poker_arena/src/state/config.rs

#[account]
pub struct ArenaConfig {
    pub admin: Pubkey,           // Admin wallet (sole authority)
    pub treasury: Pubkey,        // Treasury wallet for fees
    pub points_mint: Pubkey,     // SPL token mint for POINTS
    pub tournament_count: u64,   // Total tournaments created
    pub bump: u8,
}

// Space: 8 (discriminator) + 32 + 32 + 32 + 8 + 1 = 113 bytes
```

### Tournament

```rust
// programs/poker_arena/src/state/tournament.rs

#[account]
pub struct Tournament {
    pub id: u64,                           // Unique tournament ID
    pub admin: Pubkey,                     // Creator (must match ArenaConfig.admin)
    pub status: TournamentStatus,          // Enum: Created, Registration, InProgress, Completed
    pub created_at: i64,                   // Unix timestamp
    pub starts_at: i64,                    // Scheduled start time
    pub completed_at: Option<i64>,         // Completion timestamp

    // Structure
    pub max_players: u16,                  // Maximum entrants
    pub registered_players: u16,           // Current registrations
    pub starting_stack: u64,               // Starting chips
    pub blind_structure_hash: [u8; 32],    // SHA-256 of blind levels JSON
    pub payout_structure_hash: [u8; 32],   // SHA-256 of payout table JSON (admin-customized)

    // Results
    pub results_hash: Option<[u8; 32]>,    // SHA-256 of final results JSON
    pub winner: Option<Pubkey>,            // Winner's wallet

    // Randomness
    pub seed_slot: u64,                    // Slot used for RNG seed
    pub seed_blockhash: [u8; 32],          // Blockhash commitment

    pub bump: u8,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum TournamentStatus {
    Created,        // Admin has created, registration not yet open
    Registration,   // Open for player registration
    InProgress,     // Tournament running
    Completed,      // Tournament finished
    Cancelled,      // Tournament cancelled
}

// Space: 8 + 8 + 32 + 1 + 8 + 8 + 9 + 2 + 2 + 8 + 32 + 32 + 33 + 33 + 8 + 32 + 1 ≈ 277 bytes
```

### PlayerRegistration

```rust
// programs/poker_arena/src/state/player.rs

#[account]
pub struct PlayerRegistration {
    pub tournament: Pubkey,                // Tournament PDA
    pub wallet: Pubkey,                    // Player's wallet
    pub tier: AgentTier,                   // FREE, BASIC, PRO
    pub registered_at: i64,                // Registration timestamp
    pub agent_prompt_hash: [u8; 32],       // SHA-256 of custom prompt (if any)
    pub agent_name: [u8; 32],              // Agent display name (UTF-8, null-padded)
    pub agent_image_uri: [u8; 128],        // JPEG URI (off-chain storage)

    // Results (populated after tournament)
    pub final_rank: Option<u16>,           // 1 = winner
    pub points_awarded: Option<u64>,       // POINTS earned
    pub hands_played: Option<u32>,         // Total hands
    pub eliminations: Option<u8>,          // Players eliminated

    pub bump: u8,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum AgentTier {
    Free,           // 0 SOL - Base engine only
    Basic,          // 0.1 SOL - Base engine + sliders only (no freeform prompt)
    Pro,            // 1 SOL - Base engine + sliders + freeform strategy prompt
}

// Space: 8 + 32 + 32 + 1 + 8 + 32 + 32 + 128 + 3 + 9 + 5 + 2 + 1 ≈ 293 bytes
```

### PlayerStats

```rust
// programs/poker_arena/src/state/player.rs

#[account]
pub struct PlayerStats {
    pub wallet: Pubkey,                    // Player's wallet
    pub tournaments_played: u32,           // Lifetime tournaments
    pub tournaments_won: u32,              // First place finishes
    pub total_points: u64,                 // Lifetime POINTS earned
    pub best_finish: u16,                  // Best rank achieved
    pub total_hands_played: u64,           // Lifetime hands
    pub total_eliminations: u32,           // Lifetime knockouts
    pub last_tournament: Pubkey,           // Most recent tournament
    pub last_played_at: i64,               // Timestamp
    pub bump: u8,
}

// Space: 8 + 32 + 4 + 4 + 8 + 2 + 8 + 4 + 32 + 8 + 1 = 111 bytes
```

---

## Instructions

```rust
// programs/poker_arena/src/lib.rs

#[program]
pub mod poker_arena {
    use super::*;

    /// Initialize the arena (one-time setup)
    pub fn initialize(
        ctx: Context<Initialize>,
        admin: Pubkey,
        treasury: Pubkey,
    ) -> Result<()>;

    /// Create a new tournament (admin only)
    /// payout_structure_hash contains SHA-256 of admin-customized payout table
    pub fn create_tournament(
        ctx: Context<CreateTournament>,
        max_players: u16,
        starting_stack: u64,
        starts_at: i64,
        blind_structure_hash: [u8; 32],
        payout_structure_hash: [u8; 32],
    ) -> Result<()>;

    /// Register a player for a tournament
    /// tier determines payment: FREE (0), BASIC (0.1 SOL - sliders only), PRO (1 SOL - sliders + prompt)
    pub fn register_player(
        ctx: Context<RegisterPlayer>,
        tier: AgentTier,
        agent_prompt_hash: [u8; 32],
        agent_name: [u8; 32],
        agent_image_uri: [u8; 128],
    ) -> Result<()>;

    /// Start the tournament (admin only) - commits blockhash
    pub fn start_tournament(
        ctx: Context<StartTournament>,
    ) -> Result<()>;

    /// Finalize tournament results (admin only, called by backend)
    pub fn finalize_tournament(
        ctx: Context<FinalizeTournament>,
        results_hash: [u8; 32],
        winner: Pubkey,
    ) -> Result<()>;

    /// Record player result (admin only, after tournament)
    pub fn record_player_result(
        ctx: Context<RecordPlayerResult>,
        final_rank: u16,
        points_awarded: u64,
        hands_played: u32,
        eliminations: u8,
    ) -> Result<()>;

    /// Distribute POINTS to player (admin only)
    pub fn distribute_points(
        ctx: Context<DistributePoints>,
        amount: u64,
    ) -> Result<()>;
}
```

---

## PDA Seeds

```rust
// Arena config PDA
seeds = [b"arena_config"]

// Tournament PDA
seeds = [b"tournament", &tournament_id.to_le_bytes()]

// Player registration PDA
seeds = [b"registration", tournament.key().as_ref(), wallet.key().as_ref()]

// Player lifetime stats PDA
seeds = [b"player_stats", wallet.key().as_ref()]

// POINTS mint authority PDA
seeds = [b"points_mint_authority"]
```

---

## Error Codes

Error codes are organized by category with 4-digit codes for consistency with the API layer:

```rust
#[error_code]
pub enum ArenaError {
    // Authentication (1000-1099)
    #[msg("Only admin can perform this action")]
    Unauthorized = 1001,

    #[msg("Invalid signature provided")]
    InvalidSignature = 1002,

    // Tournament (2000-2099)
    #[msg("Tournament not found")]
    TournamentNotFound = 2001,

    #[msg("Tournament is full")]
    TournamentFull = 2002,

    #[msg("Tournament registration is not open")]
    RegistrationNotOpen = 2003,

    #[msg("Already registered for this tournament")]
    AlreadyRegistered = 2004,

    #[msg("Tournament has not started")]
    TournamentNotStarted = 2005,

    #[msg("Tournament has already started")]
    TournamentAlreadyStarted = 2006,

    #[msg("Tournament not in progress")]
    TournamentNotInProgress = 2007,

    // Agent (3000-3099)
    #[msg("Invalid agent tier")]
    InvalidTier = 3001,

    #[msg("Prompt exceeds maximum length for tier")]
    PromptTooLong = 3002,

    #[msg("Agent customization locked after tournament start")]
    AgentLocked = 3003,

    #[msg("Slider value out of valid range (0-100)")]
    SliderOutOfRange = 3004,

    // Payment (4000-4099)
    #[msg("Insufficient balance for registration")]
    InsufficientBalance = 4001,

    #[msg("Invalid agent tier payment amount")]
    InvalidTierPayment = 4002,

    #[msg("Transaction failed")]
    TransactionFailed = 4003,

    // System (5000-5099)
    #[msg("Invalid results hash")]
    InvalidResultsHash = 5001,

    #[msg("Invalid payout structure")]
    InvalidPayoutStructure = 5002,
}
```

---

## Key Addresses

### Development (Devnet)

| Purpose | Address |
|---------|---------|
| **Program ID** | `34MhwbaRczNA8Zt4H8rUwPV4o2MsAtYd8hQhNno3QaLN` |

### Production (Mainnet)

| Purpose | Address |
|---------|---------|
| **Admin Wallet** | `BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m` |
| **Agent Registration Fees Wallet** | `CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm` |
