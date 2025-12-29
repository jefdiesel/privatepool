# 🎰 SOLANA POKER AGENT ARENA

## Ultimate Context Declaration for AI-Assisted Development

> **Purpose**: This document serves as the authoritative context declaration for building a multiplayer online poker tournament system where AI agents compete on behalf of users for immutable, forgery-proof POINTS on the Solana blockchain.

> **Philosophy**: *"Context management is everything. There's a billion dollars inside of that model, and your job is to prompt it out."* — This README provides the complete context any AI coding assistant or developer needs to build this application end-to-end.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Smart Contract Specification](#4-smart-contract-specification)
5. [Backend Service Specification](#5-backend-service-specification)
6. [Frontend Specification](#6-frontend-specification)
7. [AI Agent System](#7-ai-agent-system)
8. [Tournament Engine](#8-tournament-engine)
9. [Real-Time System](#9-real-time-system)
10. [Data Models](#10-data-models)
11. [Security & Fairness](#11-security--fairness)
12. [API Reference](#12-api-reference)
13. [Deployment Guide](#13-deployment-guide)
14. [Cost Analysis](#14-cost-analysis)
15. [Legal & Compliance](#15-legal--compliance)
16. [Development Phases](#16-development-phases)

---

## 1. Project Overview

### 1.1 What We're Building

A **trustless, blockchain-verified poker tournament platform** where:

- Users connect Solana wallets and register AI agents to compete on their behalf
- Tournaments run autonomously — agents make all decisions via Claude Sonnet 4.5
- Results are cryptographically verified and stored on-chain
- POINTS (SPL tokens) are awarded based on tournament performance
- All randomness is provably fair via blockhash commitment

### 1.2 Core Value Propositions

| Stakeholder | Value |
|-------------|-------|
| **Players** | Compete without manual play; customize AI strategy; earn verifiable POINTS |
| **Spectators** | Watch agents battle in real-time (owner-only for their agent) |
| **Admin** | Full tournament control; transparent economics; no rake complexity |
| **Ecosystem** | Provably fair gaming; on-chain verification; new DeFi primitive |

### 1.3 Key Differentiators

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

## 2. Architecture

### 2.1 High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              USERS                                        │
│                    (Phantom Wallet Connected)                             │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Next.js 14 │  │  Tailwind   │  │   Zustand   │  │ Socket.IO   │      │
│  │ App Router  │  │     CSS     │  │   (State)   │  │   Client    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│                          │                                │               │
│                          │ @solana/wallet-adapter-react   │               │
└──────────────────────────┼────────────────────────────────┼───────────────┘
                           │                                │
         ┌─────────────────┴─────────────────┐              │ WebSocket
         │                                   │              │
         ▼                                   ▼              ▼
┌─────────────────────┐          ┌─────────────────────────────────────────┐
│   SOLANA BLOCKCHAIN │          │              BACKEND (Railway)           │
│   (mainnet-beta)    │          │  ┌─────────────────────────────────────┐ │
│                     │◄────────►│  │           FastAPI (Python)          │ │
│  ┌───────────────┐  │          │  │  ┌──────────┐  ┌──────────────────┐ │ │
│  │ Anchor        │  │          │  │  │Tournament│  │   AI Decision    │ │ │
│  │ Program       │  │          │  │  │  Engine  │  │     Engine       │ │ │
│  │ ┌───────────┐ │  │          │  │  └──────────┘  └──────────────────┘ │ │
│  │ │Tournament │ │  │          │  └─────────────────────────────────────┘ │
│  │ │  PDA      │ │  │          │                    │                     │
│  │ ├───────────┤ │  │          │                    ▼                     │
│  │ │Player     │ │  │          │  ┌─────────────────────────────────────┐ │
│  │ │Stats PDA  │ │  │          │  │         Anthropic Claude            │ │
│  │ ├───────────┤ │  │          │  │         Sonnet 4.5 API              │ │
│  │ │POINTS     │ │  │          │  │    (with 85% prompt caching)        │ │
│  │ │SPL Token  │ │  │          │  └─────────────────────────────────────┘ │
│  │ └───────────┘ │  │          └─────────────────────────────────────────┘
│  └───────────────┘  │                              │
└─────────────────────┘                              │
                                                     ▼
                              ┌─────────────────────────────────────────────┐
                              │              DATA LAYER                      │
                              │  ┌───────────────┐  ┌───────────────────┐   │
                              │  │     Neon      │  │     Upstash       │   │
                              │  │  PostgreSQL   │  │      Redis        │   │
                              │  │  (Primary)    │  │   (Cache/RT)      │   │
                              │  └───────────────┘  └───────────────────┘   │
                              └─────────────────────────────────────────────┘
```

### 2.2 Data Flow: Tournament Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOURNAMENT LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────────────┘

1. CREATION (Admin Only)
   Admin Wallet ──► Anchor Program ──► Create Tournament PDA
                                       • Set blind structure
                                       • Set starting stacks
                                       • Set payout structure
                                       • Set registration deadline

2. REGISTRATION (Users)
   User Wallet ──► Connect Phantom ──► Select Tier ──► Pay SOL
        │                                    │
        │         ┌──────────────────────────┼──────────────────────────┐
        │         │                          │                          │
        ▼         ▼                          ▼                          ▼
   ┌─────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
   │ FREE    │  │ BASIC (0.1 SOL) │  │  PRO (1 SOL)    │  │                 │
   │ Tier 0  │  │     Tier 1      │  │    Tier 2       │  │  On-Chain TX    │
   │         │  │                 │  │                 │  │  • Wallet       │
   │ Base    │  │ Base Engine +   │  │ Base Engine +   │  │  • Tier         │
   │ Engine  │  │ 200 char prompt │  │ Unlimited prompt│  │  • Prompt Hash  │
   │ Only    │  │ + Sliders       │  │ + Sliders       │  │  • Timestamp    │
   └─────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

3. TOURNAMENT START
   Registration Closes ──► Fetch Blockhash ──► Commit Seed ──► Shuffle & Seat
                                   │
                                   ▼
                          ┌───────────────────┐
                          │ Provably Fair RNG │
                          │ blockhash[slot-1] │
                          │ + tournament_id   │
                          └───────────────────┘

4. GAMEPLAY (Autonomous)
   ┌─────────────────────────────────────────────────────────────────────┐
   │  FOR EACH HAND:                                                      │
   │                                                                      │
   │  Deal Cards ──► Betting Rounds ──► Showdown ──► Award Pot           │
   │       │              │                                               │
   │       │              ▼                                               │
   │       │    ┌─────────────────────────────────────────┐              │
   │       │    │  FOR EACH DECISION:                      │              │
   │       │    │                                          │              │
   │       │    │  Build Context ──► Claude API ──► Parse  │              │
   │       │    │       │                │          Action │              │
   │       │    │       │                │                 │              │
   │       │    │  [Base Engine]    [5s normal]     [fold/ │              │
   │       │    │  [Custom Prompt]  [10s all-in]    call/  │              │
   │       │    │  [Game State]                     raise] │              │
   │       │    └─────────────────────────────────────────┘              │
   │       │                                                              │
   │       ▼                                                              │
   │  Store Hand History (PostgreSQL)                                     │
   └─────────────────────────────────────────────────────────────────────┘

5. TABLE BALANCING
   After Elimination ──► Check Table Sizes ──► If Diff > 1 ──► Move BB Player
                                                    │
                                                    ▼
                                          Never during active hand

6. COMPLETION
   Final Table ──► Heads Up ──► Winner ──► Calculate Payouts
        │                           │
        ▼                           ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  ON-CHAIN:                         │  OFF-CHAIN:                     │
   │  • Results hash (SHA-256)          │  • Full hand history            │
   │  • Player rankings                 │  • Agent decision logs          │
   │  • POINTS distribution (SPL)       │  • API token usage              │
   │  • Update lifetime stats PDAs      │  • Detailed tournament data     │
   └─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT INTERACTIONS                           │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │         ADMIN DASHBOARD          │
                    │  • Create tournaments            │
                    │  • Define blind structures       │
                    │  • Set payout tables             │
                    │  • Spectate (showdown only)      │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          TOURNAMENT MANAGER                            │
│                                                                        │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐       │
│  │ Registration   │───►│ Table Manager  │───►│ Payout Engine  │       │
│  │ Handler        │    │                │    │                │       │
│  └────────────────┘    └───────┬────────┘    └────────────────┘       │
│                                │                                       │
│                                ▼                                       │
│                    ┌────────────────────┐                              │
│                    │   Hand Controller  │◄─────────────────────────┐  │
│                    │                    │                          │  │
│                    │  • Deal cards      │                          │  │
│                    │  • Manage betting  │                          │  │
│                    │  • Determine winner│                          │  │
│                    └─────────┬──────────┘                          │  │
│                              │                                     │  │
└──────────────────────────────┼─────────────────────────────────────┼──┘
                               │                                     │
                               ▼                                     │
┌──────────────────────────────────────────────────────────────────┐ │
│                        AI DECISION ENGINE                         │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │                    CONTEXT BUILDER                           │ │ │
│  │                                                              │ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │ │
│  │  │ Base Engine  │  │ Custom       │  │ Game State   │       │ │ │
│  │  │ (~1500 tok)  │  │ Prompt       │  │ Formatter    │       │ │ │
│  │  │              │  │ (if paid)    │  │              │       │ │ │
│  │  │ • Pot odds   │  │              │  │ • Position   │       │ │ │
│  │  │ • Equity     │  │ • Sliders    │  │ • Stack sizes│       │ │ │
│  │  │ • Position   │  │ • Freeform   │  │ • Pot size   │       │ │ │
│  │  │ • ICM       │  │   text       │  │ • Actions    │       │ │ │
│  │  │ • SPR       │  │              │  │ • Cards      │       │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │ │ │
│  │              │              │              │                 │ │ │
│  │              └──────────────┼──────────────┘                 │ │ │
│  │                             │                                │ │ │
│  │                             ▼                                │ │ │
│  │                    ┌────────────────┐                        │ │ │
│  │                    │ PROMPT CACHE   │ ◄── 85% token savings  │ │ │
│  │                    │ (System Prompt)│                        │ │ │
│  │                    └───────┬────────┘                        │ │ │
│  └────────────────────────────┼─────────────────────────────────┘ │ │
│                               │                                   │ │
│                               ▼                                   │ │
│  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │                   CLAUDE SONNET 4.5 API                      │ │ │
│  │                                                              │ │ │
│  │   Input: System Prompt + Game State                         │ │ │
│  │   Output: { action: "raise", amount: 150 }                  │ │ │
│  │                                                              │ │ │
│  │   Timing: 5s standard | 10s all-in decisions                │ │ │
│  └─────────────────────────────────────────────────────────────┘ │ │
│                               │                                   │ │
│                               ▼                                   │ │
│  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │                    ACTION VALIDATOR                          │ │ │
│  │                                                              │ │ │
│  │   • Validate action is legal (can't raise less than min)    │ │ │
│  │   • Enforce bet sizing rules                                │ │ │
│  │   • Handle edge cases (all-in, side pots)                   │ │ │
│  └──────────────────────────────────────────┬──────────────────┘ │
│                                              │                    │
└──────────────────────────────────────────────┼────────────────────┘
                                               │
                                               └────────────────────►
```

---

## 3. Tech Stack

### 3.1 Complete Technology Matrix

| Layer | Technology | Purpose | Cost Estimate |
|-------|------------|---------|---------------|
| **Frontend** | Next.js 14 (App Router) | React framework with SSR | — |
| | TypeScript | Type safety | — |
| | Tailwind CSS | Utility-first styling | — |
| | Zustand | Client state management | — |
| | @solana/wallet-adapter-react | Wallet connection | — |
| | Socket.IO Client | Real-time updates | — |
| **Hosting (FE)** | Vercel | Edge deployment | $0-50/mo |
| **Backend** | FastAPI | Python API framework | — |
| | Python 3.11+ | Runtime | — |
| | Starlette WebSockets | Real-time communication | — |
| | Anthropic SDK | Claude API integration | — |
| **Hosting (BE)** | Railway | Container hosting | $20-500/mo |
| **Database** | Neon PostgreSQL | Primary data store | $0-50/mo |
| | Upstash Redis | Cache & real-time state | $0-50/mo |
| **Blockchain** | Solana (mainnet-beta) | Settlement layer | — |
| | Anchor 0.30+ | Smart contract framework | — |
| | Helius RPC | Solana node access | $0-999/mo |
| **AI** | Claude Sonnet 4.5 | Agent decisions | ~$7.20/tournament |
| **Monitoring** | Vercel Analytics | Frontend metrics | Free |
| | Sentry | Error tracking | $0-26/mo |
| | BetterStack | Uptime monitoring | $0-15/mo |

### 3.2 Directory Structure

```
poker-agent-arena/
├── README.md                    # This file (context declaration)
├── .env.example                 # Environment template
├── docker-compose.yml           # Local development
│
├── frontend/                    # Next.js application
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Landing/home
│   │   │   ├── tournaments/
│   │   │   │   ├── page.tsx     # Tournament list
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx # Tournament detail
│   │   │   │       └── live/
│   │   │   │           └── page.tsx # Live view
│   │   │   ├── register/
│   │   │   │   └── [tournamentId]/
│   │   │   │       └── page.tsx # Registration flow
│   │   │   ├── agent/
│   │   │   │   └── page.tsx     # Agent customization
│   │   │   ├── leaderboard/
│   │   │   │   └── page.tsx     # Global leaderboard
│   │   │   └── admin/
│   │   │       └── page.tsx     # Admin dashboard
│   │   │
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   ├── wallet/          # Wallet connection
│   │   │   ├── tournament/      # Tournament components
│   │   │   ├── poker/           # Poker table UI
│   │   │   └── agent/           # Agent configuration
│   │   │
│   │   ├── hooks/               # Custom React hooks
│   │   ├── stores/              # Zustand stores
│   │   ├── lib/                 # Utilities
│   │   │   ├── solana.ts        # Solana helpers
│   │   │   ├── api.ts           # API client
│   │   │   └── socket.ts        # Socket.IO setup
│   │   └── types/               # TypeScript types
│   │
│   └── public/
│       └── images/              # Static assets
│
├── backend/                     # FastAPI application
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── main.py                  # Entry point
│   ├── config.py                # Configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── tournaments.py   # Tournament endpoints
│   │   │   ├── agents.py        # Agent endpoints
│   │   │   ├── admin.py         # Admin endpoints
│   │   │   └── websocket.py     # WebSocket handlers
│   │   └── middleware/
│   │       ├── auth.py          # Wallet signature verification
│   │       └── rate_limit.py    # Rate limiting
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── poker/
│   │   │   ├── deck.py          # Card/deck logic
│   │   │   ├── hand_evaluator.py# Hand ranking
│   │   │   ├── betting.py       # Betting round logic
│   │   │   └── side_pots.py     # Side pot calculation
│   │   │
│   │   ├── tournament/
│   │   │   ├── manager.py       # Tournament orchestration
│   │   │   ├── table.py         # Table management
│   │   │   ├── blinds.py        # Blind structure
│   │   │   ├── seating.py       # Initial seating
│   │   │   └── balancing.py     # Table balancing
│   │   │
│   │   └── ai/
│   │       ├── engine.py        # Decision engine
│   │       ├── base_prompt.py   # Base agent system prompt
│   │       ├── context_builder.py # Game state formatter
│   │       └── action_parser.py # Response parsing
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tournament.py        # Tournament models
│   │   ├── player.py            # Player models
│   │   ├── agent.py             # Agent configuration
│   │   └── hand.py              # Hand history models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── anthropic.py         # Claude API wrapper
│   │   ├── solana.py            # Solana interactions
│   │   └── randomness.py        # Blockhash RNG
│   │
│   └── db/
│       ├── __init__.py
│       ├── database.py          # Connection management
│       ├── repositories/        # Data access layer
│       └── migrations/          # Alembic migrations
│
├── contracts/                   # Anchor smart contracts
│   ├── Anchor.toml
│   ├── Cargo.toml
│   ├── programs/
│   │   └── poker_arena/
│   │       ├── Cargo.toml
│   │       └── src/
│   │           ├── lib.rs       # Program entry
│   │           ├── state/
│   │           │   ├── tournament.rs
│   │           │   ├── player.rs
│   │           │   └── config.rs
│   │           ├── instructions/
│   │           │   ├── initialize.rs
│   │           │   ├── create_tournament.rs
│   │           │   ├── register_player.rs
│   │           │   ├── finalize_tournament.rs
│   │           │   └── distribute_points.rs
│   │           └── errors.rs
│   │
│   ├── tests/                   # Integration tests
│   └── migrations/              # Deploy scripts
│
├── scripts/                     # Utility scripts
│   ├── deploy.sh
│   ├── seed-data.ts
│   └── run-tournament.ts
│
└── docs/                        # Additional documentation
    ├── API.md
    ├── SMART_CONTRACT.md
    └── DEPLOYMENT.md
```

---

## 4. Smart Contract Specification

### 4.1 Program Overview

The Anchor program manages tournament lifecycle, player registration, and POINTS distribution.

### 4.2 Account Structures

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
    pub payout_structure_hash: [u8; 32],   // SHA-256 of payout table JSON
    
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
    Basic,          // 0.1 SOL - 200 char custom prompt
    Pro,            // 1 SOL - Unlimited custom prompt
}

// Space: 8 + 32 + 32 + 1 + 8 + 32 + 32 + 128 + 3 + 9 + 5 + 2 + 1 ≈ 293 bytes
```

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

### 4.3 Instructions

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
    pub fn create_tournament(
        ctx: Context<CreateTournament>,
        max_players: u16,
        starting_stack: u64,
        starts_at: i64,
        blind_structure_hash: [u8; 32],
        payout_structure_hash: [u8; 32],
    ) -> Result<()>;

    /// Register a player for a tournament
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

### 4.4 PDA Seeds

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

### 4.5 Error Codes

```rust
#[error_code]
pub enum ArenaError {
    #[msg("Only admin can perform this action")]
    Unauthorized,
    
    #[msg("Tournament registration is not open")]
    RegistrationNotOpen,
    
    #[msg("Tournament is full")]
    TournamentFull,
    
    #[msg("Tournament has already started")]
    TournamentAlreadyStarted,
    
    #[msg("Invalid agent tier payment")]
    InvalidTierPayment,
    
    #[msg("Agent customization locked after tournament start")]
    AgentLocked,
    
    #[msg("Tournament not in progress")]
    TournamentNotInProgress,
    
    #[msg("Invalid results hash")]
    InvalidResultsHash,
}
```

---

## 5. Backend Service Specification

### 5.1 API Overview

FastAPI backend handles tournament orchestration, AI decisions, and real-time updates.

### 5.2 Configuration

```python
# backend/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str  # Neon PostgreSQL connection string
    REDIS_URL: str     # Upstash Redis connection string
    
    # Solana
    SOLANA_RPC_URL: str  # Helius RPC endpoint
    ADMIN_WALLET_PUBKEY: str
    PROGRAM_ID: str
    
    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"
    
    # Tournament
    MAX_TOURNAMENT_BUDGET_MULTIPLIER: float = 3.0  # 3x expected cost cap
    DECISION_TIMEOUT_NORMAL: int = 5   # seconds
    DECISION_TIMEOUT_ALLIN: int = 10   # seconds
    
    # Security
    CORS_ORIGINS: list[str] = ["https://yourdomain.com"]
    
    class Config:
        env_file = ".env"
```

### 5.3 Core Tournament Engine

```python
# backend/core/tournament/manager.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio

class TournamentPhase(Enum):
    REGISTRATION = "registration"
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    FINAL_TABLE = "final_table"
    HEADS_UP = "heads_up"
    COMPLETED = "completed"

@dataclass
class BlindLevel:
    level: int
    small_blind: int
    big_blind: int
    ante: int
    duration_minutes: int

@dataclass
class TournamentConfig:
    tournament_id: str
    max_players: int
    starting_stack: int
    table_size: int = 9  # 9-max
    blind_structure: list[BlindLevel]
    payout_structure: dict[int, int]  # rank -> points
    
class TournamentManager:
    """
    Orchestrates the entire tournament lifecycle.
    
    Responsibilities:
    - Initialize tables and seat players
    - Manage blind level progression
    - Handle table balancing after eliminations
    - Coordinate hand execution across tables
    - Track eliminations and final standings
    - Finalize results and trigger on-chain settlement
    """
    
    def __init__(
        self,
        config: TournamentConfig,
        ai_engine: "AIDecisionEngine",
        db: "Database",
        event_emitter: "EventEmitter",
    ):
        self.config = config
        self.ai_engine = ai_engine
        self.db = db
        self.events = event_emitter
        
        self.tables: dict[str, Table] = {}
        self.players: dict[str, Player] = {}
        self.eliminations: list[Elimination] = []
        self.current_level: int = 0
        self.phase = TournamentPhase.REGISTRATION
        
    async def start(self, registered_players: list[Player], rng_seed: bytes):
        """
        Initialize tournament with provably fair seating.
        
        1. Verify all registrations on-chain
        2. Generate deterministic shuffle from blockhash seed
        3. Create tables and assign seats
        4. Begin hand execution loop
        """
        ...
    
    async def run_hand_loop(self):
        """
        Main game loop - runs hands in parallel across tables.
        
        - Tables run hands concurrently
        - Decisions within a hand are sequential
        - After each hand, check for eliminations
        - Trigger table balancing if needed
        - Check for level advancement
        """
        ...
    
    async def balance_tables(self):
        """
        Balance tables after elimination.
        
        Rules:
        1. Check table sizes after every elimination
        2. If max difference > 1, balance immediately
        3. Move player who will be BB next (fairest)
        4. Never move during active hand
        """
        ...
    
    async def finalize(self):
        """
        Complete tournament and settle on-chain.
        
        1. Calculate final standings
        2. Compute POINTS distribution
        3. Generate results hash
        4. Submit finalization transaction
        5. Distribute POINTS SPL tokens
        """
        ...
```

### 5.4 Hand Controller

```python
# backend/core/poker/hand_controller.py

@dataclass
class HandState:
    hand_id: str
    table_id: str
    deck: list[str]  # Remaining cards
    community_cards: list[str]
    pot: int
    side_pots: list[SidePot]
    current_bet: int
    min_raise: int
    players: list[PlayerInHand]
    button_position: int
    action_on: int  # Index of player to act
    betting_round: BettingRound  # PREFLOP, FLOP, TURN, RIVER
    
class HandController:
    """
    Manages a single poker hand.
    
    Texas Hold'em No-Limit rules:
    - 2 hole cards per player
    - 5 community cards (flop/turn/river)
    - Best 5-card hand wins
    - All-in and side pot support
    """
    
    async def deal(self, players: list[Player], deck: Deck) -> HandState:
        """Deal hole cards to all active players."""
        ...
    
    async def run_betting_round(
        self, 
        state: HandState,
        ai_engine: "AIDecisionEngine",
    ) -> HandState:
        """
        Execute a complete betting round.
        
        - Sequential decisions (poker requires this)
        - 5 second timeout for normal decisions
        - 10 second timeout for all-in decisions
        - Validate all actions against rules
        """
        ...
    
    async def showdown(self, state: HandState) -> ShowdownResult:
        """
        Determine winner(s) and distribute pot.
        
        - Evaluate all hands
        - Handle split pots
        - Calculate side pot distributions
        """
        ...
```

### 5.5 Poker Logic

```python
# backend/core/poker/hand_evaluator.py

from enum import IntEnum

class HandRank(IntEnum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

@dataclass
class EvaluatedHand:
    rank: HandRank
    rank_values: tuple[int, ...]  # For tiebreakers
    cards_used: list[str]         # The 5 cards making the hand
    
class HandEvaluator:
    """
    Evaluates poker hands.
    
    Takes 7 cards (2 hole + 5 community) and returns
    the best possible 5-card hand with ranking.
    
    Uses optimized lookup tables for performance.
    """
    
    def evaluate(self, hole_cards: list[str], community: list[str]) -> EvaluatedHand:
        """Find best 5-card hand from 7 cards."""
        ...
    
    def compare(self, hand1: EvaluatedHand, hand2: EvaluatedHand) -> int:
        """Compare two hands. Returns: -1, 0, or 1."""
        ...
```

```python
# backend/core/poker/deck.py

import hashlib

class Deck:
    """
    52-card deck with provably fair shuffle.
    
    Uses blockhash commitment for verifiable randomness.
    """
    
    CARDS = [
        f"{rank}{suit}"
        for suit in ["s", "h", "d", "c"]  # spades, hearts, diamonds, clubs
        for rank in ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    ]
    
    def __init__(self, seed: bytes):
        """
        Initialize deck with deterministic seed.
        
        seed = SHA256(blockhash + tournament_id + hand_number)
        """
        self.rng = self._create_rng(seed)
        self.cards = self._shuffle()
        
    def _create_rng(self, seed: bytes):
        """Create deterministic PRNG from seed."""
        ...
    
    def _shuffle(self) -> list[str]:
        """Fisher-Yates shuffle with PRNG."""
        ...
    
    def deal(self, count: int) -> list[str]:
        """Deal cards from top of deck."""
        ...
```

---

## 6. Frontend Specification

### 6.1 Page Routes

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/` | Landing page, tournament list | No |
| `/tournaments` | All tournaments (upcoming, live, completed) | No |
| `/tournaments/[id]` | Tournament detail, registration | No (connect wallet to register) |
| `/tournaments/[id]/live` | Live view of tournament | Wallet (only own agent) |
| `/agent` | Agent customization (name, image, prompt) | Wallet |
| `/leaderboard` | Global POINTS leaderboard | No |
| `/admin` | Admin dashboard (create tournaments) | Admin wallet only |

### 6.2 Key Components

```typescript
// frontend/src/components/tournament/TournamentCard.tsx

interface TournamentCardProps {
  tournament: {
    id: string;
    status: "registration" | "in_progress" | "completed";
    maxPlayers: number;
    registeredPlayers: number;
    startsAt: Date;
    blindStructure: string;  // Template name
    pointsPrizePool: number;
  };
}

// frontend/src/components/poker/PokerTable.tsx

interface PokerTableProps {
  tableId: string;
  seats: Seat[];           // 9 seats, some may be empty
  communityCards: Card[];
  pot: number;
  currentBet: number;
  actionOn: number;        // Seat index
  myAgentSeat?: number;    // If user's agent is at this table
  isSpectator: boolean;    // Admin spectate mode
}

interface Seat {
  position: number;
  player?: {
    wallet: string;
    agentName: string;
    agentImage: string;
    stack: number;
    holeCards?: Card[];    // Only visible to owner or at showdown
    currentBet: number;
    status: "active" | "folded" | "all_in" | "eliminated";
    isActing: boolean;
    timeRemaining?: number; // Countdown for current decision
  };
}

// frontend/src/components/agent/AgentConfigurator.tsx

interface AgentConfiguratorProps {
  tier: "free" | "basic" | "pro";
  currentConfig?: {
    name: string;
    imageUri: string;
    sliders: {
      aggression: number;      // 0-100
      bluffFrequency: number;  // 0-100
      tightness: number;       // 0-100
      positionAwareness: number; // 0-100
    };
    customPrompt: string;      // 200 chars for basic, unlimited for pro
  };
  isLocked: boolean;           // true after tournament starts
  onSave: (config: AgentConfig) => void;
}
```

### 6.3 State Management (Zustand)

```typescript
// frontend/src/stores/tournamentStore.ts

import { create } from "zustand";

interface TournamentState {
  // Active tournament being viewed
  currentTournament: Tournament | null;
  
  // Real-time table state (via WebSocket)
  tables: Map<string, TableState>;
  
  // My agent's status
  myAgent: {
    tableId: string | null;
    seatPosition: number | null;
    stack: number;
    status: "active" | "eliminated";
  } | null;
  
  // Actions
  setCurrentTournament: (tournament: Tournament) => void;
  updateTableState: (tableId: string, state: TableState) => void;
  updateMyAgent: (update: Partial<TournamentState["myAgent"]>) => void;
}

// frontend/src/stores/walletStore.ts

interface WalletState {
  connected: boolean;
  publicKey: string | null;
  isAdmin: boolean;
  
  // Agent configuration
  agent: AgentConfig | null;
  
  // Lifetime stats
  stats: PlayerStats | null;
  
  connect: () => Promise<void>;
  disconnect: () => void;
  signMessage: (message: Uint8Array) => Promise<Uint8Array>;
}
```

### 6.4 Real-Time Updates (Socket.IO)

```typescript
// frontend/src/lib/socket.ts

import { io, Socket } from "socket.io-client";

interface ServerToClientEvents {
  // Tournament events
  "tournament:started": (data: { tournamentId: string }) => void;
  "tournament:completed": (data: TournamentResults) => void;
  
  // Table events
  "table:state": (data: TableState) => void;
  "table:action": (data: PlayerAction) => void;
  
  // Hand events
  "hand:new": (data: { handId: string; tableId: string }) => void;
  "hand:deal": (data: { holeCards?: Card[] }) => void;  // Only to owner
  "hand:community": (data: { cards: Card[]; round: string }) => void;
  "hand:showdown": (data: ShowdownResult) => void;
  
  // Player events
  "player:eliminated": (data: { wallet: string; rank: number }) => void;
  "player:moved": (data: { wallet: string; fromTable: string; toTable: string }) => void;
  
  // Decision timing
  "decision:start": (data: { wallet: string; timeoutSeconds: number }) => void;
  "decision:made": (data: PlayerAction) => void;
}

interface ClientToServerEvents {
  // Join tournament room for updates
  "join:tournament": (tournamentId: string) => void;
  "leave:tournament": (tournamentId: string) => void;
  
  // Subscribe to specific table
  "subscribe:table": (tableId: string) => void;
  "unsubscribe:table": (tableId: string) => void;
}
```

### 6.5 Registration Flow

```typescript
// frontend/src/app/register/[tournamentId]/page.tsx

/**
 * Registration Flow:
 * 
 * 1. Connect wallet (Phantom)
 * 2. Display tier options:
 *    - FREE: Base agent, no cost
 *    - BASIC (0.1 SOL): Base + 200 char prompt + sliders
 *    - PRO (1 SOL): Base + unlimited prompt + sliders
 * 3. If BASIC/PRO: Configure agent (name, image, sliders, prompt)
 * 4. Legal checkboxes:
 *    □ I have read and agree to the Terms of Service
 *    □ I confirm I am not a resident of, or physically located in, Restricted Jurisdictions
 * 5. Sign transaction (includes tier payment + registration)
 * 6. Confirmation with agent preview
 */
```

---

## 7. AI Agent System

### 7.1 Base Agent Engine

The FREE tier includes a comprehensive poker foundation (~1,500 tokens, cached):

```python
# backend/core/ai/base_prompt.py

BASE_AGENT_SYSTEM_PROMPT = """
You are a poker AI agent competing in a No-Limit Texas Hold'em tournament.

## CORE DECISION FRAMEWORK

You must respond with EXACTLY ONE action in JSON format:
{"action": "fold" | "check" | "call" | "raise", "amount": <number if raise>}

## MATHEMATICAL FOUNDATIONS

### Pot Odds
- Pot odds = Call Amount / (Pot + Call Amount)
- Compare to hand equity to determine profitability
- Example: Pot is 100, call is 50 → Pot odds = 50/150 = 33%
- If your hand has >33% equity, calling is mathematically profitable

### Hand Equity Approximations
- Pocket pairs vs unpaired overcards: ~55% favorite
- Overpair vs underpair: ~80% favorite
- Flush draw on flop: ~35% to hit by river
- Open-ended straight draw: ~32% to hit by river
- Gutshot straight draw: ~17% to hit by river

### Expected Value (EV)
- EV = (Win% × Pot Won) - (Lose% × Amount Risked)
- Always choose the action with highest positive EV
- Fold when all available actions have negative EV

## POSITION AWARENESS

### Position Categories
- Early Position (UTG, UTG+1, UTG+2): Play tight, 10-12% of hands
- Middle Position (MP, HJ): Slightly wider, 15-18% of hands
- Late Position (CO, BTN): Much wider, 25-35% of hands
- Blinds (SB, BB): Defend appropriate ranges vs position raises

### Positional Advantage
- Acting last = information advantage
- Widen range in position, tighten out of position
- Position is worth approximately 1 big blind per hand

## STACK-TO-POT RATIO (SPR)

- SPR = Effective Stack / Pot Size (after preflop action)
- Low SPR (<4): Commit with top pair+, draws lose value
- Medium SPR (4-10): Standard play, consider implied odds
- High SPR (>10): Speculative hands gain value, premium hands risk stacking off

## HAND CATEGORIES

### Premium (Always raise/3-bet): AA, KK, QQ, AKs, AKo
### Strong (Raise, sometimes 3-bet): JJ, TT, AQs, AQo, AJs, KQs
### Playable (Position-dependent): 99-22, suited connectors, suited aces
### Marginal (Late position only): Suited gappers, weak suited kings

## TOURNAMENT-SPECIFIC ADJUSTMENTS (ICM Basics)

### Survival Pressure
- Chip value is non-linear in tournaments
- Near the money: survival > accumulation
- Early tournament: accumulation > survival

### Stack-Size Categories
- Short stack (<20 BB): Push/fold mode
- Medium stack (20-40 BB): Standard play
- Deep stack (>40 BB): More post-flop flexibility

### Push/Fold Guidelines (Short Stack)
- <10 BB: Push any playable hand, no calling
- 10-15 BB: Push or fold, rarely call
- 15-20 BB: Can raise smaller, but often push

## BETTING PATTERNS

### Standard Sizing
- Open raise: 2.2-2.5x BB (adjust for stack depth)
- 3-bet: 3x the open (in position), 3.5-4x (out of position)
- Continuation bet: 33-50% pot on dry boards, 50-75% on wet boards
- Value bet river: 50-75% pot

### Reading Opponent Patterns
- Minimum raise often indicates draw or weak hand testing
- Overbet often polarized (very strong or bluff)
- Quick check often indicates weakness

## RESPONSE FORMAT

Analyze the situation, then respond with a JSON action:

{"action": "fold"}
{"action": "check"}
{"action": "call"}
{"action": "raise", "amount": 150}

IMPORTANT: Always use "raise" for any aggressive action, whether you are:
- Opening the betting (technically a "bet")
- Raising a previous bet

Do NOT use "bet" — always use "raise" with the total amount.
Amount is total bet size, not raise increment.
"""
```

### 7.2 Custom Agent Configuration

```python
# backend/core/ai/context_builder.py

@dataclass
class AgentSliders:
    """Structured personality parameters (0-100 scale)."""
    aggression: int = 50       # Low = passive, High = aggressive
    bluff_frequency: int = 30  # How often to bluff
    tightness: int = 50        # Low = loose, High = tight
    position_awareness: int = 70  # Weight of position in decisions

def build_custom_prompt(
    tier: AgentTier,
    sliders: AgentSliders,
    custom_text: str,
) -> str:
    """
    Build the custom portion of agent prompt.
    
    - FREE: No customization (empty string)
    - BASIC: Sliders + 200 char limit
    - PRO: Sliders + unlimited text
    """
    if tier == AgentTier.FREE:
        return ""
    
    slider_prompt = f"""
## PERSONALITY PARAMETERS

Your playing style is calibrated as follows:
- Aggression Level: {sliders.aggression}/100 {"(very aggressive)" if sliders.aggression > 70 else "(balanced)" if sliders.aggression > 30 else "(passive)"}
- Bluff Frequency: {sliders.bluff_frequency}/100 {"(frequent bluffer)" if sliders.bluff_frequency > 50 else "(selective bluffer)"}
- Hand Selection: {sliders.tightness}/100 {"(very tight)" if sliders.tightness > 70 else "(balanced)" if sliders.tightness > 30 else "(loose)"}
- Position Weight: {sliders.position_awareness}/100

Adjust your decisions according to these parameters while maintaining mathematically sound play.
"""
    
    if tier == AgentTier.BASIC:
        # Enforce 200 char limit
        custom_text = custom_text[:200]
    
    user_prompt = f"""
## CUSTOM INSTRUCTIONS FROM OWNER

{custom_text}
"""
    
    return slider_prompt + user_prompt
```

### 7.3 Decision Engine

```python
# backend/core/ai/engine.py

import anthropic
from typing import Literal

ActionType = Literal["fold", "check", "call", "raise"]

@dataclass
class Decision:
    action: ActionType
    amount: int | None = None  # Only for raises
    reasoning: str = ""        # For logging (not sent to client)

class AIDecisionEngine:
    """
    Makes poker decisions using Claude Sonnet 4.5.
    
    Key optimizations:
    - System prompt caching (85% token savings)
    - Compressed game state format
    - Parallel table processing
    - Budget tracking per tournament
    """
    
    def __init__(self, client: anthropic.Anthropic, budget_tracker: "BudgetTracker"):
        self.client = client
        self.budget = budget_tracker
        
        # Cache the base system prompt
        self._cached_system_prompt = self._prepare_cached_prompt()
    
    async def get_decision(
        self,
        agent_config: AgentConfig,
        game_state: GameState,
        is_all_in_decision: bool = False,
    ) -> Decision:
        """
        Get a decision for the given game state.
        
        Timing:
        - Normal decisions: 5 second target
        - All-in decisions: 10 second target
        """
        # Check budget
        if not self.budget.can_make_call(agent_config.tournament_id):
            # Return conservative action if budget exceeded
            return Decision(action="fold", reasoning="Budget exceeded")
        
        # Build full prompt
        system_prompt = self._build_system_prompt(agent_config)
        user_prompt = self._format_game_state(game_state)
        
        # Call Claude API
        timeout = 10 if is_all_in_decision else 5
        response = await self._call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
        )
        
        # Parse and validate response
        decision = self._parse_response(response, game_state)
        
        # Track usage
        self.budget.record_usage(
            tournament_id=agent_config.tournament_id,
            tokens_used=response.usage.total_tokens,
        )
        
        return decision
    
    def _format_game_state(self, state: GameState) -> str:
        """
        Format game state for Claude in compressed format.
        
        Example output:
```
        HAND #1847 | FLOP | Pot: 450 | To Call: 150
        
        Board: Ah Kd 7c
        
        Your Cards: Qs Qd
        Your Position: BTN (Button)
        Your Stack: 4,850
        
        Players:
        1. [UTG] Player_A: 3,200 (folded)
        2. [MP] Player_B: 5,100 (bet 150)
        3. [CO] Player_C: 2,800 (called 150)
        4. [BTN] YOU: 4,850 (to act)
        5. [SB] Player_D: 6,200 (folded)
        6. [BB] Player_E: 4,500 (checked)
        
        Action History This Hand:
        - Preflop: UTG fold, MP raise 100, CO call, BTN call, SB fold, BB call
        - Flop: BB check, MP bet 150, CO call
        
        Your Action?
```
        """
        ...
    
    def _parse_response(self, response: str, state: GameState) -> Decision:
        """
        Parse Claude's JSON response and validate against game rules.
        
        Validation:
        - Can't check if there's a bet to call
        - Raise must be at least min-raise
        - Raise can't exceed stack
        - All-in is valid at any amount
        
        Note: "bet" is accepted as alias for "raise" since they are
        mechanically identical (aggressive action with amount).
        """
        data = json.loads(response)
        action = data["action"].lower()
        
        # Normalize "bet" to "raise" — mechanically identical
        if action == "bet":
            action = "raise"
        
        if action not in ["fold", "check", "call", "raise"]:
            raise InvalidActionError(f"Unknown action: {action}")
        
        # ... continue with validation
```

### 7.4 Prompt Caching Strategy

```python
# backend/core/ai/engine.py

def _prepare_cached_prompt(self) -> str:
    """
    Prepare the static portion of the system prompt for caching.
    
    Anthropic's prompt caching:
    - First request with prompt: Full price
    - Subsequent requests: 85% discount on cached portion
    - Cache TTL: 5 minutes of inactivity
    
    Strategy:
    - Cache: Base engine (~1,500 tokens)
    - Dynamic: Custom prompt + game state
    
    For a 27-player tournament (~200 hands, ~1000 decisions):
    - Without caching: ~$24/tournament
    - With caching: ~$7.20/tournament (70% savings)
    """
    return BASE_AGENT_SYSTEM_PROMPT

def _build_system_prompt(self, config: AgentConfig) -> list[dict]:
    """
    Build system prompt with caching markers.
    
    Format for Anthropic API:
    [
        {"type": "text", "text": "<cached base>", "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "<custom prompt>"}
    ]
    """
    ...
```

---

## 8. Tournament Engine

### 8.1 Blind Structures

```python
# backend/core/tournament/blinds.py

BLIND_TEMPLATES = {
    "turbo": [
        BlindLevel(1, 25, 50, 0, 6),
        BlindLevel(2, 50, 100, 0, 6),
        BlindLevel(3, 75, 150, 0, 6),
        BlindLevel(4, 100, 200, 25, 6),
        BlindLevel(5, 150, 300, 25, 6),
        BlindLevel(6, 200, 400, 50, 6),
        BlindLevel(7, 300, 600, 75, 6),
        BlindLevel(8, 400, 800, 100, 6),
        BlindLevel(9, 500, 1000, 100, 6),
        BlindLevel(10, 700, 1400, 175, 6),
        BlindLevel(11, 1000, 2000, 250, 6),
        BlindLevel(12, 1500, 3000, 375, 6),
        # ... continues
    ],
    
    "standard": [
        BlindLevel(1, 25, 50, 0, 10),
        BlindLevel(2, 50, 100, 0, 10),
        # ... 10-minute levels
    ],
    
    "deep_stack": [
        BlindLevel(1, 25, 50, 0, 15),
        BlindLevel(2, 50, 100, 0, 15),
        # ... 15-minute levels
    ],
}
```

### 8.2 Table Balancing Algorithm

```python
# backend/core/tournament/balancing.py

class TableBalancer:
    """
    Balances tables after player eliminations.
    
    Rules:
    1. After every elimination, check table sizes
    2. If max difference > 1, balance immediately
    3. Move the player who will be big blind next (fairest position)
    4. Never move during an active hand
    """
    
    def check_balance_needed(self, tables: list[Table]) -> bool:
        """Check if tables need balancing."""
        if len(tables) <= 1:
            return False
        
        sizes = [t.player_count for t in tables]
        return max(sizes) - min(sizes) > 1
    
    def get_move(self, tables: list[Table]) -> TableMove | None:
        """
        Determine which player to move and where.
        
        Returns None if no move needed.
        """
        if not self.check_balance_needed(tables):
            return None
        
        # Find fullest and emptiest tables
        sorted_tables = sorted(tables, key=lambda t: t.player_count, reverse=True)
        source = sorted_tables[0]
        dest = sorted_tables[-1]
        
        # Select player who will be BB next
        player_to_move = source.get_next_big_blind_player()
        
        # Find appropriate seat at destination
        dest_seat = dest.get_best_available_seat()
        
        return TableMove(
            player=player_to_move,
            from_table=source.id,
            to_table=dest.id,
            to_seat=dest_seat,
        )
    
    def should_break_table(self, tables: list[Table]) -> Table | None:
        """
        Check if a table should be broken (combined with others).
        
        Break when: num_players <= table_count
        """
        total_players = sum(t.player_count for t in tables)
        if total_players <= (len(tables) - 1) * 9:  # Can fit at fewer tables
            # Break the smallest table
            return min(tables, key=lambda t: t.player_count)
        return None
```

### 8.3 Payout Calculator

```python
# backend/core/tournament/payouts.py

class PayoutCalculator:
    """
    Calculates POINTS distribution based on payout structure.
    
    Payout structures are configured per tournament by admin.
    """
    
    def calculate(
        self,
        payout_structure: dict[int, int],  # rank -> points
        final_rankings: list[tuple[str, int]],  # (wallet, rank)
    ) -> list[PointsAward]:
        """
        Calculate POINTS for each player based on final rank.
        
        Example payout structure (27 players):
        {
            1: 5000,   # 1st place
            2: 3000,   # 2nd place
            3: 2000,   # 3rd place
            4: 1000,   # 4th place
            5: 500,    # 5th place
            6: 500,    # 6th place
        }
        """
        awards = []
        for wallet, rank in final_rankings:
            points = payout_structure.get(rank, 0)
            if points > 0:
                awards.append(PointsAward(
                    wallet=wallet,
                    rank=rank,
                    points=points,
                ))
        return awards
```

---

## 9. Real-Time System

### 9.1 WebSocket Events

```python
# backend/api/routes/websocket.py

from fastapi import WebSocket

class TournamentBroadcaster:
    """
    Manages real-time updates to connected clients.
    
    Event categories:
    - Tournament-wide: Started, level changes, eliminations
    - Table-specific: Hand actions, pot updates, showdowns
    - Player-specific: Hole cards (only to owner)
    """
    
    def __init__(self):
        self.tournament_connections: dict[str, set[WebSocket]] = {}
        self.table_subscriptions: dict[str, set[WebSocket]] = {}
        self.player_sessions: dict[str, WebSocket] = {}  # wallet -> socket
    
    async def broadcast_to_tournament(self, tournament_id: str, event: str, data: dict):
        """Send event to all viewers of a tournament."""
        ...
    
    async def broadcast_to_table(self, table_id: str, event: str, data: dict):
        """Send event to all viewers of a specific table."""
        ...
    
    async def send_to_player(self, wallet: str, event: str, data: dict):
        """Send private event to specific player (e.g., hole cards)."""
        ...
    
    async def broadcast_decision_timer(
        self,
        table_id: str,
        wallet: str,
        timeout_seconds: int,
    ):
        """
        Start decision countdown for UX.
        
        5 seconds for normal decisions
        10 seconds for all-in decisions
        """
        ...
```

### 9.2 Event Payloads

```typescript
// Event type definitions

interface TournamentStartedEvent {
  tournamentId: string;
  tables: {
    tableId: string;
    seats: SeatAssignment[];
  }[];
  blindLevel: {
    level: number;
    smallBlind: number;
    bigBlind: number;
    ante: number;
  };
}

interface HandDealEvent {
  handId: string;
  tableId: string;
  button: number;
  holeCards?: [string, string];  // Only sent to owner
}

interface PlayerActionEvent {
  tableId: string;
  handId: string;
  wallet: string;
  action: "fold" | "check" | "call" | "raise";
  amount?: number;
  newStack: number;
  pot: number;
}

interface ShowdownEvent {
  tableId: string;
  handId: string;
  players: {
    wallet: string;
    holeCards: [string, string];
    handRank: string;
    handDescription: string;
  }[];
  winners: {
    wallet: string;
    amount: number;
    potType: "main" | "side";
  }[];
}

interface EliminationEvent {
  wallet: string;
  rank: number;
  eliminatedBy: string;
  lastHand: string;  // Hand ID
}
```

---

## 10. Data Models

### 10.1 PostgreSQL Schema

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
    blind_structure JSONB NOT NULL,
    payout_structure JSONB NOT NULL,
    
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
    agent_sliders JSONB,  -- {aggression, bluff_frequency, tightness, position_awareness}
    agent_prompt_encrypted TEXT,  -- Encrypted custom prompt
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
    ante_amount INTEGER,
    
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
    action VARCHAR(10) NOT NULL,  -- 'fold', 'check', 'call', 'raise', 'all_in'
    amount INTEGER,
    
    -- AI decision metadata
    decision_time_ms INTEGER,
    tokens_used INTEGER,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hand players (who was dealt in)
CREATE TABLE hand_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(id),
    wallet VARCHAR(44) NOT NULL,
    
    seat_position SMALLINT NOT NULL,
    hole_cards VARCHAR(4),  -- "QsQd"
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

### 10.2 Redis Cache Structure

```
# Upstash Redis

# Active tournament state (TTL: duration of tournament)
tournament:{id}:state → JSON {
    phase: "in_progress",
    currentLevel: 3,
    levelStartedAt: timestamp,
    playersRemaining: 18,
    tables: ["table_1", "table_2"]
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
    actionOn: 4
}

# Player session mapping (TTL: 24 hours)
session:{socketId} → {
    wallet: "...",
    tournamentId: "...",
    tableId: "..."
}

# Rate limiting (TTL: 1 minute)
ratelimit:{wallet}:{endpoint} → count
```

---

## 11. Security & Fairness

### 11.1 Provably Fair Randomness

```python
# backend/services/randomness.py

import hashlib
from solders.hash import Hash as Blockhash

class ProvablyFairRNG:
    """
    Generates verifiable random numbers using Solana blockhash commitment.
    
    Process:
    1. At tournament start, commit to a future blockhash (slot N+1)
    2. After slot N+1 is finalized, reveal the blockhash
    3. Use blockhash + tournament_id as seed for all shuffles
    4. Anyone can verify the shuffle by recomputing from public data
    """
    
    def __init__(self, solana_client):
        self.client = solana_client
    
    async def commit_seed(self, tournament_id: str) -> tuple[int, bytes]:
        """
        Commit to using the blockhash of the next slot.
        
        Returns (slot_number, commitment_hash)
        """
        current_slot = await self.client.get_slot()
        commit_slot = current_slot + 1
        
        # Create commitment (cannot be changed)
        commitment = hashlib.sha256(
            f"commit:{tournament_id}:{commit_slot}".encode()
        ).digest()
        
        return commit_slot, commitment
    
    async def reveal_seed(self, slot: int, tournament_id: str) -> bytes:
        """
        Reveal the seed after the slot is finalized.
        
        Returns the actual seed used for RNG.
        """
        blockhash = await self.client.get_block_hash(slot)
        
        seed = hashlib.sha256(
            blockhash.to_bytes() + tournament_id.encode()
        ).digest()
        
        return seed
    
    def generate_deck_seed(self, master_seed: bytes, hand_number: int) -> bytes:
        """
        Generate deterministic seed for a specific hand.
        
        seed = SHA256(master_seed + hand_number)
        """
        return hashlib.sha256(
            master_seed + hand_number.to_bytes(4, 'big')
        ).digest()
```

### 11.2 Agent Prompt Integrity

```python
# backend/services/prompt_integrity.py

import hashlib
from cryptography.fernet import Fernet

class PromptIntegrity:
    """
    Ensures agent prompts cannot be tampered with after registration.
    
    Security model:
    1. User submits prompt during registration
    2. Prompt is encrypted and stored in PostgreSQL
    3. SHA-256 hash is stored on-chain
    4. At tournament start, prompts are locked
    5. Post-tournament, users can optionally reveal prompt for verification
    """
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
    
    def process_prompt(self, prompt: str) -> tuple[str, bytes]:
        """
        Process a prompt for storage.
        
        Returns (encrypted_prompt, hash)
        """
        # Normalize prompt
        normalized = prompt.strip()
        
        # Generate hash
        prompt_hash = hashlib.sha256(normalized.encode()).digest()
        
        # Encrypt for storage
        encrypted = self.cipher.encrypt(normalized.encode()).decode()
        
        return encrypted, prompt_hash
    
    def verify_prompt(self, encrypted: str, expected_hash: bytes) -> bool:
        """Verify prompt matches on-chain hash."""
        decrypted = self.cipher.decrypt(encrypted.encode()).decode()
        actual_hash = hashlib.sha256(decrypted.encode()).digest()
        return actual_hash == expected_hash
    
    def decrypt_for_game(self, encrypted: str) -> str:
        """Decrypt prompt for use during tournament."""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### 11.3 Backend Security

```python
# backend/api/middleware/auth.py

from nacl.signing import VerifyKey
from base58 import b58decode

class WalletAuthMiddleware:
    """
    Verifies wallet ownership via message signing.
    
    Flow:
    1. Client requests nonce for wallet
    2. Client signs nonce with Phantom
    3. Server verifies signature
    4. Server issues session token
    """
    
    async def verify_signature(
        self,
        wallet: str,
        message: bytes,
        signature: bytes,
    ) -> bool:
        """Verify Ed25519 signature from Phantom wallet."""
        try:
            public_key = VerifyKey(b58decode(wallet))
            public_key.verify(message, signature)
            return True
        except Exception:
            return False

# backend/api/middleware/rate_limit.py

class RateLimiter:
    """
    Rate limiting for API endpoints.
    
    Limits:
    - Registration: 5/minute per wallet
    - Agent update: 10/minute per wallet
    - Websocket connections: 3 concurrent per wallet
    """
    
    async def check_limit(
        self,
        wallet: str,
        endpoint: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """Check if request is within rate limit."""
        key = f"ratelimit:{wallet}:{endpoint}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window_seconds)
        return count <= limit
```

### 11.4 Budget Protection

```python
# backend/core/ai/budget.py

class BudgetTracker:
    """
    Prevents runaway API costs.
    
    Budget per tournament = 3x expected cost (from devnet tests)
    
    Example (27 player tournament):
    - Expected: ~$7.20
    - Budget cap: ~$21.60
    """
    
    def __init__(self, redis):
        self.redis = redis
        self.cost_per_1k_tokens = 0.003  # Sonnet 4.5 pricing
    
    async def set_budget(self, tournament_id: str, expected_cost: float):
        """Set budget for a tournament."""
        budget = expected_cost * 3.0
        await self.redis.set(f"budget:{tournament_id}", budget)
        await self.redis.set(f"spent:{tournament_id}", 0)
    
    async def can_make_call(self, tournament_id: str) -> bool:
        """Check if we're within budget."""
        budget = float(await self.redis.get(f"budget:{tournament_id}") or 0)
        spent = float(await self.redis.get(f"spent:{tournament_id}") or 0)
        return spent < budget
    
    async def record_usage(self, tournament_id: str, tokens_used: int):
        """Record API usage."""
        cost = (tokens_used / 1000) * self.cost_per_1k_tokens
        await self.redis.incrbyfloat(f"spent:{tournament_id}", cost)
```

---

## 12. API Reference

### 12.1 REST Endpoints

```yaml
# Admin Endpoints (require admin wallet signature)

POST /api/admin/tournaments
  Description: Create a new tournament
  Body:
    maxPlayers: number (27 or 54)
    startingStack: number
    startsAt: ISO8601 datetime
    blindStructure: string (template name) or BlindLevel[]
    payoutStructure: {rank: points}[]
  Response: Tournament

POST /api/admin/tournaments/{id}/start
  Description: Start registration period
  Response: Tournament

POST /api/admin/tournaments/{id}/cancel
  Description: Cancel tournament (refunds processed)
  Response: Tournament

# Public Endpoints

GET /api/tournaments
  Description: List tournaments
  Query:
    status: created | registration | in_progress | completed
    limit: number (default 20)
    offset: number
  Response: Tournament[]

GET /api/tournaments/{id}
  Description: Get tournament details
  Response: Tournament with registrations count

GET /api/tournaments/{id}/results
  Description: Get tournament results (after completion)
  Response: TournamentResults

GET /api/leaderboard
  Description: Global POINTS leaderboard
  Query:
    limit: number (default 100)
  Response: PlayerStats[]

# Authenticated Endpoints (require wallet signature)

POST /api/tournaments/{id}/register
  Description: Register for tournament
  Body:
    tier: "free" | "basic" | "pro"
    agentName: string (max 32 chars)
    agentImageUri?: string
    agentSliders?: {aggression, bluffFrequency, tightness, positionAwareness}
    customPrompt?: string (200 chars for basic, unlimited for pro)
  Response: Registration

PUT /api/agent
  Description: Update agent configuration (before tournament starts)
  Body: Same as register (partial)
  Response: AgentConfig

GET /api/me
  Description: Get current user's profile
  Response: {wallet, stats, activeRegistrations}
```

### 12.2 WebSocket Events

```yaml
# Client → Server

join:tournament
  Data: {tournamentId: string}
  Description: Subscribe to tournament updates

leave:tournament
  Data: {tournamentId: string}
  Description: Unsubscribe from tournament

subscribe:table
  Data: {tableId: string}
  Description: Subscribe to specific table updates

# Server → Client (Tournament)

tournament:started
  Data: {tournamentId, tables, blindLevel}

tournament:level_up
  Data: {level, smallBlind, bigBlind, ante}

tournament:completed
  Data: {results, winner}

# Server → Client (Table)

table:state
  Data: Full table state snapshot

hand:new
  Data: {handId, tableId, button}

hand:deal
  Data: {holeCards?}  # Only to owner

hand:community
  Data: {cards, round}

hand:action
  Data: {wallet, action, amount, pot}

hand:showdown
  Data: {players, winners}

# Server → Client (Player)

player:eliminated
  Data: {wallet, rank, eliminatedBy}

player:moved
  Data: {wallet, fromTable, toTable}

decision:start
  Data: {wallet, timeoutSeconds}
```

---

## 13. Deployment Guide

### 13.1 Environment Variables

```bash
# .env.example

# Environment
ENVIRONMENT=production
DEBUG=false

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_SOLANA_NETWORK=mainnet-beta
NEXT_PUBLIC_PROGRAM_ID=<deployed_program_id>

# Backend (Railway)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
REDIS_URL=redis://user:pass@host:6379

SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=<key>
ADMIN_WALLET_PUBKEY=<admin_wallet_base58>
TREASURY_WALLET_PUBKEY=<treasury_wallet_base58>
PROGRAM_ID=<deployed_program_id>

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

ENCRYPTION_KEY=<fernet_key_for_prompt_encryption>

CORS_ORIGINS=["https://yourdomain.com"]
```

### 13.2 Deployment Checklist

```markdown
## Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Admin wallet funded
- [ ] Treasury wallet created
- [ ] POINTS SPL token mint created

## Smart Contract (Solana)

- [ ] Build: `anchor build`
- [ ] Test on devnet: `anchor test`
- [ ] Deploy to mainnet: `anchor deploy --provider.cluster mainnet`
- [ ] Initialize arena: Run initialization script
- [ ] Verify program on Solana Explorer

## Backend (Railway)

- [ ] Dockerfile configured
- [ ] Database migrations run
- [ ] Redis connection verified
- [ ] Health check endpoint responding
- [ ] WebSocket connections working
- [ ] Claude API connection verified

## Frontend (Vercel)

- [ ] Build successful
- [ ] Environment variables set
- [ ] Wallet connection working
- [ ] API endpoints reachable
- [ ] WebSocket connection established

## Post-Deployment

- [ ] Create test tournament (devnet clone on mainnet)
- [ ] Register test agents
- [ ] Run full tournament
- [ ] Verify on-chain results
- [ ] Check POINTS distribution
```

### 13.3 Monitoring Setup

```yaml
# Sentry (Error Tracking)
- Backend errors with full context
- Frontend errors with replay
- Performance monitoring
- Alert rules for critical errors

# BetterStack (Uptime)
- API health endpoint: /health
- WebSocket endpoint: wss://api.../health
- Solana RPC availability
- 1-minute check interval
- SMS/Email alerts

# Vercel Analytics
- Page views and performance
- Web Vitals tracking
- Geographic distribution

# Custom Metrics (Log to PostgreSQL)
- Tournaments created/completed
- Players registered per tier
- API tokens consumed
- Decision times
- Win rate by tier (for balancing)
```

---

## 14. Cost Analysis

### 14.1 Per-Tournament Costs

```
27-Player Tournament Estimate:
├── Anthropic API (Claude Sonnet 4.5)
│   ├── Decisions: ~1,000 total
│   ├── Tokens/decision: ~2,000 (with caching)
│   ├── Cost/1K tokens: $0.003
│   ├── Caching savings: 85%
│   └── Subtotal: ~$7.20
│
├── Solana Transactions
│   ├── Tournament creation: 0.001 SOL
│   ├── Player registrations (27): 0.027 SOL
│   ├── Result finalization: 0.001 SOL
│   ├── POINTS distribution (6 winners): 0.006 SOL
│   └── Subtotal: ~0.035 SOL (~$4.50 @ $130/SOL)
│
├── Database (Neon PostgreSQL)
│   └── Negligible per tournament
│
├── Redis (Upstash)
│   └── Negligible per tournament
│
└── TOTAL: ~$11.70 per tournament

Revenue (if all paid tiers):
├── 9 FREE players: $0
├── 9 BASIC players: 0.9 SOL (~$117)
├── 9 PRO players: 9 SOL (~$1,170)
└── MAX POSSIBLE: ~$1,287 per tournament
```

### 14.2 Monthly Infrastructure Costs

```
Low Usage (5 tournaments/month, 50 users):
├── Vercel (Frontend): $0 (hobby tier)
├── Railway (Backend): $20
├── Neon PostgreSQL: $0 (free tier)
├── Upstash Redis: $0 (free tier)
├── Helius RPC: $0 (free tier)
├── Sentry: $0 (free tier)
├── BetterStack: $0 (free tier)
├── Anthropic API: ~$36
├── Solana fees: ~$22.50
└── TOTAL: ~$78.50/month

Medium Usage (20 tournaments/month, 500 users):
├── Vercel (Frontend): $20
├── Railway (Backend): $100
├── Neon PostgreSQL: $25
├── Upstash Redis: $10
├── Helius RPC: $49
├── Sentry: $26
├── BetterStack: $15
├── Anthropic API: ~$144
├── Solana fees: ~$90
└── TOTAL: ~$479/month
```

---

## 15. Legal & Compliance

### 15.1 Terms of Service Requirements

```markdown
## Key TOS Provisions

1. POINTS Nature
   - POINTS are virtual items with no inherent monetary value
   - POINTS are awarded based on AI agent performance
   - POINTS accumulation does not constitute gambling winnings
   - POINTS cannot be exchanged for fiat currency

2. Participation Requirements
   - Users must be 18+ years of age
   - Users must not be residents of Restricted Jurisdictions
   - Users must not be physically located in Restricted Jurisdictions

3. No Gambling Classification
   - Entry fees (0.1 SOL / 1 SOL) are for agent customization features
   - FREE tier available to all users
   - Competition is skill-based (AI strategy optimization)
   - No element of chance in prize distribution (deterministic AI)

4. User Responsibilities
   - Compliance with local laws
   - Accurate jurisdiction representation
   - No use of multiple accounts
```

### 15.2 Registration Checkboxes

```typescript
// Required checkboxes before registration

const LEGAL_CHECKBOXES = [
  {
    id: "tos",
    required: true,
    label: "I have read and agree to the Terms of Service",
    link: "/terms",
  },
  {
    id: "jurisdiction",
    required: true,
    label: "I confirm that I am not a resident of, or person physically located in, any Restricted Jurisdiction as defined in the Terms of Service",
    link: "/terms#restricted-jurisdictions",
  },
];
```

### 15.3 Restricted Jurisdictions

```markdown
The following jurisdictions are restricted (update based on legal review):

- United States (all states)
- United Kingdom
- Australia
- [Additional jurisdictions as advised by legal counsel]

Implementation:
- Checkbox attestation at registration
- No IP blocking (attestation-based)
- Clear disclosure in Terms of Service
```

---

## 16. Development Phases

### Phase 1: Foundation (Weeks 1-3)

```markdown
## Deliverables

### Smart Contract
- [ ] ArenaConfig account
- [ ] Tournament account
- [ ] PlayerRegistration account
- [ ] PlayerStats account
- [ ] Initialize instruction
- [ ] CreateTournament instruction
- [ ] RegisterPlayer instruction
- [ ] Unit tests for all instructions

### Backend Core
- [ ] FastAPI project setup
- [ ] PostgreSQL schema + migrations
- [ ] Redis connection
- [ ] Solana service (RPC connection)
- [ ] Basic health endpoints

### Frontend Shell
- [ ] Next.js project setup
- [ ] Tailwind configuration
- [ ] Wallet adapter integration
- [ ] Basic routing structure
- [ ] Landing page

## Exit Criteria
- Can create tournament on devnet
- Can register player on devnet
- Frontend connects to Phantom wallet
```

### Phase 2: Poker Engine (Weeks 4-6)

```markdown
## Deliverables

### Poker Logic
- [ ] Deck implementation with provably fair shuffle
- [ ] Hand evaluator (all hand rankings)
- [ ] Betting round logic
- [ ] Side pot calculation
- [ ] Texas Hold'em rules enforcement

### Tournament Logic
- [ ] Table creation and seating
- [ ] Blind structure progression
- [ ] Table balancing algorithm
- [ ] Elimination tracking
- [ ] Final standings calculation

### Testing
- [ ] Unit tests for hand evaluator
- [ ] Integration tests for betting rounds
- [ ] Simulation tests (1000 hands)

## Exit Criteria
- Can simulate complete tournament offline
- All poker rules correctly enforced
- Table balancing works correctly
```

### Phase 3: AI Integration (Weeks 7-9)

```markdown
## Deliverables

### Agent System
- [ ] Base agent prompt (~1,500 tokens)
- [ ] Prompt caching implementation
- [ ] Custom prompt handling (tiers)
- [ ] Slider personality system
- [ ] Game state formatter
- [ ] Action parser and validator

### Decision Engine
- [ ] Claude API integration
- [ ] 5s/10s timeout handling
- [ ] Budget tracking
- [ ] Error handling and fallbacks
- [ ] Decision logging

### Integration
- [ ] Connect AI to poker engine
- [ ] End-to-end hand simulation
- [ ] Performance benchmarking

## Exit Criteria
- AI makes valid decisions
- Prompt caching achieving 85%+ savings
- Decision latency within targets
```

### Phase 4: Real-Time & Frontend (Weeks 10-12)

```markdown
## Deliverables

### WebSocket System
- [ ] Socket.IO server setup
- [ ] Tournament event broadcasting
- [ ] Table-specific subscriptions
- [ ] Player-specific hole card delivery
- [ ] Reconnection handling

### Frontend Pages
- [ ] Tournament list page
- [ ] Tournament detail page
- [ ] Registration flow (all tiers)
- [ ] Agent customization page
- [ ] Live tournament view
- [ ] Leaderboard page

### Admin Dashboard
- [ ] Tournament creation form
- [ ] Blind structure templates
- [ ] Payout structure configuration
- [ ] Tournament monitoring
- [ ] Spectator mode (showdown only)

## Exit Criteria
- Full tournament visible in real-time
- All user flows working
- Admin can create and monitor tournaments
```

### Phase 5: On-Chain Settlement (Weeks 13-14)

```markdown
## Deliverables

### Smart Contract Finalization
- [ ] StartTournament instruction
- [ ] FinalizeTournament instruction
- [ ] RecordPlayerResult instruction
- [ ] DistributePoints instruction
- [ ] POINTS SPL token mint

### Backend Integration
- [ ] Tournament start transaction
- [ ] Results hash generation
- [ ] Finalization transaction
- [ ] POINTS distribution

### Verification
- [ ] Prompt hash verification
- [ ] Results hash verification
- [ ] Blockhash seed verification

## Exit Criteria
- Full tournament settles on-chain
- POINTS distributed correctly
- All verifications passing
```

### Phase 6: Testing & Launch (Weeks 15-16)

```markdown
## Deliverables

### Testing
- [ ] Full integration tests
- [ ] Load testing (54 players)
- [ ] Security audit (basic)
- [ ] Devnet beta testing

### Documentation
- [ ] API documentation
- [ ] User guide
- [ ] Admin guide
- [ ] Terms of Service

### Launch
- [ ] Mainnet deployment
- [ ] Monitoring setup
- [ ] First tournament (27 players)

## Exit Criteria
- System handles 27-player tournament
- No critical bugs
- Documentation complete
- First tournament successful
```

---

## 17. Anti-Patterns: What NOT to Do

### 17.1 Smart Contract Anti-Patterns

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

### 17.2 AI Decision Anti-Patterns

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

### 17.3 Backend Anti-Patterns

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

### 17.4 Frontend Anti-Patterns

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

### 17.5 Tournament Logic Anti-Patterns

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

## 18. Error Handling Strategy

### 18.1 Graceful Degradation Hierarchy

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

### 18.2 Error Response Format

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

// Error codes
const ERROR_CODES = {
  // Auth (1xxx)
  WALLET_NOT_CONNECTED: "1001",
  INVALID_SIGNATURE: "1002",
  SESSION_EXPIRED: "1003",
  
  // Tournament (2xxx)
  TOURNAMENT_NOT_FOUND: "2001",
  TOURNAMENT_FULL: "2002",
  REGISTRATION_CLOSED: "2003",
  ALREADY_REGISTERED: "2004",
  TOURNAMENT_NOT_STARTED: "2005",
  
  // Agent (3xxx)
  INVALID_TIER: "3001",
  PROMPT_TOO_LONG: "3002",
  AGENT_LOCKED: "3003",
  
  // Payment (4xxx)
  INSUFFICIENT_BALANCE: "4001",
  TRANSACTION_FAILED: "4002",
  
  // System (5xxx)
  RATE_LIMITED: "5001",
  SERVICE_UNAVAILABLE: "5002",
  INTERNAL_ERROR: "5003",
};
```

### 18.3 User-Facing Error Messages

```typescript
// Never expose internal errors. Map to friendly messages:

const USER_MESSAGES: Record<string, string> = {
  // Good: Actionable, friendly
  "TOURNAMENT_FULL": "This tournament is full. Check back for the next one!",
  "INSUFFICIENT_BALANCE": "You need {amount} SOL in your wallet to register.",
  "RATE_LIMITED": "Too many requests. Please wait {seconds} seconds.",
  "SERVICE_UNAVAILABLE": "We're experiencing issues. Please try again in a moment.",
  
  // Bad: Never show these to users
  // "DatabaseConnectionError: connection pool exhausted"
  // "anthropic.RateLimitError: 429 Too Many Requests"
  // "SolanaRpcError: Transaction simulation failed"
};
```

---

## 19. Testing Strategy

### 19.1 Coverage Requirements

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
    └── Account validation

90%+ TARGET:
├── Tournament Manager
├── Table Balancing
├── WebSocket Event Handlers
└── API Endpoints
```

### 19.2 Integration Test Scenarios

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
```

### 19.3 Load Testing Targets

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

### 19.4 Test Data Fixtures

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
```

---

## 20. State Machines

### 20.1 Tournament State Machine

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

### 20.2 Hand State Machine

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
│   DEALING    │  Hole cards distributed
└──────┬───────┘
       │
       ▼
┌──────────────┐     all_fold()     ┌──────────────────┐
│   PREFLOP    │ ─────────────────► │ WINNER_DETERMINED│
│              │                    │                  │
│ Blinds posted│                    │ Last player wins │
│ First betting│                    │ No showdown      │
└──────┬───────┘                    └──────────────────┘
       │ betting_complete()                 ▲
       ▼                                    │
┌──────────────┐     all_fold()             │
│    FLOP      │ ───────────────────────────┤
│              │                            │
│ 3 community  │                            │
│ cards dealt  │                            │
└──────┬───────┘                            │
       │ betting_complete()                 │
       ▼                                    │
┌──────────────┐     all_fold()             │
│    TURN      │ ───────────────────────────┤
│              │                            │
│ 4th community│                            │
│ card dealt   │                            │
└──────┬───────┘                            │
       │ betting_complete()                 │
       ▼                                    │
┌──────────────┐     all_fold()             │
│    RIVER     │ ───────────────────────────┤
│              │                            │
│ 5th community│                            │
│ card dealt   │                            │
└──────┬───────┘                            │
       │ betting_complete()                 │
       ▼                                    │
┌──────────────┐                            │
│   SHOWDOWN   │ ───────────────────────────┘
│              │     evaluate_hands()
│ Hands reveal │
│ Best wins    │
└──────────────┘

Notes:
- "all_fold()" = all but one player folds
- "betting_complete()" = all active players have acted and bets are matched
- From any betting state, if all players are all-in, skip to SHOWDOWN
```

### 20.3 Player State Machine (Within Hand)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PLAYER STATE MACHINE (PER HAND)                       │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│    ACTIVE    │ ◄───────────────────────────────────┐
│              │                                     │
│ Can take     │                                     │
│ actions      │                                     │
└──────┬───────┘                                     │
       │                                             │
       ├── fold() ──────────► ┌──────────────┐      │
       │                      │    FOLDED    │      │
       │                      │              │      │
       │                      │ Out of hand  │      │
       │                      │ Keep stack   │      │
       │                      └──────────────┘      │
       │                                             │
       ├── check() ─────────────────────────────────┘
       │                                             │
       ├── call() ──────────────────────────────────┘
       │                                             │
       ├── raise() ─────────────────────────────────┘
       │                                             │
       └── all_in() ────────► ┌──────────────┐
                              │   ALL_IN     │
                              │              │
                              │ No more      │
                              │ actions      │
                              │ Wait for     │
                              │ showdown     │
                              └──────────────┘

Transitions to ELIMINATED (separate lifecycle):
- If stack == 0 at end of hand → ELIMINATED from tournament
```

---

## 21. API Response Definitions

### 21.1 REST API Response Types

```typescript
// types/api.ts

// ============ Common Types ============

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  requestId: string;
}

// ============ Tournament Types ============

interface TournamentResponse {
  id: string;
  onChainId: number;
  status: "created" | "registration" | "in_progress" | "completed" | "cancelled";
  
  // Configuration
  maxPlayers: number;
  registeredPlayers: number;
  startingStack: number;
  
  // Timing
  createdAt: string;  // ISO8601
  startsAt: string;
  completedAt: string | null;
  
  // Structure (summaries, not full data)
  blindStructure: {
    template: string;
    currentLevel?: number;
    levels: number;
  };
  payoutStructure: {
    positions: number;
    topPrize: number;
  };
  
  // Results (only when completed)
  results?: {
    winner: {
      wallet: string;
      agentName: string;
    };
    resultsHash: string;
    totalHands: number;
    duration: number;  // seconds
  };
}

interface TournamentListResponse extends PaginatedResponse<TournamentResponse> {}

interface TournamentDetailResponse extends TournamentResponse {
  // Additional detail fields
  blindStructure: BlindLevel[];
  payoutStructure: PayoutEntry[];
  registrations: RegistrationSummary[];
}

// ============ Registration Types ============

interface RegistrationRequest {
  tier: "free" | "basic" | "pro";
  agentName: string;
  agentImageUri?: string;
  agentSliders?: AgentSliders;
  customPrompt?: string;  // Encrypted in transit
}

interface RegistrationResponse {
  id: string;
  tournamentId: string;
  wallet: string;
  tier: "free" | "basic" | "pro";
  agentName: string;
  agentImageUri: string | null;
  registeredAt: string;
  promptHash: string;  // SHA-256 hex
  
  // Transaction details
  transactionSignature: string;
  onChainConfirmed: boolean;
}

interface RegistrationSummary {
  wallet: string;
  agentName: string;
  agentImageUri: string | null;
  tier: "free" | "basic" | "pro";
}

// ============ Agent Types ============

interface AgentSliders {
  aggression: number;        // 0-100
  bluffFrequency: number;    // 0-100
  tightness: number;         // 0-100
  positionAwareness: number; // 0-100
}

interface AgentConfigResponse {
  wallet: string;
  name: string;
  imageUri: string | null;
  tier: "free" | "basic" | "pro";
  sliders: AgentSliders | null;
  promptLength: number;  // Characters, not the actual prompt
  promptHash: string;
  createdAt: string;
  updatedAt: string;
}

// ============ Leaderboard Types ============

interface LeaderboardEntry {
  rank: number;
  wallet: string;
  agentName: string;
  totalPoints: number;
  tournamentsPlayed: number;
  tournamentsWon: number;
  bestFinish: number;
  winRate: number;  // Percentage
}

interface LeaderboardResponse extends PaginatedResponse<LeaderboardEntry> {}

// ============ Results Types ============

interface TournamentResultsResponse {
  tournamentId: string;
  completedAt: string;
  totalPlayers: number;
  totalHands: number;
  duration: number;  // seconds
  
  standings: PlayerResult[];
  
  // Verification
  resultsHash: string;
  seedBlockhash: string;
  seedSlot: number;
}

interface PlayerResult {
  rank: number;
  wallet: string;
  agentName: string;
  tier: "free" | "basic" | "pro";
  pointsAwarded: number;
  handsPlayed: number;
  eliminations: number;
  eliminatedBy: string | null;  // Winner has null
}

// ============ Blind Structure Types ============

interface BlindLevel {
  level: number;
  smallBlind: number;
  bigBlind: number;
  ante: number;
  durationMinutes: number;
}

interface PayoutEntry {
  rank: number;
  points: number;
  percentage?: number;  // Optional, for display
}
```

### 21.2 WebSocket Message Types

```typescript
// types/websocket.ts

// ============ Server → Client Events ============

interface WsTableState {
  tableId: string;
  tournamentId: string;
  seats: WsSeat[];
  button: number;
  pot: number;
  communityCards: string[];  // e.g., ["Ah", "Kd", "7c"]
  currentBet: number;
  minRaise: number;
  bettingRound: "preflop" | "flop" | "turn" | "river";
  actionOn: number | null;  // Seat index, null if no action pending
}

interface WsSeat {
  position: number;          // 0-8
  wallet: string | null;     // null if empty seat
  agentName: string | null;
  agentImage: string | null;
  stack: number;
  currentBet: number;
  status: "waiting" | "active" | "folded" | "all_in" | "eliminated";
  holeCards?: [string, string];  // Only sent to owner
  isActing: boolean;
  timeRemaining?: number;    // Countdown seconds
}

interface WsHandDeal {
  handId: string;
  tableId: string;
  button: number;
  holeCards?: [string, string];  // Only to owner
}

interface WsPlayerAction {
  tableId: string;
  handId: string;
  wallet: string;
  seatPosition: number;
  action: "fold" | "check" | "call" | "raise" | "all_in";
  amount: number | null;
  newStack: number;
  pot: number;
  timestamp: string;
}

interface WsShowdown {
  tableId: string;
  handId: string;
  communityCards: string[];
  players: {
    wallet: string;
    seatPosition: number;
    holeCards: [string, string];
    handRank: string;        // "Pair", "Flush", etc.
    handDescription: string; // "Pair of Kings, Ace kicker"
    isWinner: boolean;
  }[];
  pots: {
    type: "main" | "side";
    amount: number;
    winners: string[];       // Wallet addresses
    amountPerWinner: number;
  }[];
}

interface WsElimination {
  wallet: string;
  agentName: string;
  rank: number;
  eliminatedBy: string;      // Wallet of eliminator
  pointsAwarded: number;
  lastHandId: string;
}

interface WsLevelUp {
  level: number;
  smallBlind: number;
  bigBlind: number;
  ante: number;
  nextLevelIn: number;       // Seconds
}

// ============ Client → Server Events ============

interface WsJoinTournament {
  tournamentId: string;
  wallet: string;
  signature: string;         // For auth
}

interface WsSubscribeTable {
  tableId: string;
}
```

---

## 22. Environment Configuration

### 22.1 Environment-Specific Behavior

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Solana Network** | localhost/devnet | devnet | mainnet-beta |
| **RPC Endpoint** | localhost:8899 | Helius devnet | Helius mainnet |
| **Claude Model** | claude-3-haiku-20240307 | claude-sonnet-4-5-20250929 | claude-sonnet-4-5-20250929 |
| **Decision Timeout** | 30s (debugging) | 5s / 10s | 5s / 10s |
| **Budget Multiplier** | 10x (testing) | 3x | 3x |
| **CORS Origins** | localhost:3000 | staging.domain.com | domain.com |
| **Log Level** | DEBUG | INFO | INFO |
| **Error Details** | Full stack traces | Sanitized | Sanitized |
| **Database** | Local PostgreSQL | Neon (staging branch) | Neon (main branch) |
| **Redis** | Local Redis | Upstash (staging) | Upstash (production) |
| **SSL** | Disabled | Enabled | Enabled |
| **Rate Limits** | Disabled | Relaxed (5x prod) | Enforced |

### 22.2 Feature Flags

```python
# config.py

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

## 23. Prompt Caching Implementation

### 23.1 Cache Architecture

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
│  │  Custom Prompt (0-500 tokens)                                      │  │
│  │  • Personality sliders                                             │  │
│  │  • User freeform instructions                                      │  │
│  │                                                                    │  │
│  │  Game State (~300 tokens)                                          │  │
│  │  • Current hand info                                               │  │
│  │  • Player stacks                                                   │  │
│  │  • Action history                                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 23.2 Token Breakdown Per Decision

| Component | Tokens | Cached | Cost/1K |
|-----------|--------|--------|---------|
| Base Engine | ~1,500 | ✅ Yes | $0.00045 (85% off) |
| Custom Prompt (Pro) | 0-500 | ❌ No | $0.003 |
| Custom Prompt (Basic) | 0-100 | ❌ No | $0.003 |
| Game State | ~300 | ❌ No | $0.003 |
| **Response** | ~50 | N/A | $0.015 |

**Cost per decision (with caching):**
- FREE tier: ~$0.00135 (base cached + state + response)
- PRO tier: ~$0.00285 (base cached + custom + state + response)

**Cost per tournament (27 players, ~1000 decisions):**
- Without caching: ~$24.00
- With caching: ~$7.20 (70% savings)

### 23.3 Cache Management

```python
# backend/core/ai/cache_manager.py

class PromptCacheManager:
    """
    Manages Anthropic prompt cache lifecycle.
    
    Cache behavior:
    - TTL: 5 minutes of inactivity
    - Key: SHA256 of cached content
    - Automatic refresh on cache hit
    """
    
    def __init__(self):
        self.last_call_time: dict[str, datetime] = {}  # tournament_id -> timestamp
        self.cache_warmed: set[str] = set()
    
    async def warm_cache(self, tournament_id: str):
        """
        Make a dummy API call before tournament starts.
        
        This ensures the base prompt is cached when real hands begin.
        """
        if tournament_id in self.cache_warmed:
            return
        
        # Minimal call to warm cache
        await self._make_cache_warming_call()
        self.cache_warmed.add(tournament_id)
    
    async def ensure_cache_fresh(self, tournament_id: str):
        """
        Ensure cache hasn't expired between hands.
        
        If >4 minutes since last call, make a keep-alive request.
        """
        last = self.last_call_time.get(tournament_id)
        if last and (datetime.now() - last) > timedelta(minutes=4):
            await self._make_cache_warming_call()
        
        self.last_call_time[tournament_id] = datetime.now()
    
    def build_cached_messages(self, agent_config: AgentConfig) -> list[dict]:
        """
        Build message array with cache markers.
        
        Returns format expected by Anthropic SDK.
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": BASE_AGENT_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}  # ← Cache marker
                    },
                    {
                        "type": "text",
                        "text": agent_config.custom_prompt or ""
                    }
                ]
            }
        ]
```

---

## 24. Logging Standards

### 24.1 Log Levels

```python
# Logging level definitions and usage

LOGGING_GUIDELINES = """
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
"""
```

### 24.2 Structured Log Format

```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "INFO",
  "service": "tournament-engine",
  "version": "1.2.3",
  "environment": "production",
  
  "event": "player_eliminated",
  "tournament_id": "abc123",
  "table_id": "table_1",
  "hand_id": "hand_47",
  
  "data": {
    "wallet": "7xKXtg2CW87...",
    "agent_name": "PokerBot3000",
    "rank": 15,
    "eliminated_by": "9yMNtd3DX98...",
    "final_stack": 0,
    "hands_played": 47
  },
  
  "trace_id": "req_abc123xyz",
  "span_id": "span_456"
}
```

### 24.3 Sensitive Data Handling

```python
# What to NEVER log

NEVER_LOG = [
    "agent_prompt",           # Competitive advantage
    "custom_instructions",    # User secrets
    "wallet_private_key",     # Obviously
    "api_keys",               # Any service
    "hole_cards",             # During active hand (INFO level)
    "session_tokens",         # Security risk
]

# What to REDACT

def redact_wallet(wallet: str) -> str:
    """Show first 4 and last 4 characters only."""
    return f"{wallet[:4]}...{wallet[-4:]}"

def redact_for_logging(data: dict) -> dict:
    """Sanitize sensitive fields before logging."""
    sanitized = data.copy()
    
    if "wallet" in sanitized:
        sanitized["wallet"] = redact_wallet(sanitized["wallet"])
    
    if "prompt" in sanitized:
        sanitized["prompt"] = f"<{len(sanitized['prompt'])} chars>"
    
    if "hole_cards" in sanitized:
        sanitized["hole_cards"] = "[REDACTED]"
    
    return sanitized
```

---

## 25. Pinned Dependencies

### 25.1 Backend (Python)

```toml
# pyproject.toml

[tool.poetry.dependencies]
python = "^3.11"

# Web framework
fastapi = "0.109.x"
uvicorn = {extras = ["standard"], version = "0.27.x"}
starlette = "0.35.x"

# Database
sqlalchemy = "2.0.x"
asyncpg = "0.29.x"
alembic = "1.13.x"

# Redis
redis = "5.0.x"

# Solana
solana = "0.32.x"
solders = "0.20.x"
anchorpy = "0.19.x"

# AI
anthropic = "0.18.x"

# Security
pynacl = "1.5.x"
python-jose = "3.3.x"
passlib = "1.7.x"

# Utilities
pydantic = "2.6.x"
pydantic-settings = "2.1.x"
python-dotenv = "1.0.x"
httpx = "0.26.x"

[tool.poetry.group.dev.dependencies]
pytest = "8.0.x"
pytest-asyncio = "0.23.x"
pytest-cov = "4.1.x"
black = "24.1.x"
ruff = "0.2.x"
mypy = "1.8.x"
```

### 25.2 Frontend (Node)

```json
{
  "engines": {
    "node": "20.x"
  },
  "dependencies": {
    "next": "14.1.x",
    "react": "18.2.x",
    "react-dom": "18.2.x",
    "typescript": "5.3.x",
    
    "@solana/web3.js": "1.89.x",
    "@solana/wallet-adapter-react": "0.15.x",
    "@solana/wallet-adapter-react-ui": "0.9.x",
    "@solana/wallet-adapter-wallets": "0.19.x",
    
    "zustand": "4.5.x",
    "socket.io-client": "4.7.x",
    
    "tailwindcss": "3.4.x",
    "@headlessui/react": "1.7.x",
    "lucide-react": "0.321.x"
  },
  "devDependencies": {
    "@types/node": "20.11.x",
    "@types/react": "18.2.x",
    "eslint": "8.56.x",
    "eslint-config-next": "14.1.x",
    "prettier": "3.2.x"
  }
}
```

### 25.3 Smart Contracts (Rust/Anchor)

```toml
# Cargo.toml

[dependencies]
anchor-lang = "0.30.0"
anchor-spl = "0.30.0"

[dev-dependencies]
anchor-client = "0.30.0"

# Anchor.toml
[toolchain]
anchor_version = "0.30.0"
solana_version = "1.17.x"
```

---

## 26. Example: Complete Hand Execution

### 26.1 Setup

```
Tournament: Weekly Showdown #42
Players: 27 (started), 18 remaining
Level: 4 (100/200, 25 ante)
Table 1: 8 players

Seats:
0. [UTG]   Player_A   Stack: 4,200
1. [UTG+1] Player_B   Stack: 3,100
2. [MP]    Player_C   Stack: 5,800
3. [MP2]   Player_D   Stack: 2,400
4. [HJ]    Player_E   Stack: 6,200 ← YOU (Pro tier, aggressive settings)
5. [CO]    Player_F   Stack: 4,500
6. [BTN]   Player_G   Stack: 3,800
7. [SB]    Player_H   Stack: 2,900
8. [BB]    Player_I   Stack: 5,100

Hand #127
```

### 26.2 Execution Trace

```
═══════════════════════════════════════════════════════════════════════════
HAND #127 EXECUTION TRACE
═══════════════════════════════════════════════════════════════════════════

[T+0ms] HAND START
├── State: DEALING
├── Button: Seat 6 (Player_G)
├── Deck Seed: SHA256(master_seed + "127") = 0x7a3f...
└── Shuffle: Fisher-Yates with seeded PRNG

[T+5ms] DEAL HOLE CARDS
├── Seat 0 (Player_A): 7♠ 2♦
├── Seat 1 (Player_B): K♣ 9♣
├── Seat 2 (Player_C): A♦ Q♦
├── Seat 3 (Player_D): 5♥ 5♦
├── Seat 4 (Player_E): A♠ K♥  ← Your cards (visible to you only)
├── Seat 5 (Player_F): J♦ T♦
├── Seat 6 (Player_G): 8♣ 3♠
├── Seat 7 (Player_H): Q♠ J♠
└── Seat 8 (Player_I): 6♦ 6♣

[T+10ms] POST BLINDS & ANTES
├── Antes: 8 players × 25 = 200
├── SB (Seat 7): 100
├── BB (Seat 8): 200
└── Pot: 500

───────────────────────────────────────────────────────────────────────────
PREFLOP BETTING ROUND
───────────────────────────────────────────────────────────────────────────

[T+100ms] ACTION ON: Seat 0 (UTG)
├── Claude API Call
│   ├── Input tokens: 1,847 (1,500 cached + 347 dynamic)
│   ├── Cache status: HIT (85% discount)
│   └── Response: {"action": "fold"}
├── Decision time: 1.2s
└── Pot: 500

[T+1.3s] ACTION ON: Seat 1 (UTG+1)
├── Claude API Call: {"action": "fold"}
├── Decision time: 0.9s
└── Pot: 500

[T+2.2s] ACTION ON: Seat 2 (MP)
├── Claude API Call: {"action": "raise", "amount": 500}
│   └── Reasoning: "AQs is premium in MP, standard 2.5x open"
├── Decision time: 1.4s
└── Pot: 1,000

[T+3.6s] ACTION ON: Seat 3 (MP2)
├── Claude API Call: {"action": "call"}
│   └── Reasoning: "55 has good implied odds, set-mining"
├── Decision time: 1.1s
└── Pot: 1,500

[T+4.7s] ACTION ON: Seat 4 (HJ) ← YOUR AGENT
├── Claude API Call
│   ├── System prompt: Base engine (cached) + Your custom prompt
│   ├── Your sliders: aggression=75, bluff=40, tight=60, position=80
│   ├── Game state: AKo in HJ, facing raise + call, 31 BB effective
│   └── Response: {"action": "raise", "amount": 1,600}
├── Reasoning: "Premium hand in position, 3-bet to isolate and build pot"
├── Decision time: 1.8s
└── Pot: 3,100

[T+6.5s] ACTION ON: Seat 5 (CO)
├── Claude API Call: {"action": "fold"}
└── Pot: 3,100

[T+7.4s] ACTION ON: Seat 6 (BTN)
├── Claude API Call: {"action": "fold"}
└── Pot: 3,100

[T+8.3s] ACTION ON: Seat 7 (SB)
├── Claude API Call: {"action": "fold"}
└── Pot: 3,100

[T+9.2s] ACTION ON: Seat 8 (BB)
├── Claude API Call: {"action": "fold"}
└── Pot: 3,100

[T+10.0s] ACTION ON: Seat 2 (MP) - Original raiser
├── Claude API Call: {"action": "call"}
│   └── Reasoning: "AQs plays well vs 3-bet, in position postflop"
├── Decision time: 1.3s
└── Pot: 4,200

[T+11.3s] ACTION ON: Seat 3 (MP2)
├── Claude API Call: {"action": "fold"}
│   └── Reasoning: "55 can't profitably call 3-bet OOP, SPR too low"
└── Pot: 4,200

───────────────────────────────────────────────────────────────────────────
FLOP: K♦ 7♣ 2♠
───────────────────────────────────────────────────────────────────────────

[T+12.0s] DEAL FLOP
├── Pot: 4,200
├── Your hand: A♠ K♥ → Top pair, top kicker
└── Opponent (Seat 2): A♦ Q♦ → Missed, two overs

[T+12.1s] ACTION ON: Seat 2 (first to act postflop)
├── Claude API Call: {"action": "check"}
│   └── Reasoning: "Missed flop, checking to aggressor"
└── Pot: 4,200

[T+13.3s] ACTION ON: Seat 4 ← YOUR AGENT
├── Claude API Call
│   ├── Board analysis: Dry board, top pair is strong
│   └── Response: {"action": "raise", "amount": 2,100}
├── Reasoning: "Strong value bet, 50% pot on dry board"
├── Decision time: 1.5s
└── Pot: 6,300

[T+14.8s] ACTION ON: Seat 2
├── Claude API Call: {"action": "call"}
│   └── Reasoning: "Two overs + backdoor nut flush, pot odds acceptable"
└── Pot: 8,400

───────────────────────────────────────────────────────────────────────────
TURN: K♦ 7♣ 2♠ 9♦
───────────────────────────────────────────────────────────────────────────

[T+16.0s] DEAL TURN
├── Your hand: Still top pair, opponent picked up flush draw
└── Pot: 8,400

[T+16.1s] ACTION ON: Seat 2
├── Claude API Call: {"action": "check"}
└── Pot: 8,400

[T+17.2s] ACTION ON: Seat 4 ← YOUR AGENT
├── Claude API Call
│   ├── Board analysis: Flush draw possible, continue value betting
│   └── Response: {"action": "raise", "amount": 4,200}
├── Reasoning: "Bet 50% pot for value, charge draws"
├── Decision time: 1.6s
└── Pot: 12,600

[T+18.8s] ACTION ON: Seat 2
├── Claude API Call: {"action": "call"}
│   └── Reasoning: "Nut flush draw, 2:1 pot odds, need 33%, have ~20% + implied"
└── Pot: 16,800

───────────────────────────────────────────────────────────────────────────
RIVER: K♦ 7♣ 2♠ 9♦ 4♥
───────────────────────────────────────────────────────────────────────────

[T+20.0s] DEAL RIVER
├── Your hand: Still top pair top kicker
├── Opponent: Missed flush draw, A-high only
└── Pot: 16,800

[T+20.1s] ACTION ON: Seat 2
├── Claude API Call: {"action": "check"}
│   └── Reasoning: "Missed draw, cannot bluff into capped range"
└── Pot: 16,800

[T+21.3s] ACTION ON: Seat 4 ← YOUR AGENT
├── Claude API Call
│   ├── Timeout: 10s (all-in consideration)
│   ├── Stack remaining: 2,500
│   └── Response: {"action": "raise", "amount": 2,500}  // All-in
├── Reasoning: "Value shove, can be called by worse Kings, some 7x"
├── Decision time: 2.1s
└── Pot: 19,300

[T+23.4s] ACTION ON: Seat 2
├── Claude API Call: {"action": "fold"}
│   └── Reasoning: "Cannot beat any value hands, A-high never good here"
├── Decision time: 1.4s
└── Pot: 19,300

───────────────────────────────────────────────────────────────────────────
HAND COMPLETE - NO SHOWDOWN
───────────────────────────────────────────────────────────────────────────

[T+24.8s] WINNER DETERMINED
├── Winner: Seat 4 (YOUR AGENT)
├── Amount won: 19,300
├── New stack: 6,200 + 19,300 = 25,500
├── Hand not shown (no showdown)
└── Cards mucked

[T+25.0s] DATABASE WRITES
├── hand_history: Insert complete hand record
├── hand_actions: 14 actions recorded
├── hand_players: 9 players with outcomes
└── player_stats: Update running totals

[T+25.5ms] WEBSOCKET BROADCASTS
├── hand:complete → All table subscribers
│   └── {tableId, handId, winner: "Seat 4", amount: 19300}
├── table:state → Updated stacks for all
└── (Hole cards NOT broadcast - no showdown)

═══════════════════════════════════════════════════════════════════════════
HAND #127 SUMMARY
═══════════════════════════════════════════════════════════════════════════

Duration: 25.5 seconds
API Calls: 14 decisions
Total Tokens: ~25,800 input, ~700 output
Estimated Cost: $0.12 (with 85% caching)
Winner: Your agent (Seat 4 / Player_E)
Pot Size: 19,300 chips

Your agent gained: +13,100 chips (from 6,200 to 19,300... wait, let me recalculate)
Actually: Started with 6,200, won pot of 19,300, but invested 4,200 in pot
Net gain: +15,100 chips
Final stack: 6,200 - 4,200 (invested) + 19,300 (won) = 21,300

Moving to Hand #128...
```

---

## Appendix A: Quick Reference

### Key Constants

```typescript
const CONSTANTS = {
  // Table
  TABLE_SIZE: 9,
  
  // Timing (seconds)
  DECISION_TIMEOUT_NORMAL: 5,
  DECISION_TIMEOUT_ALL_IN: 10,
  
  // Tiers
  TIER_FREE_COST: 0,
  TIER_BASIC_COST: 0.1,  // SOL
  TIER_PRO_COST: 1.0,    // SOL
  
  // Prompts
  TIER_BASIC_CHAR_LIMIT: 200,
  TIER_PRO_CHAR_LIMIT: Infinity,
  
  // Budget
  BUDGET_MULTIPLIER: 3.0,
  
  // Scale
  INITIAL_MAX_PLAYERS: 27,
  TARGET_MAX_PLAYERS: 54,
};
```

### Common Commands

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

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI-powered bot that makes poker decisions for a user |
| **All-In** | Betting all remaining chips; cannot take further action |
| **Ante** | Forced bet from all players before each hand |
| **Blockhash Commitment** | Using a Solana blockhash as a verifiable random seed |
| **Button (BTN)** | Dealer position; acts last post-flop, best position |
| **Commitment Hash** | SHA-256 hash stored on-chain before tournament for RNG verification |
| **Cutoff (CO)** | Position to the right of the button; second-best position |
| **Effective Stack** | Minimum stack between two players in a pot (relevant for all-in decisions) |
| **EV (Expected Value)** | Average outcome of a decision over infinite iterations |
| **Heads Up** | Two players remaining in tournament or hand |
| **Hijack (HJ)** | Position to the right of the cutoff |
| **ICM** | Independent Chip Model — tournament equity calculation |
| **Implied Odds** | Potential future winnings beyond current pot odds |
| **Min-Raise** | Smallest legal raise; must be at least the size of previous raise |
| **PDA** | Program Derived Address — deterministic Solana account address |
| **POINTS** | SPL token awarded for tournament performance |
| **Pot Odds** | Ratio of call amount to total pot size |
| **SPR** | Stack-to-Pot Ratio — key metric for commitment decisions |
| **Side Pot** | Additional pot created when player is all-in but others continue betting |
| **Tier** | Agent customization level (FREE / BASIC / PRO) |
| **UTG** | Under The Gun — first to act preflop; worst position |
| **VRF** | Verifiable Random Function — cryptographic random number generation |

---

## Appendix C: Contact & Resources

```markdown
## Development Resources

- Solana Docs: https://docs.solana.com
- Anchor Docs: https://www.anchor-lang.com
- Anthropic API: https://docs.anthropic.com
- Next.js Docs: https://nextjs.org/docs
- FastAPI Docs: https://fastapi.tiangolo.com

## Project Links

- Repository: [TBD]
- Deployed App: [TBD]
- Program ID: [TBD after deployment]
```

---

**END OF CONTEXT DECLARATION**

*This document should be the first file read by any AI assistant or developer working on this project. Keep it updated as the project evolves.*
