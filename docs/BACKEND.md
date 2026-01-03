# Backend Service Specification

This document covers the FastAPI backend, AI agent system, tournament engine, real-time system, security, and API reference.

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Configuration](#configuration)
3. [Core Tournament Engine](#core-tournament-engine)
4. [Hand Controller](#hand-controller)
5. [Poker Logic](#poker-logic)
6. [AI Agent System](#ai-agent-system)
7. [Tournament Engine Details](#tournament-engine-details)
8. [Real-Time System](#real-time-system)
9. [Security & Fairness](#security--fairness)
10. [API Reference](#api-reference)
11. [Example: Complete Hand Execution](#example-complete-hand-execution)

---

## API Overview

FastAPI backend handles tournament orchestration, AI decisions, and real-time updates.

---

## Configuration

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
    ADMIN_WALLET_PUBKEY: str  # BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m (mainnet)
    TREASURY_WALLET_PUBKEY: str  # CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm (mainnet)
    PROGRAM_ID: str  # 34MhwbaRczNA8Zt4H8rUwPV4o2MsAtYd8hQhNno3QaLN (devnet)

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

---

## Core Tournament Engine

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
    ante: int  # Paid by big blind only
    duration_minutes: int

@dataclass
class TournamentConfig:
    tournament_id: str
    max_players: int
    starting_stack: int
    table_size: int = 9  # 9-max
    blind_structure: list[BlindLevel]
    payout_structure: dict[int, int]  # rank -> points (admin-customized)

class TournamentManager:
    """
    Orchestrates the entire tournament lifecycle.

    Responsibilities:
    - Initialize tables and seat players
    - Manage blind level progression (with BB-only antes)
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
        2. Compute POINTS distribution (using admin-customized payout structure)
        3. Generate results hash
        4. Submit finalization transaction
        5. Distribute POINTS SPL tokens
        """
        ...
```

---

## Hand Controller

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
    ante_amount: int  # Current level's ante (paid by BB only)

class HandController:
    """
    Manages a single poker hand.

    Texas Hold'em No-Limit rules:
    - 2 hole cards per player
    - 5 community cards (flop/turn/river)
    - Best 5-card hand wins
    - All-in and side pot support
    - BB-only ante collection
    """

    async def deal(self, players: list[Player], deck: Deck, blind_level: BlindLevel) -> HandState:
        """
        Deal hole cards to all active players.
        Post blinds and ante (BB pays ante).
        """
        ...

    async def post_blinds_and_ante(self, state: HandState, blind_level: BlindLevel) -> HandState:
        """
        Post small blind, big blind, and ante.

        Ante is paid by big blind only:
        - SB posts small_blind
        - BB posts big_blind + ante
        """
        sb_player = self._get_small_blind_player(state)
        bb_player = self._get_big_blind_player(state)

        # Post small blind
        sb_amount = min(blind_level.small_blind, sb_player.stack)
        sb_player.stack -= sb_amount
        sb_player.current_bet = sb_amount
        state.pot += sb_amount

        # Post big blind + ante (BB pays both)
        bb_amount = min(blind_level.big_blind, bb_player.stack)
        ante_amount = min(blind_level.ante, bb_player.stack - bb_amount)
        total_bb = bb_amount + ante_amount

        bb_player.stack -= total_bb
        bb_player.current_bet = bb_amount  # Only BB counts toward bet
        state.pot += total_bb
        state.ante_amount = ante_amount

        return state

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

---

## Poker Logic

### Hand Evaluator

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

### Deck

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

## AI Agent System

### Base Agent Engine

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

### Custom Agent Configuration

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
    - BASIC: Sliders only (no freeform text)
    - PRO: Sliders + unlimited freeform text
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
        # BASIC tier: sliders only, no freeform text
        return slider_prompt

    # PRO tier: sliders + freeform text
    user_prompt = f"""
## CUSTOM INSTRUCTIONS FROM OWNER

{custom_text}
"""

    return slider_prompt + user_prompt
```

### Decision Engine

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
    Makes poker decisions using Claude (claude-sonnet-4-5-20250929).

    Key optimizations:
    - System prompt caching (85% token savings)
    - Compressed game state format
    - Parallel table processing
    - Budget tracking per tournament (input + output tokens)
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
        if not await self.budget.can_make_call(agent_config.tournament_id):
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

        # Track usage (both input and output tokens)
        await self.budget.record_usage(
            tournament_id=agent_config.tournament_id,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_hit=response.usage.cache_read_input_tokens > 0,
        )

        return decision

    def _format_game_state(self, state: GameState) -> str:
        """
        Format game state for Claude in compressed format.

        Example output:
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
        6. [BB] Player_E: 4,500 (checked) [posted ante: 25]

        Action History This Hand:
        - Preflop: BB posts 200 + 25 ante, UTG fold, MP raise 100, CO call, BTN call, SB fold, BB call
        - Flop: BB check, MP bet 150, CO call

        Your Action?
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

---

## Tournament Engine Details

### Blind Structures

```python
# backend/core/tournament/blinds.py

BLIND_TEMPLATES = {
    "turbo": [
        BlindLevel(1, 25, 50, 0, 6),      # No ante
        BlindLevel(2, 50, 100, 0, 6),
        BlindLevel(3, 75, 150, 0, 6),
        BlindLevel(4, 100, 200, 25, 6),   # BB pays 200+25=225
        BlindLevel(5, 150, 300, 25, 6),   # BB pays 300+25=325
        BlindLevel(6, 200, 400, 50, 6),   # BB pays 400+50=450
        BlindLevel(7, 300, 600, 75, 6),   # BB pays 600+75=675
        BlindLevel(8, 400, 800, 100, 6),  # BB pays 800+100=900
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

### Table Balancing Algorithm

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

### Payout Calculator

```python
# backend/core/tournament/payouts.py

class PayoutCalculator:
    """
    Calculates POINTS distribution based on admin-customized payout structure.

    Payout structures are configured per tournament by admin.
    """

    def calculate(
        self,
        payout_structure: dict[int, int],  # rank -> points (admin-defined)
        final_rankings: list[tuple[str, int]],  # (wallet, rank)
    ) -> list[PointsAward]:
        """
        Calculate POINTS for each player based on final rank.

        Example admin-customized payout structure (27 players):
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

## Real-Time System

### WebSocket Events

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

### Event Payloads

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
    ante: number;  // Paid by BB only
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
  action: "fold" | "check" | "call" | "raise" | "post_blind" | "post_ante";
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

## Security & Fairness

### Provably Fair Randomness

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

### Agent Prompt Integrity

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

### Backend Security

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
    - WebSocket connections: 3 concurrent per wallet
    - AI API calls: 1000/minute global (Anthropic tier dependent)
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

### Budget Protection

```python
# backend/core/ai/budget.py

class BudgetTracker:
    """
    Prevents runaway API costs.

    Budget per tournament = 3x expected cost (from devnet tests)

    Example (27 player tournament):
    - Expected: ~$7.20
    - Budget cap: ~$21.60

    Tracks both input and output tokens separately.
    """

    # Claude claude-sonnet-4-5-20250929 pricing
    INPUT_COST_PER_1K = 0.003   # $0.003 per 1K input tokens
    OUTPUT_COST_PER_1K = 0.015  # $0.015 per 1K output tokens

    def __init__(self, redis):
        self.redis = redis

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

    async def record_usage(
        self,
        tournament_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool = False,
    ):
        """Record API usage with proper cost calculation."""
        input_cost = (input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost

        await self.redis.incrbyfloat(f"spent:{tournament_id}", total_cost)
        await self.redis.incr(f"decisions:{tournament_id}")
        await self.redis.incrby(f"tokens_input:{tournament_id}", input_tokens)
        await self.redis.incrby(f"tokens_output:{tournament_id}", output_tokens)

        if cache_hit:
            await self.redis.incr(f"cache_hits:{tournament_id}")
```

---

## API Reference

### REST Endpoints

```yaml
# Admin Endpoints (require admin wallet signature)

POST /api/admin/tournaments
  Description: Create a new tournament
  Body:
    maxPlayers: number (27 or 54)
    startingStack: number
    startsAt: ISO8601 datetime
    blindStructure: string (template name) or BlindLevel[]
    payoutStructure: {rank: points}[]  # Admin-customized
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
    agentSliders?: {aggression, bluffFrequency, tightness, positionAwareness}  # BASIC + PRO only
    customPrompt?: string  # PRO only (unlimited)
  Response: Registration

PUT /api/agent
  Description: Update agent configuration (before tournament starts)
  Body: Same as register (partial)
  Response: AgentConfig

GET /api/me
  Description: Get current user's profile
  Response: {wallet, stats, activeRegistrations}
```

### WebSocket Events

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

## Example: Complete Hand Execution

### Setup

```
Tournament: Weekly Showdown #42
Players: 27 (started), 18 remaining
Level: 4 (100/200, 25 ante - BB only)
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

### Execution Trace

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

[T+10ms] POST BLINDS & ANTE (BB only)
├── SB (Seat 7): 100
├── BB (Seat 8): 200 + 25 ante = 225
└── Pot: 325

───────────────────────────────────────────────────────────────────────────
PREFLOP BETTING ROUND
───────────────────────────────────────────────────────────────────────────

[T+100ms] ACTION ON: Seat 0 (UTG)
├── Claude API Call
│   ├── Input tokens: 1,847 (1,500 cached + 347 dynamic)
│   ├── Output tokens: 23
│   ├── Cache status: HIT (85% discount)
│   └── Response: {"action": "fold"}
├── Decision time: 1.2s
└── Pot: 325

[T+1.3s] ACTION ON: Seat 1 (UTG+1)
├── Claude API Call: {"action": "fold"}
├── Decision time: 0.9s
└── Pot: 325

[T+2.2s] ACTION ON: Seat 2 (MP)
├── Claude API Call: {"action": "raise", "amount": 500}
│   └── Reasoning: "AQs is premium in MP, standard 2.5x open"
├── Decision time: 1.4s
└── Pot: 825

... [continues through all betting rounds] ...

═══════════════════════════════════════════════════════════════════════════
HAND #127 SUMMARY
═══════════════════════════════════════════════════════════════════════════

Duration: 25.5 seconds
API Calls: 14 decisions
Total Input Tokens: ~25,800
Total Output Tokens: ~700
Estimated Cost: $0.12 (with 85% caching on input)
Winner: Your agent (Seat 4 / Player_E)
Pot Size: 19,300 chips

Moving to Hand #128...
```
