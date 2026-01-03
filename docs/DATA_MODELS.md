# Data Models

This document covers the PostgreSQL schema and Redis cache structure for the Poker Agent Arena.

---

## Table of Contents

1. [PostgreSQL Schema](#postgresql-schema)
2. [Redis Cache Structure](#redis-cache-structure)

---

## PostgreSQL Schema

```sql
-- Database: Neon PostgreSQL

-- Tournaments table
CREATE TABLE tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    on_chain_id BIGINT UNIQUE NOT NULL,  -- Matches Solana program
    status VARCHAR(20) NOT NULL DEFAULT 'created',

    -- Configuration
    max_players SMALLINT NOT NULL,
    starting_stack BIGINT NOT NULL,
    blind_structure JSONB NOT NULL,       -- Includes ante per level (BB-only)
    payout_structure JSONB NOT NULL,      -- Admin-customized payout table

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    registration_opens_at TIMESTAMPTZ,
    starts_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Results
    results_hash BYTEA,  -- SHA-256
    winner_wallet VARCHAR(44),

    -- Randomness
    seed_slot BIGINT,
    seed_blockhash BYTEA,

    CONSTRAINT valid_status CHECK (status IN ('created', 'registration', 'in_progress', 'completed', 'cancelled'))
);

-- Player registrations
CREATE TABLE registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id),
    wallet VARCHAR(44) NOT NULL,

    -- Agent configuration
    tier VARCHAR(10) NOT NULL,  -- 'free', 'basic', 'pro'
    agent_name VARCHAR(32) NOT NULL,
    agent_image_uri VARCHAR(256),
    agent_sliders JSONB,  -- {aggression, bluff_frequency, tightness, position_awareness} - BASIC + PRO only
    agent_prompt_encrypted TEXT,  -- Encrypted custom prompt - PRO only
    agent_prompt_hash BYTEA NOT NULL,  -- SHA-256 for on-chain verification

    -- Timestamps
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prompt_locked_at TIMESTAMPTZ,  -- Set when tournament starts

    -- Results (populated after tournament)
    final_rank SMALLINT,
    points_awarded BIGINT,
    hands_played INTEGER,
    eliminations SMALLINT,

    UNIQUE (tournament_id, wallet),
    CONSTRAINT valid_tier CHECK (tier IN ('free', 'basic', 'pro'))
);

-- Hand history
CREATE TABLE hands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id),
    table_id VARCHAR(36) NOT NULL,
    hand_number INTEGER NOT NULL,

    -- Hand data
    button_position SMALLINT NOT NULL,
    small_blind_amount INTEGER NOT NULL,
    big_blind_amount INTEGER NOT NULL,
    ante_amount INTEGER,  -- Paid by BB only

    -- Cards
    community_cards VARCHAR(14),  -- "AhKd7c2s9h"

    -- Pot
    pot_size INTEGER NOT NULL,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    UNIQUE (tournament_id, hand_number)
);

-- Hand actions
CREATE TABLE hand_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(id),

    -- Action details
    sequence INTEGER NOT NULL,  -- Order within hand
    wallet VARCHAR(44) NOT NULL,
    betting_round VARCHAR(10) NOT NULL,  -- 'preflop', 'flop', 'turn', 'river'
    action VARCHAR(10) NOT NULL,  -- 'fold', 'check', 'call', 'raise', 'all_in', 'post_blind', 'post_ante'
    amount INTEGER,

    -- AI decision metadata
    decision_time_ms INTEGER,
    input_tokens_used INTEGER,
    output_tokens_used INTEGER,
    cache_hit BOOLEAN,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hand players (who was dealt in)
CREATE TABLE hand_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(id),
    wallet VARCHAR(44) NOT NULL,

    seat_position SMALLINT NOT NULL,
    hole_cards_encrypted VARCHAR(64),  -- Encrypted "QsQd"
    starting_stack INTEGER NOT NULL,
    ending_stack INTEGER NOT NULL,

    -- Result
    won_amount INTEGER DEFAULT 0,
    hand_rank VARCHAR(20),  -- 'pair', 'two_pair', etc.

    UNIQUE (hand_id, wallet)
);

-- Lifetime player stats (denormalized for performance)
CREATE TABLE player_stats (
    wallet VARCHAR(44) PRIMARY KEY,

    tournaments_played INTEGER NOT NULL DEFAULT 0,
    tournaments_won INTEGER NOT NULL DEFAULT 0,
    total_points BIGINT NOT NULL DEFAULT 0,
    best_finish SMALLINT,
    total_hands_played BIGINT NOT NULL DEFAULT 0,
    total_eliminations INTEGER NOT NULL DEFAULT 0,

    last_tournament_id UUID REFERENCES tournaments(id),
    last_played_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_registrations_tournament ON registrations(tournament_id);
CREATE INDEX idx_registrations_wallet ON registrations(wallet);
CREATE INDEX idx_hands_tournament ON hands(tournament_id);
CREATE INDEX idx_hand_actions_hand ON hand_actions(hand_id);
CREATE INDEX idx_player_stats_points ON player_stats(total_points DESC);
```

### Blind Structure JSON Example

```json
{
  "levels": [
    {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 6},
    {"level": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 6},
    {"level": 3, "small_blind": 75, "big_blind": 150, "ante": 0, "duration_minutes": 6},
    {"level": 4, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 6},
    {"level": 5, "small_blind": 150, "big_blind": 300, "ante": 25, "duration_minutes": 6},
    {"level": 6, "small_blind": 200, "big_blind": 400, "ante": 50, "duration_minutes": 6}
  ]
}
```

**Note**: The `ante` field represents the additional amount the big blind player pays. For level 4, the BB posts 200 (big blind) + 25 (ante) = 225 total.

### Payout Structure JSON Example (Admin-Customized)

```json
{
  "payouts": [
    {"rank": 1, "points": 5000},
    {"rank": 2, "points": 3000},
    {"rank": 3, "points": 2000},
    {"rank": 4, "points": 1000},
    {"rank": 5, "points": 500},
    {"rank": 6, "points": 500}
  ],
  "created_by": "admin",
  "description": "Top 6 payout structure for 27-player tournament"
}
```

---

## Redis Cache Structure

```
# Upstash Redis

# Active tournament state (TTL: duration of tournament)
tournament:{id}:state → JSON {
    phase: "in_progress",
    currentLevel: 3,
    levelStartedAt: timestamp,
    playersRemaining: 18,
    tables: ["table_1", "table_2"],
    currentAnte: 25  # BB-only ante for current level
}

# Table state (TTL: duration of tournament)
table:{id}:state → JSON {
    tournamentId: "...",
    seats: [...],
    button: 2,
    currentHand: "hand_123",
    pot: 450
}

# Current hand state (TTL: 5 minutes)
hand:{id}:state → JSON {
    tableId: "...",
    bettingRound: "flop",
    communityCards: ["Ah", "Kd", "7c"],
    pot: 300,
    currentBet: 150,
    actionOn: 4,
    antePosted: true  # Indicates BB has posted ante
}

# Player session mapping (TTL: 24 hours)
session:{socketId} → {
    wallet: "...",
    tournamentId: "...",
    tableId: "..."
}

# Rate limiting (TTL: 1 minute)
ratelimit:{wallet}:{endpoint} → count

# Budget tracking per tournament
budget:{tournament_id} → float  # Max budget
spent:{tournament_id} → float   # Current spend (input + output token costs)
```

### Budget Tracking Keys

```
# Per-tournament budget management
budget:{tournament_id} → float              # Maximum allowed spend
spent:{tournament_id} → float               # Accumulated cost
decisions:{tournament_id} → int             # Decision count
tokens_input:{tournament_id} → int          # Total input tokens
tokens_output:{tournament_id} → int         # Total output tokens
cache_hits:{tournament_id} → int            # Prompt cache hit count
```
