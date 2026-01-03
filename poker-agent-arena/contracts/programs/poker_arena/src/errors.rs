use anchor_lang::prelude::*;

/// Arena error codes organized by category.
/// Error codes are 4-digit for consistency with the API layer.
#[error_code]
pub enum ArenaError {
    // =========================================================================
    // Authentication (1000-1099)
    // =========================================================================
    /// Only admin can perform this action
    #[msg("Only admin can perform this action")]
    Unauthorized = 1001,

    /// Invalid signature provided
    #[msg("Invalid signature provided")]
    InvalidSignature = 1002,

    // =========================================================================
    // Tournament (2000-2099)
    // =========================================================================
    /// Tournament not found
    #[msg("Tournament not found")]
    TournamentNotFound = 2001,

    /// Tournament is full
    #[msg("Tournament is full")]
    TournamentFull = 2002,

    /// Tournament registration is not open
    #[msg("Tournament registration is not open")]
    RegistrationNotOpen = 2003,

    /// Already registered for this tournament
    #[msg("Already registered for this tournament")]
    AlreadyRegistered = 2004,

    /// Tournament has not started
    #[msg("Tournament has not started")]
    TournamentNotStarted = 2005,

    /// Tournament has already started
    #[msg("Tournament has already started")]
    TournamentAlreadyStarted = 2006,

    /// Tournament not in progress
    #[msg("Tournament not in progress")]
    TournamentNotInProgress = 2007,

    /// Tournament not completed
    #[msg("Tournament not completed")]
    TournamentNotCompleted = 2008,

    /// Points already distributed to player
    #[msg("Points already distributed to player")]
    PointsAlreadyDistributed = 2009,

    /// Player has no points to distribute
    #[msg("Player has no points to distribute")]
    NoPointsToDistribute = 2010,

    // =========================================================================
    // Agent (3000-3099)
    // =========================================================================
    /// Invalid agent tier
    #[msg("Invalid agent tier")]
    InvalidTier = 3001,

    /// Prompt exceeds maximum length for tier
    #[msg("Prompt exceeds maximum length for tier")]
    PromptTooLong = 3002,

    /// Agent customization locked after tournament start
    #[msg("Agent customization locked after tournament start")]
    AgentLocked = 3003,

    /// Slider value out of valid range (0-100)
    #[msg("Slider value out of valid range (0-100)")]
    SliderOutOfRange = 3004,

    // =========================================================================
    // Payment (4000-4099)
    // =========================================================================
    /// Insufficient balance for registration
    #[msg("Insufficient balance for registration")]
    InsufficientBalance = 4001,

    /// Invalid agent tier payment amount
    #[msg("Invalid agent tier payment amount")]
    InvalidTierPayment = 4002,

    /// Transaction failed
    #[msg("Transaction failed")]
    TransactionFailed = 4003,

    // =========================================================================
    // System (5000-5099)
    // =========================================================================
    /// Invalid results hash
    #[msg("Invalid results hash")]
    InvalidResultsHash = 5001,

    /// Invalid payout structure
    #[msg("Invalid payout structure")]
    InvalidPayoutStructure = 5002,
}
