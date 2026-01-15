-- Agent Live Settings for Real-Time Slider Control
-- Allows BASIC and PRO tier users to adjust aggression and tightness during live tournaments

CREATE TABLE IF NOT EXISTS agent_live_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
    wallet VARCHAR(44) NOT NULL,

    -- Active settings (currently being used by the agent)
    active_aggression SMALLINT NOT NULL DEFAULT 5,
    active_tightness SMALLINT NOT NULL DEFAULT 5,

    -- Pending settings (slider position, not yet confirmed)
    pending_aggression SMALLINT,
    pending_tightness SMALLINT,

    -- Confirmed settings (waiting to be applied at next hand start)
    confirmed_aggression SMALLINT,
    confirmed_tightness SMALLINT,
    confirmed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE (tournament_id, wallet),
    CONSTRAINT valid_active_aggression CHECK (active_aggression >= 1 AND active_aggression <= 10),
    CONSTRAINT valid_active_tightness CHECK (active_tightness >= 1 AND active_tightness <= 10),
    CONSTRAINT valid_pending_aggression CHECK (pending_aggression IS NULL OR (pending_aggression >= 1 AND pending_aggression <= 10)),
    CONSTRAINT valid_pending_tightness CHECK (pending_tightness IS NULL OR (pending_tightness >= 1 AND pending_tightness <= 10)),
    CONSTRAINT valid_confirmed_aggression CHECK (confirmed_aggression IS NULL OR (confirmed_aggression >= 1 AND confirmed_aggression <= 10)),
    CONSTRAINT valid_confirmed_tightness CHECK (confirmed_tightness IS NULL OR (confirmed_tightness >= 1 AND confirmed_tightness <= 10))
);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_live_settings_tournament ON agent_live_settings(tournament_id);
CREATE INDEX IF NOT EXISTS idx_live_settings_wallet ON agent_live_settings(wallet);
CREATE INDEX IF NOT EXISTS idx_live_settings_confirmed ON agent_live_settings(tournament_id)
    WHERE confirmed_aggression IS NOT NULL OR confirmed_tightness IS NOT NULL;

-- Comment for documentation
COMMENT ON TABLE agent_live_settings IS 'Real-time slider settings for BASIC/PRO tier agents during live tournaments';
COMMENT ON COLUMN agent_live_settings.active_aggression IS '1=passive (check/call), 10=aggressive (bet/raise)';
COMMENT ON COLUMN agent_live_settings.active_tightness IS '1=loose (many hands), 10=tight (selective)';
