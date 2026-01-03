-- Phase 5: On-Chain Settlement Schema Updates
-- Adds columns and tables for tracking on-chain settlement

-- Add new columns to tournaments table
ALTER TABLE tournaments ADD COLUMN IF NOT EXISTS finalization_tx VARCHAR(256);
ALTER TABLE tournaments ADD COLUMN IF NOT EXISTS points_distributed BOOLEAN DEFAULT FALSE;

-- Add new columns to registrations table
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS result_recorded_at TIMESTAMPTZ;
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS points_distributed_at TIMESTAMPTZ;
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS result_tx VARCHAR(256);
ALTER TABLE registrations ADD COLUMN IF NOT EXISTS distribution_tx VARCHAR(256);

-- Create audit log table for tracking admin actions
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID REFERENCES tournaments(id),
    action VARCHAR(50) NOT NULL,
    wallet VARCHAR(44),
    tx_signature VARCHAR(256),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_tournament ON audit_log(tournament_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_wallet ON audit_log(wallet);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- Create index for tracking points distribution status
CREATE INDEX IF NOT EXISTS idx_registrations_points_distributed ON registrations(points_distributed_at);
CREATE INDEX IF NOT EXISTS idx_tournaments_points_distributed ON tournaments(points_distributed);
