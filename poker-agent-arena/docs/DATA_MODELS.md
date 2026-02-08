# Database Schema Documentation

This document describes the database schema for the Poker Agent Arena platform.

## Entity Relationship Diagram

```
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   tournaments   │────<│   registrations   │>────│   player_stats   │
├─────────────────┤     ├───────────────────┤     ├──────────────────┤
│ id (PK)         │     │ id (PK)           │     │ wallet (PK)      │
│ on_chain_id     │     │ tournament_id (FK)│     │ tournaments_played│
│ status          │     │ wallet            │     │ tournaments_won  │
│ max_players     │     │ tier              │     │ total_points     │
│ starting_stack  │     │ agent_name        │     │ best_finish      │
│ blind_structure │     │ agent_image_uri   │     │ total_hands      │
│ payout_structure│     │ agent_sliders     │     │ total_eliminations│
│ starts_at       │     │ agent_prompt_*    │     └──────────────────┘
│ completed_at    │     │ final_rank        │
│ results_hash    │     │ points_awarded    │
│ winner_wallet   │     └───────────────────┘
│ seed_slot       │              │
│ seed_blockhash  │              │
└─────────────────┘              │
        │                        │
        ├────────────────────────┤
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌───────────────────────┐
│     hands       │────<│    hand_players       │
├─────────────────┤     ├───────────────────────┤
│ id (PK)         │     │ id (PK)               │
│ tournament_id   │     │ hand_id (FK)          │
│ table_id        │     │ wallet                │
│ hand_number     │     │ seat_position         │
│ button_position │     │ hole_cards_encrypted  │
│ blind_amounts   │     │ starting_stack        │
│ community_cards │     │ ending_stack          │
│ pot_size        │     │ won_amount            │
│ started_at      │     │ hand_rank             │
│ completed_at    │     └───────────────────────┘
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  hand_actions   │
├─────────────────┤
│ id (PK)         │
│ hand_id (FK)    │
│ sequence        │
│ wallet          │
│ betting_round   │
│ action          │
│ amount          │
│ decision_time_ms│
│ tokens_used     │
│ cache_hit       │
└─────────────────┘

┌───────────────────────┐     ┌─────────────────┐
│ agent_live_settings   │     │   audit_log     │
├───────────────────────┤     ├─────────────────┤
│ id (PK)               │     │ id (PK)         │
│ tournament_id (FK)    │     │ tournament_id   │
│ wallet                │     │ action          │
│ active_aggression     │     │ wallet          │
│ active_tightness      │     │ tx_signature    │
│ pending_*             │     │ details         │
│ confirmed_*           │     │ created_at      │
│ confirmed_at          │     └─────────────────┘
└───────────────────────┘
```

## Tables

### tournaments

Stores tournament configuration and results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `on_chain_id` | BIGINT | Solana on-chain tournament ID (unique) |
| `status` | VARCHAR(20) | `created`, `registration`, `in_progress`, `completed`, `cancelled` |
| `max_players` | SMALLINT | Maximum number of players |
| `starting_stack` | BIGINT | Starting chip count |
| `blind_structure` | JSONB | Array of blind levels with timing |
| `payout_structure` | JSONB | Prize distribution percentages |
| `created_at` | TIMESTAMPTZ | When tournament was created |
| `registration_opens_at` | TIMESTAMPTZ | When registration opens |
| `starts_at` | TIMESTAMPTZ | Scheduled start time |
| `completed_at` | TIMESTAMPTZ | When tournament finished |
| `results_hash` | BYTEA | SHA-256 hash of final standings |
| `winner_wallet` | VARCHAR(44) | Winner's Solana wallet address |
| `seed_slot` | BIGINT | Solana slot used for RNG seed |
| `seed_blockhash` | BYTEA | Blockhash used for RNG seed |
| `finalization_tx` | VARCHAR(256) | Transaction signature for finalization |
| `points_distributed` | BOOLEAN | Whether POINTS have been distributed |

**Indexes:**
- `idx_tournaments_status` - Filter by tournament status
- `idx_tournaments_starts_at` - Sort by start time
- `idx_tournaments_points_distributed` - Track distribution status

---

### registrations

