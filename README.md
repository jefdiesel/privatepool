# SOLANA POKER AGENT ARENA

## Ultimate Context Declaration for AI-Assisted Development

> **Purpose**: This document serves as the authoritative context declaration for building a multiplayer online poker tournament system where AI agents compete on behalf of users for immutable, forgery-proof POINTS on the Solana blockchain.

> **Philosophy**: *"Context management is everything. There's a billion dollars inside of that model, and your job is to prompt it out."* — This README provides the complete context any AI coding assistant or developer needs to build this application end-to-end.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Documentation Index](#documentation-index)
4. [Key Wallet Addresses](#key-wallet-addresses)
5. [Core Concepts](#core-concepts)
6. [Development Phases](#development-phases)
7. [Anti-Patterns](#anti-patterns)
8. [Error Handling Strategy](#error-handling-strategy)
9. [State Machines](#state-machines)
10. [Environment Configuration](#environment-configuration)
11. [Prompt Caching Implementation](#prompt-caching-implementation)
12. [Logging Standards](#logging-standards)
13. [Pinned Dependencies](#pinned-dependencies)
14. [Example: Complete Hand Execution](#example-complete-hand-execution)
15. [Appendices](#appendices)

---

## Project Overview

### What We're Building

A **trustless, blockchain-verified poker tournament platform** where:

- Users connect Solana wallets and register AI agents to compete on their behalf
- Tournaments run autonomously — agents make all decisions via Claude (model: `claude-sonnet-4-5-20250929`)
- Results are cryptographically verified and stored on-chain
- POINTS (SPL tokens) are awarded based on tournament performance
- All randomness is provably fair via blockhash commitment

### Core Value Propositions

| Stakeholder | Value |
|-------------|-------|
| **Players** | Compete without manual play; customize AI strategy; earn verifiable POINTS |
| **Spectators** | Watch agents battle in real-time (owner-only for their agent) |
| **Admin** | Full tournament control; transparent economics; customizable payout structures |
| **Ecosystem** | Provably fair gaming; on-chain verification; new DeFi primitive |

### Key Differentiators

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL POKER                            │
│  • Manual play required                                         │
│  • Trust centralized platforms                                  │
│  • Results stored in private databases                          │
│  • No strategy customization                                    │
└─────────────────────────────────────────────────────────────────┘
                              vs
┌─────────────────────────────────────────────────────────────────┐
│                    POKER AGENT ARENA                            │
│  • AI plays on your behalf                                      │
│  • Trustless verification on Solana                             │
│  • Results hash stored on-chain                                 │
│  • Customize your agent's strategy via prompts                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Node.js 20.x
- Python 3.11+
- Rust + Solana CLI + Anchor 0.30+
- PostgreSQL (local or Neon)
- Redis (local or Upstash)

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd poker-agent-arena

# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# Smart Contracts
cd contracts && anchor test
```

### Environment Variables

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete environment configuration.

---

## Documentation Index

| Document | Contents |
|----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, component diagrams, tech stack |
| [docs/SMART_CONTRACT.md](docs/SMART_CONTRACT.md) | Anchor program specification, PDAs, instructions |
| [docs/BACKEND.md](docs/BACKEND.md) | FastAPI services, AI engine, tournament engine, real-time system, security, API reference |
| [docs/FRONTEND.md](docs/FRONTEND.md) | Next.js pages, components, state management, WebSocket events |
| [docs/DATA_MODELS.md](docs/DATA_MODELS.md) | PostgreSQL schema, Redis cache structure |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Environment setup, deployment checklist, cost analysis |
| [docs/TESTING.md](docs/TESTING.md) | Unit tests, integration tests, load testing |
| [docs/LEGAL.md](docs/LEGAL.md) | Terms of Service, compliance, restricted jurisdictions |

---

## Key Wallet Addresses

### Development (Devnet)

| Purpose | Address |
|---------|---------|
| **Program ID** | `34MhwbaRczNA8Zt4H8rUwPV4o2MsAtYd8hQhNno3QaLN` |

### Production (Mainnet)

| Purpose | Address |
|---------|---------|
| **Admin Wallet** | `BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m` |
| **Agent Registration Fees Wallet** | `CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm` |

---

## Core Concepts

### Agent Tiers

| Tier | Cost | Features |
|------|------|----------|
| **FREE** | 0 SOL | Base engine only (comprehensive poker AI foundation) |
| **BASIC** | 0.1 SOL | Base engine + **strategy sliders only** (aggression, bluff frequency, tightness, position awareness) |
| **PRO** | 1 SOL | Base engine + sliders + **freeform strategy tuning system prompt** (cached for the agent) |

> **Important**: The 0.1 SOL tier grants access to slider-based customization only. Freeform text strategy prompts require the 1 SOL PRO tier.

### Blind Structure & Antes

Blind structures are fully customizable per tournament by the admin. Each level specifies:
- Small blind amount
- Big blind amount
- **Ante amount (paid by big blind only)**
- Level duration in minutes

> **Ante Implementation**: Only the player in the big blind position pays the ante for that hand. The ante amount is customizable per level, just like blinds and level time. This simplifies collection and maintains the ante's intended effect of increasing action while reducing complexity.

Example blind structure:
```python
BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=6)
BlindLevel(level=4, small_blind=100, big_blind=200, ante=25, duration_minutes=6)  # BB pays 200+25=225
BlindLevel(level=7, small_blind=300, big_blind=600, ante=75, duration_minutes=6)  # BB pays 600+75=675
```

### Payout Structure

Payout structures are **fully customizable by the admin** when creating a tournament. The admin specifies exactly how many positions pay and how many POINTS each position receives.

Example payout structure (admin-defined):
```python
payout_structure = {
    1: 5000,   # 1st place
    2: 3000,   # 2nd place
    3: 2000,   # 3rd place
    4: 1000,   # 4th place
    5: 500,    # 5th place
    6: 500,    # 6th place
}
```

The admin has complete flexibility to:
- Determine how many positions receive payouts
- Set exact POINTS amounts per position
- Create top-heavy or flat payout structures
- Adjust based on tournament size and type

### AI Model Configuration

| Context | Model ID |
|---------|----------|
| **Production** | `claude-sonnet-4-5-20250929` |
| **Development (cost savings)** | `claude-sonnet-4-5-20250929` (or `claude-3-haiku-20240307` for testing) |

### Rate Limits

| Endpoint/Action | Limit | Window |
|-----------------|-------|--------|
| Registration | 5 requests | per minute per wallet |
| Agent update | 10 requests | per minute per wallet |
| WebSocket connections | 3 concurrent | per wallet |
| AI decisions (per tournament) | Determined by budget | per tournament |
| AI API calls (global) | 1000 requests | per minute (Anthropic tier dependent) |

### Budget Tracking

Budget protection prevents runaway API costs:

```python
# Budget calculation
expected_cost = (expected_decisions * avg_tokens_per_decision / 1000) * cost_per_1k_tokens
budget_cap = expected_cost * BUDGET_MULTIPLIER  # 3.0x

# Per-decision tracking
async def record_usage(tournament_id: str, input_tokens: int, output_tokens: int):
    """Track actual token usage and cost per decision."""
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K   # $0.003 for Sonnet
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K  # $0.015 for Sonnet
    total_cost = input_cost + output_cost
    await redis.incrbyfloat(f"spent:{tournament_id}", total_cost)

# Budget check before each API call
async def can_make_call(tournament_id: str) -> bool:
    budget = float(await redis.get(f"budget:{tournament_id}") or 0)
    spent = float(await redis.get(f"spent:{tournament_id}") or 0)
    return spent < budget
```

### Hand History Storage

Hand history is stored in PostgreSQL with the following structure:

1. **`hands` table**: Core hand metadata (tournament, table, hand number, blinds, community cards, pot size, timestamps)
2. **`hand_actions` table**: Individual actions (sequence, wallet, betting round, action type, amount, decision time, tokens used)
3. **`hand_players` table**: Per-hand player data (seat position, hole cards, starting/ending stack, winnings, hand rank)

**Storage Strategy**:
- Full hand history stored in PostgreSQL for queryability and replay
- SHA-256 hash of complete results stored on-chain for verification
- Hand actions include AI decision metadata (decision time, tokens used) for analytics
- Hole cards encrypted at rest, only decrypted for owner view or showdown broadcast

---

## Development Phases

### Phase 1: Foundation

**Deliverables:**

#### Smart Contract
- [ ] ArenaConfig account
- [ ] Tournament account
- [ ] PlayerRegistration account
- [ ] PlayerStats account
- [ ] Initialize instruction
- [ ] CreateTournament instruction
- [ ] RegisterPlayer instruction
- [ ] Unit tests for all instructions

#### Backend Core
- [ ] FastAPI project setup
- [ ] PostgreSQL schema + migrations
- [ ] Redis connection
- [ ] Solana service (RPC connection)
- [ ] Basic health endpoints

#### Frontend Shell
- [ ] Next.js project setup
- [ ] Tailwind configuration
- [ ] Wallet adapter integration
- [ ] Basic routing structure
- [ ] Landing page

**Exit Criteria:**
- Can create tournament on devnet
- Can register player on devnet
- Frontend connects to Phantom wallet

---

### Phase 2: Poker Engine

**Deliverables:**

#### Poker Logic
- [ ] Deck implementation with provably fair shuffle
- [ ] Hand evaluator (all hand rankings)
- [ ] Betting round logic
- [ ] Side pot calculation
- [ ] Texas Hold'em rules enforcement

#### Tournament Logic
- [ ] Table creation and seating
- [ ] Blind structure progression (with BB-only antes)
- [ ] Table balancing algorithm
- [ ] Elimination tracking
- [ ] Final standings calculation

#### Testing
- [ ] Unit tests for hand evaluator
- [ ] Integration tests for betting rounds
- [ ] Simulation tests (1000 hands)

**Exit Criteria:**
- Can simulate complete tournament offline
- All poker rules correctly enforced
- Table balancing works correctly

---

### Phase 3: AI Integration

**Deliverables:**

#### Agent System
- [ ] Base agent prompt (~1,500 tokens)
- [ ] Prompt caching implementation
- [ ] Custom prompt handling (tiers - sliders for BASIC, freeform for PRO)
- [ ] Slider personality system
- [ ] Game state formatter
- [ ] Action parser and validator

#### Decision Engine
- [ ] Claude API integration (model: `claude-sonnet-4-5-20250929`)
- [ ] 5s/10s timeout handling
- [ ] Budget tracking (input + output tokens)
- [ ] Error handling and fallbacks
- [ ] Decision logging

#### Integration
- [ ] Connect AI to poker engine
- [ ] End-to-end hand simulation
- [ ] Performance benchmarking

**Exit Criteria:**
- AI makes valid decisions
- Prompt caching achieving 85%+ savings
- Decision latency within targets

---

### Phase 4: Real-Time & Frontend

**Deliverables:**

#### WebSocket System
- [ ] Socket.IO server setup
- [ ] WebSocket authentication flow
- [ ] Tournament event broadcasting
- [ ] Table-specific subscriptions
- [ ] Player-specific hole card delivery
- [ ] Reconnection handling

#### Frontend Pages
- [ ] Tournament list page
- [ ] Tournament detail page
- [ ] Registration flow (all tiers with correct feature access)
- [ ] Agent customization page (sliders for BASIC, sliders + prompt for PRO)
- [ ] Live tournament view
- [ ] Leaderboard page

#### Admin Dashboard
- [ ] Tournament creation form
- [ ] Blind structure templates (with customizable BB-only antes)
- [ ] Payout structure configuration (fully admin-customizable)
- [ ] Tournament monitoring
- [ ] Spectator mode (showdown only)

**Exit Criteria:**
- Full tournament visible in real-time
- All user flows working
- Admin can create and monitor tournaments

---

### Phase 5: On-Chain Settlement

**Deliverables:**

#### Smart Contract Finalization
- [ ] StartTournament instruction
- [ ] FinalizeTournament instruction
- [ ] RecordPlayerResult instruction
- [ ] DistributePoints instruction
- [ ] POINTS SPL token mint

#### Backend Integration
- [ ] Tournament start transaction
- [ ] Results hash generation
- [ ] Finalization transaction
- [ ] POINTS distribution

#### Verification
- [ ] Prompt hash verification
- [ ] Results hash verification
- [ ] Blockhash seed verification

**Exit Criteria:**
- Full tournament settles on-chain
- POINTS distributed correctly
- All verifications passing

---

### Phase 6: Testing & Launch

**Deliverables:**

#### Testing
- [ ] Full integration tests
- [ ] Load testing (54 players)
- [ ] Security audit (basic)
- [ ] Devnet beta testing

#### Documentation
- [ ] API documentation
- [ ] User guide
- [ ] Admin guide
- [ ] Terms of Service

#### Launch
- [ ] Mainnet deployment
- [ ] Monitoring setup
- [ ] First tournament (27 players)

**Exit Criteria:**
- System handles 27-player tournament
- No critical bugs
- Documentation complete
- First tournament successful

---

## Anti-Patterns

### Smart Contract Anti-Patterns

```
❌ NEVER store full hand history on-chain
   → Cost: ~$80-120 per tournament vs $4.50 with hash only
   → Solution: Store SHA-256 hash on-chain, full data in PostgreSQL

❌ NEVER use PDA seeds that could collide
   → Bad:  seeds = [b"player", wallet.as_ref()]  // Collides across tournaments
   → Good: seeds = [b"registration", tournament.as_ref(), wallet.as_ref()]

❌ NEVER process external calls before state changes
   → Vulnerable to re-entrancy attacks
   → Always: Update state → Then transfer tokens

❌ NEVER trust client-provided timestamps
   → Use Clock::get()?.unix_timestamp for all on-chain time

❌ NEVER store mutable data in instruction data
   → All mutable state belongs in accounts
```

### AI Decision Anti-Patterns

```
❌ NEVER retry Claude API without exponential backoff
   → Bad:  for i in range(5): call_claude()
   → Good: retry with delays [1s, 2s, 4s, 8s, 16s] + jitter

❌ NEVER expose raw prompts to clients
   → Custom prompts are competitive advantages
   → Only expose: agent name, tier, sliders (not freeform text)

❌ NEVER trust AI output without validation
   → Claude could return: {"action": "raise", "amount": -500}
   → Always validate: action ∈ valid_actions, amount ≥ min_raise

❌ NEVER make speculative API calls
   → Don't pre-compute "what if they call" decisions
   → Wastes tokens and budget

❌ NEVER block on AI response without timeout
   → Always: asyncio.wait_for(call_claude(), timeout=10)
   → Fallback: fold/check if timeout exceeded
```

### Backend Anti-Patterns

```
❌ NEVER expose Claude API key to frontend
   → All AI calls must go through backend
   → Frontend only sends: game state request → receives: action taken

❌ NEVER process hands across tables synchronously
   → Tables are independent—parallelize with asyncio.gather()

❌ NEVER store sensitive data in Redis without TTL
   → Session tokens, rate limits: always set expiry
   → Prevents memory leaks and stale data

❌ NEVER skip database transactions for multi-step writes
   → Bad:  insert_hand(); insert_actions();  // Partial failure risk
   → Good: async with db.transaction(): ...

❌ NEVER log full prompts or hole cards at INFO level
   → Prompts: competitive secrets
   → Hole cards: only log at DEBUG, never in production
```

### Frontend Anti-Patterns

```
❌ NEVER poll for real-time data
   → Bad:  setInterval(() => fetch('/api/table'), 1000)
   → Good: WebSocket subscription with automatic reconnect

❌ NEVER store wallet private keys or signatures
   → Signatures are one-time use for auth
   → Never persist to localStorage/sessionStorage

❌ NEVER show opponent hole cards before showdown
   → Even if data is available, UI must hide until showdown event

❌ NEVER make Solana RPC calls directly from browser
   → Route through backend to: hide RPC keys, rate limit, add caching

❌ NEVER assume WebSocket is connected
   → Always check connection state before sending
   → Queue messages during reconnection
```

### Tournament Logic Anti-Patterns

```
❌ NEVER move players during an active hand
   → Wait for hand completion, then balance tables

❌ NEVER process eliminations before pot distribution
   → Player might win side pot despite losing main pot

❌ NEVER skip blind level checks between hands
   → Level could advance mid-hand; apply at next hand start

❌ NEVER allow registration after tournament starts
   → Creates unfair late-position advantages
   → No late registration per requirements

❌ NEVER modify agent prompts after registration closes
   → Lock prompts at tournament start, verify hash matches on-chain
```

---

## Error Handling Strategy

### Graceful Degradation Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING HIERARCHY                             │
└─────────────────────────────────────────────────────────────────────────┘

LEVEL 1: AI Decision Failure
├── Cause: Claude API timeout, rate limit, malformed response
├── Detection: asyncio.TimeoutError, anthropic.APIError, JSON parse fail
├── Response: Return conservative action (check if possible, else fold)
├── Logging: WARN with full context (tournament, hand, player, error)
└── User Impact: None visible—game continues normally

LEVEL 2: WebSocket Disconnection
├── Cause: Network issues, server restart, idle timeout
├── Detection: Socket.IO disconnect event
├── Response: Auto-reconnect with exponential backoff [1s, 2s, 4s, 8s, 16s]
├── UI: Show "Reconnecting..." overlay, disable actions
└── Recovery: Re-subscribe to tournament/table rooms on reconnect

LEVEL 3: Database Write Failure
├── Cause: Connection pool exhausted, constraint violation, timeout
├── Detection: SQLAlchemy exceptions
├── Response:
│   ├── Critical (registration): Return 503, retry client-side
│   ├── Non-critical (hand history): Queue to Redis, process async
├── Logging: ERROR with query and parameters (sanitized)
└── Recovery: Background worker processes Redis queue

LEVEL 4: Solana RPC Failure
├── Cause: Node overloaded, network partition, rate limit
├── Detection: SolanaRpcError, timeout
├── Response: Retry with backup RPC endpoint (Helius → public fallback)
├── Circuit Breaker: After 3 failures, mark primary unhealthy for 60s
└── User Impact: Transaction delayed, show "Processing..." state

LEVEL 5: Unrecoverable Error
├── Cause: Smart contract bug, critical state corruption
├── Detection: Anchor program error, assertion failure
├── Response: Pause tournament, alert admin, log everything
├── User Notification: "Tournament paused due to technical issue"
└── Recovery: Manual intervention required
```

### Error Response Format

```typescript
// Standard error response (all API endpoints)
interface ErrorResponse {
  error: {
    code: string;           // Machine-readable: "TOURNAMENT_FULL"
    message: string;        // Human-readable: "This tournament is full"
    details?: {
      field?: string;       // For validation errors
      limit?: number;       // For rate limit errors
      retryAfter?: number;  // Seconds until retry allowed
    };
  };
  requestId: string;        // For support tickets
}
```

### Error Codes

Error codes are organized by category with 4-digit codes:

| Category | Range | Examples |
|----------|-------|----------|
| **Authentication** | 1000-1099 | `1001` WALLET_NOT_CONNECTED, `1002` INVALID_SIGNATURE, `1003` SESSION_EXPIRED |
| **Tournament** | 2000-2099 | `2001` TOURNAMENT_NOT_FOUND, `2002` TOURNAMENT_FULL, `2003` REGISTRATION_CLOSED, `2004` ALREADY_REGISTERED, `2005` TOURNAMENT_NOT_STARTED |
| **Agent** | 3000-3099 | `3001` INVALID_TIER, `3002` PROMPT_TOO_LONG, `3003` AGENT_LOCKED, `3004` SLIDER_OUT_OF_RANGE |
| **Payment** | 4000-4099 | `4001` INSUFFICIENT_BALANCE, `4002` TRANSACTION_FAILED, `4003` INVALID_PAYMENT_AMOUNT |
| **System** | 5000-5099 | `5001` RATE_LIMITED, `5002` SERVICE_UNAVAILABLE, `5003` INTERNAL_ERROR, `5004` BUDGET_EXCEEDED |

---

## State Machines

### Tournament State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      TOURNAMENT STATE MACHINE                            │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   CREATED    │
                              │              │
                              │ Admin creates│
                              │ tournament   │
                              └──────┬───────┘
                                     │ open_registration()
                                     ▼
                   ┌─────────────────────────────────┐
                   │          REGISTRATION           │
                   │                                 │
                   │  • Players can register         │
                   │  • Agents can be configured     │
                   │  • Max players enforced         │
                   └─────────────┬───────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              │ cancel()         │ start()          │
              ▼                  ▼                  │
    ┌──────────────┐   ┌──────────────────┐        │
    │  CANCELLED   │   │    STARTING      │        │
    │              │   │                  │        │
    │ Refunds if   │   │ • Lock agents    │        │
    │ applicable   │   │ • Commit RNG seed│        │
    └──────────────┘   │ • Seat players   │        │
                       └────────┬─────────┘        │
                                │                  │
                                ▼                  │
                       ┌──────────────────┐        │
                       │   IN_PROGRESS    │◄───────┘
                       │                  │   (if min players not met,
                       │ • Hands dealt    │    can cancel instead)
                       │ • AI decisions   │
                       │ • Eliminations   │
                       │ • Table balance  │
                       └────────┬─────────┘
                                │
                                │ (players_remaining == 1)
                                ▼
                       ┌──────────────────┐
                       │    COMPLETED     │
                       │                  │
                       │ • Results hash   │
                       │ • POINTS awarded │
                       │ • Stats updated  │
                       └──────────────────┘

Valid Transitions:
  CREATED → REGISTRATION       (admin action)
  CREATED → CANCELLED          (admin action)
  REGISTRATION → STARTING      (admin action, min players met)
  REGISTRATION → CANCELLED     (admin action)
  STARTING → IN_PROGRESS       (automatic, after seating)
  IN_PROGRESS → COMPLETED      (automatic, one player left)
```

### Hand State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HAND STATE MACHINE                               │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   WAITING    │  (Between hands, button moving)
└──────┬───────┘
       │ deal()
       ▼
┌──────────────┐
│   DEALING    │  Hole cards distributed, BB posts blind + ante
└──────┬───────┘
       │
       ▼
┌──────────────┐     all_fold()     ┌──────────────────┐
│   PREFLOP    │ ─────────────────► │ WINNER_DETERMINED│
│              │                    │                  │
│ Blinds posted│                    │ Last player wins │
│ BB pays ante │                    │ No showdown      │
│ First betting│                    └──────────────────┘
└──────┬───────┘                           ▲
       │ betting_complete()                │
       ▼                                   │
┌──────────────┐     all_fold()            │
│    FLOP      │ ──────────────────────────┤
│              │                           │
│ 3 community  │                           │
│ cards dealt  │                           │
└──────┬───────┘                           │
       │ betting_complete()                │
       ▼                                   │
┌──────────────┐     all_fold()            │
│    TURN      │ ──────────────────────────┤
│              │                           │
│ 4th community│                           │
│ card dealt   │                           │
└──────┬───────┘                           │
       │ betting_complete()                │
       ▼                                   │
┌──────────────┐     all_fold()            │
│    RIVER     │ ──────────────────────────┤
│              │                           │
│ 5th community│                           │
│ card dealt   │                           │
└──────┬───────┘                           │
       │ betting_complete()                │
       ▼                                   │
┌──────────────┐                           │
│   SHOWDOWN   │ ──────────────────────────┘
│              │     evaluate_hands()
│ Hands reveal │
│ Best wins    │
└──────────────┘

Notes:
- "all_fold()" = all but one player folds
- "betting_complete()" = all active players have acted and bets are matched
- From any betting state, if all players are all-in, skip to SHOWDOWN
```

---

## Environment Configuration

### Environment-Specific Behavior

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Solana Network** | localhost/devnet | devnet | mainnet-beta |
| **RPC Endpoint** | localhost:8899 | Helius devnet | Helius mainnet |
| **Claude Model** | `claude-3-haiku-20240307` | `claude-sonnet-4-5-20250929` | `claude-sonnet-4-5-20250929` |
| **Decision Timeout** | 30s (debugging) | 5s / 10s | 5s / 10s |
| **Budget Multiplier** | 10x (testing) | 3x | 3x |
| **CORS Origins** | localhost:3000 | staging.domain.com | domain.com |
| **Log Level** | DEBUG | INFO | INFO |
| **Error Details** | Full stack traces | Sanitized | Sanitized |
| **Database** | Local PostgreSQL | Neon (staging branch) | Neon (main branch) |
| **Redis** | Local Redis | Upstash (staging) | Upstash (production) |
| **SSL** | Disabled | Enabled | Enabled |
| **Rate Limits** | Disabled | Relaxed (5x prod) | Enforced |

### Feature Flags

```python
class FeatureFlags:
    """Environment-specific feature toggles."""

    # Development only
    SKIP_WALLET_VERIFICATION: bool = False  # Bypass signature checks
    MOCK_CLAUDE_RESPONSES: bool = False     # Use deterministic test responses
    INSTANT_BLINDS: bool = False            # Skip blind level timers

    # Staging + Production
    ENABLE_PROMPT_CACHING: bool = True      # Anthropic prompt caching
    ENABLE_BUDGET_LIMITS: bool = True       # Per-tournament API budget
    ENABLE_RATE_LIMITING: bool = True       # API rate limits

    # Gradual rollout
    ENABLE_54_PLAYER_TOURNAMENTS: bool = False  # Phase 2 feature
    ENABLE_SPECTATOR_MODE: bool = False         # Admin-only for now
```

---

## Prompt Caching Implementation

### Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ANTHROPIC PROMPT CACHING                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT (Cached)                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Base Engine (~1,500 tokens)                                       │  │
│  │  • Pot odds, equity, EV calculations                              │  │
│  │  • Position awareness rules                                        │  │
│  │  • Hand categories and ranges                                      │  │
│  │  • Tournament adjustments (ICM)                                    │  │
│  │  • Betting patterns                                                │  │
│  │                                                                    │  │
│  │  cache_control: {"type": "ephemeral"}  ◄── CACHE THIS              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DYNAMIC CONTENT (Not Cached)                                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Custom Prompt (0-500 tokens) - PRO tier only                      │  │
│  │  • Personality sliders (BASIC + PRO)                               │  │
│  │  • User freeform instructions (PRO only)                           │  │
│  │                                                                    │  │
│  │  Game State (~300 tokens)                                          │  │
│  │  • Current hand info                                               │  │
│  │  • Player stacks                                                   │  │
│  │  • Action history                                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Cost per Tournament (27 players, ~1000 decisions)

- Without caching: ~$24.00
- With caching: ~$7.20 (70% savings)

---

## Logging Standards

### Log Levels

```
ERROR - System failures requiring immediate attention
├── Database connection failures
├── Smart contract transaction failures
├── Claude API errors (after retries exhausted)
├── Budget exceeded
└── Unhandled exceptions

WARN - Issues that don't stop execution but need monitoring
├── Claude API retries
├── Slow decisions (>4s)
├── WebSocket reconnections
├── Rate limit approaches (>80% of limit)
└── Validation failures (malformed requests)

INFO - Normal operational events
├── Tournament lifecycle (created, started, completed)
├── Player registration
├── Eliminations
├── Level changes
├── Table breaks/merges
└── POINTS distribution

DEBUG - Detailed diagnostic info (dev/staging only)
├── Individual AI decisions
├── Hand states
├── WebSocket message details
├── Query execution times
└── Cache hit/miss details
```

### Sensitive Data Handling

**Never log:**
- `agent_prompt` (competitive advantage)
- `custom_instructions` (user secrets)
- `wallet_private_key`
- `api_keys`
- `hole_cards` during active hand (INFO level)
- `session_tokens`

---

## Pinned Dependencies

### Backend (Python)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "0.109.x"
anthropic = "0.18.x"
sqlalchemy = "2.0.x"
redis = "5.0.x"
solana = "0.32.x"
```

### Frontend (Node)

```json
{
  "engines": { "node": "20.x" },
  "dependencies": {
    "next": "14.1.x",
    "@solana/web3.js": "1.89.x",
    "zustand": "4.5.x",
    "socket.io-client": "4.7.x"
  }
}
```

### Smart Contracts (Rust/Anchor)

```toml
[dependencies]
anchor-lang = "0.30.0"
anchor-spl = "0.30.0"
```

---

## Example: Complete Hand Execution

See [docs/BACKEND.md](docs/BACKEND.md#example-complete-hand-execution) for a detailed trace of a complete hand from deal to showdown, including:

- Deck shuffling with provably fair RNG
- Blind and ante posting (BB pays ante)
- AI decision timing and caching
- Side pot calculation
- WebSocket broadcast events

---

## Appendices

### Appendix A: Quick Reference

#### Key Constants

```typescript
const CONSTANTS = {
  TABLE_SIZE: 9,
  DECISION_TIMEOUT_NORMAL: 5,      // seconds
  DECISION_TIMEOUT_ALL_IN: 10,     // seconds
  TIER_FREE_COST: 0,               // SOL
  TIER_BASIC_COST: 0.1,            // SOL - sliders only
  TIER_PRO_COST: 1.0,              // SOL - sliders + freeform prompt
  BUDGET_MULTIPLIER: 3.0,
  INITIAL_MAX_PLAYERS: 27,
  TARGET_MAX_PLAYERS: 54,
};
```

#### Common Commands

```bash
# Development
cd frontend && npm run dev
cd backend && uvicorn main:app --reload
cd contracts && anchor test

# Deployment
anchor deploy --provider.cluster mainnet
vercel --prod
railway up

# Database
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI-powered bot that makes poker decisions for a user |
| **All-In** | Betting all remaining chips; cannot take further action |
| **Ante** | Forced bet paid by big blind only before each hand; amount customizable per level |
| **Blockhash Commitment** | Using a Solana blockhash as a verifiable random seed |
| **Button (BTN)** | Dealer position; acts last post-flop, best position |
| **ICM** | Independent Chip Model — tournament equity calculation |
| **PDA** | Program Derived Address — deterministic Solana account address |
| **POINTS** | SPL token awarded for tournament performance |
| **Pot Odds** | Ratio of call amount to total pot size |
| **Slider** | Adjustable personality parameter (aggression, bluff frequency, etc.) |
| **SPR** | Stack-to-Pot Ratio — key metric for commitment decisions |
| **Tier** | Agent customization level (FREE / BASIC / PRO) |

### Appendix C: Placeholder Sections

The following sections require additional specification:

#### Schema Versioning & Migration Strategy

```
[PLACEHOLDER]

This section will define:
- Database schema versioning approach
- Migration strategy for zero-downtime deployments
- Rollback procedures
- Data migration best practices for Neon PostgreSQL
- Alembic configuration and conventions
```

#### Disaster Recovery Plan

```
[PLACEHOLDER]

This section will define:
- Backup frequency and retention (PostgreSQL, Redis)
- Recovery Point Objective (RPO) and Recovery Time Objective (RTO)
- Failover procedures for each service
- Tournament state recovery procedures
- On-chain vs off-chain data reconciliation
- Incident response playbook
```

#### WebSocket Authentication Flow

```
[PLACEHOLDER]

This section will define:
- WebSocket connection authentication sequence
- Token/signature verification on connect
- Session management and refresh
- Reconnection authentication
- Rate limiting for WebSocket connections
- Security considerations for real-time data
```

---

**END OF CONTEXT DECLARATION**

*This document should be the first file read by any AI assistant or developer working on this project. Keep it updated as the project evolves.*
