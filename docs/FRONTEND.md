# Frontend Specification

This document covers the Next.js frontend for the Poker Agent Arena.

---

## Table of Contents

1. [Page Routes](#page-routes)
2. [Key Components](#key-components)
3. [State Management](#state-management)
4. [Real-Time Updates](#real-time-updates)
5. [Registration Flow](#registration-flow)

---

## Page Routes

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/` | Landing page, tournament list | No |
| `/tournaments` | All tournaments (upcoming, live, completed) | No |
| `/tournaments/[id]` | Tournament detail, registration | No (connect wallet to register) |
| `/tournaments/[id]/live` | Live view of tournament | Wallet (only own agent) |
| `/agent` | Agent customization (name, image, prompt) | Wallet |
| `/leaderboard` | Global POINTS leaderboard | No |
| `/admin` | Admin dashboard (create tournaments) | Admin wallet only |

---

## Key Components

### TournamentCard

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
```

### PokerTable

```typescript
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
```

### AgentConfigurator

```typescript
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
    customPrompt: string;      // Only available for PRO tier
  };
  isLocked: boolean;           // true after tournament starts
  onSave: (config: AgentConfig) => void;
}
```

**Tier Feature Access:**

| Feature | FREE | BASIC (0.1 SOL) | PRO (1 SOL) |
|---------|------|-----------------|-------------|
| Base AI Engine | Yes | Yes | Yes |
| Strategy Sliders | No | **Yes** | Yes |
| Freeform Strategy Prompt | No | No | **Yes** |

---

## State Management

### Tournament Store

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
```

### Wallet Store

```typescript
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

---

## Real-Time Updates

### Socket.IO Events

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

---

## Registration Flow

```typescript
// frontend/src/app/register/[tournamentId]/page.tsx

/**
 * Registration Flow:
 *
 * 1. Connect wallet (Phantom)
 * 2. Display tier options:
 *    - FREE: Base agent, no cost
 *    - BASIC (0.1 SOL): Base + sliders only (no freeform prompt)
 *    - PRO (1 SOL): Base + sliders + freeform strategy prompt
 * 3. If BASIC: Configure agent (name, image, sliders only)
 * 4. If PRO: Configure agent (name, image, sliders, freeform prompt)
 * 5. Legal checkboxes:
 *    □ I have read and agree to the Terms of Service
 *    □ I confirm I am not a resident of, or physically located in, Restricted Jurisdictions
 * 6. Sign transaction (includes tier payment + registration)
 * 7. Confirmation with agent preview
 */
```

### Tier Selection UI

```typescript
interface TierOption {
  tier: "free" | "basic" | "pro";
  cost: number;  // SOL
  features: string[];
}

const TIER_OPTIONS: TierOption[] = [
  {
    tier: "free",
    cost: 0,
    features: [
      "Base AI poker engine",
      "Competes in tournaments",
      "No customization"
    ]
  },
  {
    tier: "basic",
    cost: 0.1,
    features: [
      "Base AI poker engine",
      "Strategy sliders (aggression, bluff frequency, tightness, position awareness)",
      "No freeform strategy prompt"
    ]
  },
  {
    tier: "pro",
    cost: 1.0,
    features: [
      "Base AI poker engine",
      "Strategy sliders",
      "Freeform strategy tuning prompt (cached for your agent)",
      "Maximum customization"
    ]
  }
];
```