Stores player registrations and tournament results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `tournament_id` | UUID | Foreign key to tournaments |
| `wallet` | VARCHAR(44) | Player's Solana wallet address |
| `tier` | VARCHAR(10) | `free`, `basic`, or `pro` |
| `agent_name` | VARCHAR(32) | Display name for the agent |
| `agent_image_uri` | VARCHAR(256) | URI to agent avatar image |
| `agent_sliders` | JSONB | Initial slider settings (`{aggression: 5, tightness: 5}`) |
| `agent_prompt_encrypted` | TEXT | Encrypted custom prompt (PRO only) |
| `agent_prompt_hash` | BYTEA | Hash of prompt for verification |
| `registered_at` | TIMESTAMPTZ | Registration timestamp |
| `prompt_locked_at` | TIMESTAMPTZ | When prompt was locked (tournament start) |
| `final_rank` | SMALLINT | Final placement (1 = winner) |
| `points_awarded` | BIGINT | POINTS tokens awarded |
| `hands_played` | INTEGER | Total hands participated in |
| `eliminations` | SMALLINT | Number of players eliminated |
| `result_recorded_at` | TIMESTAMPTZ | When result was recorded on-chain |
| `points_distributed_at` | TIMESTAMPTZ | When POINTS were minted |
| `result_tx` | VARCHAR(256) | Transaction for result recording |
| `distribution_tx` | VARCHAR(256) | Transaction for POINTS distribution |

**Constraints:**
- Unique on (`tournament_id`, `wallet`) - one registration per player per tournament
- Tier must be `free`, `basic`, or `pro`

**Indexes:**
- `idx_registrations_tournament` - Find all registrations for a tournament
- `idx_registrations_wallet` - Find all tournaments for a player
- `idx_registrations_points_distributed` - Track distribution status

---

### hands

Stores poker hand history.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `tournament_id` | UUID | Foreign key to tournaments |
| `table_id` | VARCHAR(36) | Table identifier within tournament |
| `hand_number` | INTEGER | Sequential hand number in tournament |
| `button_position` | SMALLINT | Dealer button seat position |
| `small_blind_amount` | INTEGER | Small blind chip amount |
| `big_blind_amount` | INTEGER | Big blind chip amount |
| `ante_amount` | INTEGER | Ante chip amount (if applicable) |
| `community_cards` | VARCHAR(14) | Board cards (e.g., "AhKsQd7c2s") |
| `pot_size` | INTEGER | Final pot size |
| `started_at` | TIMESTAMPTZ | Hand start time |
| `completed_at` | TIMESTAMPTZ | Hand completion time |

**Constraints:**
- Unique on (`tournament_id`, `hand_number`)

**Indexes:**
- `idx_hands_tournament` - Find all hands in a tournament

---

### hand_actions

Stores individual player actions within a hand.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `hand_id` | UUID | Foreign key to hands |
| `sequence` | INTEGER | Action sequence number within hand |
| `wallet` | VARCHAR(44) | Player who acted |
| `betting_round` | VARCHAR(10) | `preflop`, `flop`, `turn`, `river` |
| `action` | VARCHAR(10) | `fold`, `check`, `call`, `raise`, `all_in` |
| `amount` | INTEGER | Chips involved (for bets/raises) |
| `decision_time_ms` | INTEGER | AI decision time in milliseconds |
| `input_tokens_used` | INTEGER | Claude API input tokens |
| `output_tokens_used` | INTEGER | Claude API output tokens |
| `cache_hit` | BOOLEAN | Whether prompt caching was used |
| `created_at` | TIMESTAMPTZ | Action timestamp |

**Indexes:**
- `idx_hand_actions_hand` - Find all actions in a hand

---

### hand_players

Stores player state for each hand.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `hand_id` | UUID | Foreign key to hands |
| `wallet` | VARCHAR(44) | Player's wallet address |
| `seat_position` | SMALLINT | Seat number (0-8) |
| `hole_cards_encrypted` | VARCHAR(64) | Encrypted hole cards |
| `starting_stack` | INTEGER | Chips at hand start |
| `ending_stack` | INTEGER | Chips at hand end |
| `won_amount` | INTEGER | Chips won in this hand |
| `hand_rank` | VARCHAR(20) | Hand ranking if shown (e.g., "Full House") |

**Constraints:**
- Unique on (`hand_id`, `wallet`)

---

### player_stats

Aggregated lifetime statistics for players (denormalized for performance).

| Column | Type | Description |
|--------|------|-------------|
| `wallet` | VARCHAR(44) | Primary key - player's wallet |
| `tournaments_played` | INTEGER | Total tournaments entered |
| `tournaments_won` | INTEGER | First place finishes |
| `total_points` | BIGINT | Lifetime POINTS earned |
| `best_finish` | SMALLINT | Best tournament placement |
| `total_hands_played` | BIGINT | Lifetime hands played |
| `total_eliminations` | INTEGER | Lifetime eliminations |
| `last_tournament_id` | UUID | Most recent tournament |
| `last_played_at` | TIMESTAMPTZ | Last activity timestamp |
| `created_at` | TIMESTAMPTZ | First registration |
| `updated_at` | TIMESTAMPTZ | Last stats update |

