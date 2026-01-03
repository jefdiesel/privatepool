-- Initial Schema for Poker Agent Arena
-- Database: Neon PostgreSQL

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    on_chain_id BIGINT UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'created',

    -- Configuration
    max_players SMALLINT NOT NULL,
    starting_stack BIGINT NOT NULL,
    blind_structure JSONB NOT NULL,
    payout_structure JSONB NOT NULL,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    registration_opens_at TIMESTAMPTZ,
    starts_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    -- Results
    results_hash BYTEA,
    winner_wallet VARCHAR(44),

    -- Randomness
    seed_slot BIGINT,
    seed_blockhash BYTEA,

    CONSTRAINT valid_status CHECK (status IN ('created', 'registration', 'in_progress', 'completed', 'cancelled'))
);

-- Player registrations
CREATE TABLE IF NOT EXISTS registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id),
    wallet VARCHAR(44) NOT NULL,

    -- Agent configuration
    tier VARCHAR(10) NOT NULL,
    agent_name VARCHAR(32) NOT NULL,
    agent_image_uri VARCHAR(256),
    agent_sliders JSONB,
    agent_prompt_encrypted TEXT,
    agent_prompt_hash BYTEA NOT NULL,

    -- Timestamps
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prompt_locked_at TIMESTAMPTZ,

    -- Results (populated after tournament)
    final_rank SMALLINT,
    points_awarded BIGINT,
    hands_played INTEGER,
    eliminations SMALLINT,

    UNIQUE (tournament_id, wallet),
    CONSTRAINT valid_tier CHECK (tier IN ('free', 'basic', 'pro'))
);

-- Hand history
CREATE TABLE IF NOT EXISTS hands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id),
    table_id VARCHAR(36) NOT NULL,
    hand_number INTEGER NOT NULL,

    -- Hand data
    button_position SMALLINT NOT NULL,
    small_blind_amount INTEGER NOT NULL,
    big_blind_amount INTEGER NOT NULL,
    ante_amount INTEGER,

    -- Cards
    community_cards VARCHAR(14),

    -- Pot
    pot_size INTEGER NOT NULL,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    UNIQUE (tournament_id, hand_number)
);

-- Hand actions
CREATE TABLE IF NOT EXISTS hand_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(id),

    -- Action details
    sequence INTEGER NOT NULL,
    wallet VARCHAR(44) NOT NULL,
    betting_round VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    amount INTEGER,

    -- AI decision metadata
    decision_time_ms INTEGER,
    input_tokens_used INTEGER,
    output_tokens_used INTEGER,
    cache_hit BOOLEAN,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hand players (who was dealt in)
CREATE TABLE IF NOT EXISTS hand_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(id),
    wallet VARCHAR(44) NOT NULL,

    seat_position SMALLINT NOT NULL,
    hole_cards_encrypted VARCHAR(64),
    starting_stack INTEGER NOT NULL,
    ending_stack INTEGER NOT NULL,

    -- Result
    won_amount INTEGER DEFAULT 0,
    hand_rank VARCHAR(20),

    UNIQUE (hand_id, wallet)
);

-- Lifetime player stats (denormalized for performance)
CREATE TABLE IF NOT EXISTS player_stats (
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
CREATE INDEX IF NOT EXISTS idx_registrations_tournament ON registrations(tournament_id);
CREATE INDEX IF NOT EXISTS idx_registrations_wallet ON registrations(wallet);
CREATE INDEX IF NOT EXISTS idx_hands_tournament ON hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_hand_actions_hand ON hand_actions(hand_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_points ON player_stats(total_points DESC);
CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);
CREATE INDEX IF NOT EXISTS idx_tournaments_starts_at ON tournaments(starts_at);
