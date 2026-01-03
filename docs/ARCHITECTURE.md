# Architecture

This document covers the system architecture, component diagrams, and technology stack for the Poker Agent Arena.

---

## Table of Contents

1. [High-Level System Architecture](#high-level-system-architecture)
2. [Data Flow: Tournament Lifecycle](#data-flow-tournament-lifecycle)
3. [Component Interaction Diagram](#component-interaction-diagram)
4. [Tech Stack](#tech-stack)
5. [Directory Structure](#directory-structure)

---

## High-Level System Architecture

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
│  │ ├───────────┤ │  │          │  │    claude-sonnet-4-5-20250929       │ │
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

---

## Data Flow: Tournament Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TOURNAMENT LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────────────┘

1. CREATION (Admin Only)
   Admin Wallet ──► Anchor Program ──► Create Tournament PDA
                                       • Set blind structure (with BB-only antes)
                                       • Set starting stacks
                                       • Set payout structure (admin-customized)
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
   │ Engine  │  │ Sliders Only    │  │ Sliders +       │  │  • Prompt Hash  │
   │ Only    │  │                 │  │ Freeform Prompt │  │  • Timestamp    │
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
   │  Post Blinds + Ante (BB only) ──► Deal Cards ──► Betting Rounds     │
   │       │                                │                             │
   │       │                                ▼                             │
   │       │                    ┌─────────────────────────────────────────┐
   │       │                    │  FOR EACH DECISION:                      │
   │       │                    │                                          │
   │       │                    │  Build Context ──► Claude API ──► Parse  │
   │       │                    │       │                │          Action │
   │       │                    │       │                │                 │
   │       │                    │  [Base Engine]    [5s normal]     [fold/ │
   │       │                    │  [Custom Prompt]  [10s all-in]    call/  │
   │       │                    │  [Game State]                     raise] │
   │       │                    └─────────────────────────────────────────┘
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
   Final Table ──► Heads Up ──► Winner ──► Calculate Payouts (admin-defined)
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

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT INTERACTIONS                           │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────┐
                    │         ADMIN DASHBOARD          │
                    │  • Create tournaments            │
                    │  • Define blind structures       │
                    │  • Set payout tables (custom)    │
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
│                    │  • Post BB + Ante  │                          │  │
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
│  │  │ • Position   │  │   (BASIC+PRO)│  │ • Pot size   │       │ │ │
│  │  │ • ICM        │  │ • Freeform   │  │ • Actions    │       │ │ │
│  │  │ • SPR        │  │   (PRO only) │  │ • Cards      │       │ │ │
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
│  │              CLAUDE claude-sonnet-4-5-20250929               │ │ │
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

## Tech Stack

### Complete Technology Matrix

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
| **AI** | Claude `claude-sonnet-4-5-20250929` | Agent decisions | ~$7.20/tournament |
| **Monitoring** | Vercel Analytics | Frontend metrics | Free |
| | Sentry | Error tracking | $0-26/mo |
| | BetterStack | Uptime monitoring | $0-15/mo |

---

## Directory Structure

```
poker-agent-arena/
├── README.md                    # Main context declaration
├── docs/                        # Detailed documentation
│   ├── ARCHITECTURE.md          # This file
│   ├── SMART_CONTRACT.md
│   ├── BACKEND.md
│   ├── FRONTEND.md
│   ├── DATA_MODELS.md
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   └── LEGAL.md
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
│   │   │   ├── blinds.py        # Blind structure (with BB-only antes)
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
