# Testing Strategy

This document covers unit testing, integration testing, and load testing for the Poker Agent Arena.

---

## Table of Contents

1. [Coverage Requirements](#coverage-requirements)
2. [Integration Test Scenarios](#integration-test-scenarios)
3. [Load Testing Targets](#load-testing-targets)
4. [Test Data Fixtures](#test-data-fixtures)

---

## Coverage Requirements

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      UNIT TEST COVERAGE TARGETS                          │
└─────────────────────────────────────────────────────────────────────────┘

100% REQUIRED (zero tolerance):
├── Hand Evaluator
│   ├── All 10 hand rankings
│   ├── Tie-breaking logic
│   ├── 7-card to 5-card selection
│   └── Edge cases: wheel straight, steel wheel, etc.
│
├── Betting Logic
│   ├── Min-raise calculation
│   ├── All-in handling
│   ├── Side pot creation
│   ├── BB-only ante posting
│   └── Pot limit enforcement (N/A for no-limit, but validate no negative bets)
│
├── AI Action Parser
│   ├── Valid JSON responses
│   ├── Invalid JSON (fallback to fold)
│   ├── Out-of-range amounts
│   ├── Invalid actions for game state
│   └── Missing fields
│
└── Smart Contract Instructions
    ├── All happy paths
    ├── All error conditions
    ├── Authorization checks
    ├── Tier payment validation (0 / 0.1 / 1 SOL)
    └── Account validation

90%+ TARGET:
├── Tournament Manager
├── Table Balancing
├── WebSocket Event Handlers
├── API Endpoints
└── Budget Tracking (input + output token costs)
```

---

## Integration Test Scenarios

```python
# tests/integration/test_tournament_e2e.py

class TestTournamentE2E:
    """End-to-end tournament scenarios."""

    async def test_27_player_tournament_completion(self):
        """Full tournament from registration to POINTS distribution."""
        # Setup: 27 mock players with various tiers
        # Execute: Run tournament to completion
        # Verify: Winner determined, POINTS distributed, on-chain state correct

    async def test_all_in_with_three_way_side_pot(self):
        """Complex side pot scenario."""
        # Player A: 1000 chips, all-in
        # Player B: 2000 chips, all-in
        # Player C: 5000 chips, calls
        # Verify: Main pot (3000) and side pot (2000) distributed correctly

    async def test_table_break_and_rebalance(self):
        """Table consolidation when players bust."""
        # Start: 3 tables, 27 players
        # Bust players until 18 remain
        # Verify: Tables balanced, no player moved mid-hand

    async def test_budget_exceeded_mid_tournament(self):
        """API budget protection."""
        # Set artificially low budget
        # Run hands until budget exceeded
        # Verify: Agents fold gracefully, tournament continues

    async def test_websocket_reconnection_during_hand(self):
        """Client disconnect/reconnect."""
        # Connect client, subscribe to table
        # Disconnect mid-hand
        # Reconnect after 5 seconds
        # Verify: Client receives current state, no missed actions

    async def test_rpc_failover(self):
        """Solana RPC redundancy."""
        # Primary RPC returns errors
        # Verify: Automatic failover to secondary
        # Verify: Transactions complete successfully

    async def test_bb_only_ante_collection(self):
        """Verify only big blind pays ante."""
        # Setup: Level with ante enabled
        # Execute: Deal hand
        # Verify: Only BB position posts ante
        # Verify: Pot size = SB + BB + ante (not ante * players)

    async def test_tier_feature_access(self):
        """Verify tier-based feature access."""
        # FREE: Only base engine
        # BASIC: Base + sliders, no freeform prompt
        # PRO: Base + sliders + freeform prompt
        # Verify: Prompt hash only populated for PRO tier freeform
```

---

## Load Testing Targets

```yaml
# k6 load test configuration

scenarios:
  tournament_simulation:
    executor: constant-vus
    vus: 54  # Maximum players
    duration: 30m

thresholds:
  # API latency
  http_req_duration:
    - p(95) < 500   # 95th percentile under 500ms
    - p(99) < 1000  # 99th percentile under 1s

  # AI decision latency (custom metric)
  ai_decision_latency:
    - p(50) < 2000  # Median under 2s
    - p(95) < 4000  # 95th under 4s
    - p(99) < 5000  # 99th under 5s (timeout threshold)

  # WebSocket delivery
  ws_message_latency:
    - p(95) < 100   # 95th percentile under 100ms
    - p(99) < 250   # 99th percentile under 250ms

  # Error rate
  http_req_failed:
    - rate < 0.01   # Less than 1% errors
```

---

## Test Data Fixtures

```python
# tests/fixtures/hands.py

# Predefined hand scenarios for deterministic testing

HAND_FIXTURES = {
    "royal_flush": {
        "hole": ["As", "Ks"],
        "community": ["Qs", "Js", "Ts", "2d", "3c"],
        "expected_rank": HandRank.ROYAL_FLUSH,
    },
    "wheel_straight": {
        "hole": ["Ah", "2d"],
        "community": ["3s", "4c", "5h", "Kd", "Qc"],
        "expected_rank": HandRank.STRAIGHT,
        "expected_high": 5,  # Wheel: A-2-3-4-5, 5 is high
    },
    "split_pot_scenario": {
        "players": [
            {"hole": ["Ah", "Kh"], "expected_rank": HandRank.TWO_PAIR},
            {"hole": ["Ad", "Kd"], "expected_rank": HandRank.TWO_PAIR},
        ],
        "community": ["As", "Ks", "5c", "5d", "2h"],
        "expected_winners": 2,  # Split pot
    },
}

# Blind structure fixtures
BLIND_FIXTURES = {
    "turbo_with_antes": [
        {"level": 1, "sb": 25, "bb": 50, "ante": 0, "duration": 6},
        {"level": 2, "sb": 50, "bb": 100, "ante": 0, "duration": 6},
        {"level": 3, "sb": 75, "bb": 150, "ante": 0, "duration": 6},
        {"level": 4, "sb": 100, "bb": 200, "ante": 25, "duration": 6},  # BB pays 225
        {"level": 5, "sb": 150, "bb": 300, "ante": 50, "duration": 6},  # BB pays 350
    ],
}

# Admin-customized payout fixtures
PAYOUT_FIXTURES = {
    "standard_27": {
        1: 5000,
        2: 3000,
        3: 2000,
        4: 1000,
        5: 500,
        6: 500,
    },
    "top_heavy_27": {
        1: 8000,
        2: 3000,
        3: 1000,
    },
    "flat_27": {
        1: 2000,
        2: 1800,
        3: 1600,
        4: 1400,
        5: 1200,
        6: 1000,
        7: 800,
        8: 600,
        9: 600,
    },
}
```