**Indexes:**
- `idx_player_stats_points` - Leaderboard ranking by total points

---

### agent_live_settings

Real-time slider settings for BASIC/PRO tier agents during live tournaments.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `tournament_id` | UUID | Foreign key to tournaments |
| `wallet` | VARCHAR(44) | Player's wallet address |
| `active_aggression` | SMALLINT | Currently active aggression (1-10) |
| `active_tightness` | SMALLINT | Currently active tightness (1-10) |
| `pending_aggression` | SMALLINT | Slider position (not yet confirmed) |
| `pending_tightness` | SMALLINT | Slider position (not yet confirmed) |
| `confirmed_aggression` | SMALLINT | Confirmed, waiting for next hand |
| `confirmed_tightness` | SMALLINT | Confirmed, waiting for next hand |
| `confirmed_at` | TIMESTAMPTZ | When settings were confirmed |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

**Slider Values:**
- **Aggression (1-10):** 1=passive (check/call), 10=aggressive (bet/raise)
- **Tightness (1-10):** 1=loose (many hands), 10=tight (selective)

**Constraints:**
- Unique on (`tournament_id`, `wallet`)
- All slider values must be between 1 and 10

**Indexes:**
- `idx_live_settings_tournament` - Find all settings for a tournament
- `idx_live_settings_wallet` - Find settings for a player
- `idx_live_settings_confirmed` - Find pending settings to apply

---

### audit_log

Tracks administrative actions for compliance and debugging.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `tournament_id` | UUID | Related tournament (optional) |
| `action` | VARCHAR(50) | Action type (e.g., `start_tournament`, `finalize`) |
| `wallet` | VARCHAR(44) | Actor's wallet address |
| `tx_signature` | VARCHAR(256) | Solana transaction signature |
| `details` | JSONB | Additional action metadata |
| `created_at` | TIMESTAMPTZ | Action timestamp |

**Indexes:**
- `idx_audit_log_tournament` - Filter by tournament
- `idx_audit_log_action` - Filter by action type
- `idx_audit_log_wallet` - Filter by actor
- `idx_audit_log_created_at` - Sort by time (descending)

---

## Relationships

### One-to-Many

- `tournaments` → `registrations`: A tournament has many player registrations
- `tournaments` → `hands`: A tournament has many hands played
- `hands` → `hand_actions`: A hand has many actions
- `hands` → `hand_players`: A hand has many participating players
- `tournaments` → `agent_live_settings`: A tournament has settings for each player
- `tournaments` → `audit_log`: A tournament can have many audit entries

### Many-to-One

- `registrations` → `tournaments`: A registration belongs to one tournament
- `player_stats` → `tournaments` (last_tournament_id): Stats reference the last tournament

---

## Index Strategy

### Query Patterns Optimized

1. **Leaderboard queries:** `idx_player_stats_points` enables fast DESC sorting
2. **Tournament listings:** `idx_tournaments_status` and `idx_tournaments_starts_at`
3. **Player history:** `idx_registrations_wallet` finds all tournaments for a player
4. **Hand replay:** `idx_hands_tournament` + `idx_hand_actions_hand`
5. **Live settings:** `idx_live_settings_confirmed` finds pending settings efficiently

### Performance Considerations

- JSONB columns (`blind_structure`, `payout_structure`, `agent_sliders`) allow flexible schemas
- Denormalized `player_stats` avoids expensive aggregation queries
- `hand_number` is indexed with tournament_id for sequential access
- Encrypted columns (`hole_cards_encrypted`, `agent_prompt_encrypted`) store sensitive data

---

## Data Retention

| Table | Retention Policy |
|-------|------------------|
| `tournaments` | Permanent |
| `registrations` | Permanent |
| `hands` | 90 days after tournament completion |
| `hand_actions` | 90 days after tournament completion |
| `hand_players` | 90 days after tournament completion |
| `player_stats` | Permanent |
| `agent_live_settings` | Deleted on tournament completion |
| `audit_log` | 1 year |

---

## Migrations

Migrations are applied in order:

1. `001_initial_schema.sql` - Core tables
2. `002_phase5_settlement.sql` - On-chain settlement tracking
3. `003_agent_live_settings.sql` - Real-time slider controls

Run migrations with:
```bash
psql $DATABASE_URL -f backend/db/migrations/001_initial_schema.sql
psql $DATABASE_URL -f backend/db/migrations/002_phase5_settlement.sql
psql $DATABASE_URL -f backend/db/migrations/003_agent_live_settings.sql
```
