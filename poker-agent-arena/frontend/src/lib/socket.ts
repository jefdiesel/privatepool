/**
 * Socket.IO client for real-time tournament updates
 */

import { io, Socket } from 'socket.io-client';
import { getSessionToken } from './api';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8000';

// Socket.IO event types
export interface TableState {
  table_id: string;
  seats: SeatState[];
  community_cards: string[];
  pot: number;
  current_bet: number;
  action_on: number | null;
  betting_round: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
}

export interface SeatState {
  position: number;
  wallet: string | null;
  agent_name: string | null;
  agent_image: string | null;
  stack: number;
  current_bet: number;
  status: 'active' | 'folded' | 'all_in' | 'eliminated' | 'empty';
  hole_cards?: string[];
}

export interface TournamentStartedEvent {
  tournament_id: string;
  table_assignments: {
    wallet: string;
    table_id: string;
    seat: number;
  }[];
}

export interface LevelUpEvent {
  tournament_id: string;
  level: number;
  small_blind: number;
  big_blind: number;
  ante: number;
}

export interface TournamentCompletedEvent {
  tournament_id: string;
  results: {
    rank: number;
    wallet: string;
    agent_name: string;
    points_awarded: number;
  }[];
}

export interface PlayerEliminatedEvent {
  tournament_id: string;
  wallet: string;
  position: number;
  eliminator_wallet: string | null;
}

export interface PlayerMovedEvent {
  tournament_id: string;
  wallet: string;
  from_table_id: string;
  to_table_id: string;
  new_seat: number;
}

export interface HandNewEvent {
  table_id: string;
  hand_number: number;
  button_seat: number;
  player_stacks: Record<string, number>;
}

export interface HandDealEvent {
  table_id: string;
  hole_cards: string[];
}

export interface HandCommunityEvent {
  table_id: string;
  betting_round: string;
  cards: string[];
  pot: number;
}

export interface HandActionEvent {
  table_id: string;
  wallet: string;
  action: 'fold' | 'check' | 'call' | 'raise';
  amount: number | null;
  pot: number;
  stack_remaining: number;
}

export interface HandShowdownEvent {
  table_id: string;
  showdown: {
    wallet: string;
    hole_cards: string[];
    hand_rank: string;
  }[];
  winners: {
    wallet: string;
    amount: number;
    hand_rank: string;
  }[];
  pot_distribution: Record<string, number>;
}

export interface DecisionStartEvent {
  table_id: string;
  wallet: string;
  timeout_seconds: number;
  to_call: number;
  min_raise: number;
  pot: number;
}

// Event callback types
export interface SocketEventCallbacks {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: { code: string; message: string }) => void;
  onAuthenticated?: (data: { wallet: string; is_admin?: boolean }) => void;

  // Tournament events
  onTournamentStarted?: (event: TournamentStartedEvent) => void;
  onLevelUp?: (event: LevelUpEvent) => void;
  onTournamentCompleted?: (event: TournamentCompletedEvent) => void;
  onPlayerEliminated?: (event: PlayerEliminatedEvent) => void;
  onPlayerMoved?: (event: PlayerMovedEvent) => void;

  // Table events
  onTableState?: (state: TableState) => void;
  onHandNew?: (event: HandNewEvent) => void;
  onHandDeal?: (event: HandDealEvent) => void;
  onHandCommunity?: (event: HandCommunityEvent) => void;
  onHandAction?: (event: HandActionEvent) => void;
  onHandShowdown?: (event: HandShowdownEvent) => void;
  onDecisionStart?: (event: DecisionStartEvent) => void;
}

class SocketClient {
  private socket: Socket | null = null;
  private callbacks: SocketEventCallbacks = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(callbacks: SocketEventCallbacks = {}) {
    this.callbacks = callbacks;

    const token = getSessionToken();
    if (!token) {
      console.error('Cannot connect: No session token');
      return;
    }

    this.socket = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('Socket connected');
      this.reconnectAttempts = 0;
      this.callbacks.onConnect?.();
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      this.callbacks.onDisconnect?.();
    });

    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
      this.callbacks.onError?.(error);
    });

    this.socket.on('authenticated', (data) => {
      console.log('Socket authenticated');
      this.callbacks.onAuthenticated?.(data);
    });

    // Tournament events
    this.socket.on('tournament:started', (data) => {
      this.callbacks.onTournamentStarted?.(data);
    });

    this.socket.on('tournament:level_up', (data) => {
      this.callbacks.onLevelUp?.(data);
    });

    this.socket.on('tournament:completed', (data) => {
      this.callbacks.onTournamentCompleted?.(data);
    });

    this.socket.on('player:eliminated', (data) => {
      this.callbacks.onPlayerEliminated?.(data);
    });

    this.socket.on('player:moved', (data) => {
      this.callbacks.onPlayerMoved?.(data);
    });

    // Table events
    this.socket.on('table:state', (data) => {
      this.callbacks.onTableState?.(data);
    });

    this.socket.on('hand:new', (data) => {
      this.callbacks.onHandNew?.(data);
    });

    this.socket.on('hand:deal', (data) => {
      this.callbacks.onHandDeal?.(data);
    });

    this.socket.on('hand:community', (data) => {
      this.callbacks.onHandCommunity?.(data);
    });

    this.socket.on('hand:action', (data) => {
      this.callbacks.onHandAction?.(data);
    });

    this.socket.on('hand:showdown', (data) => {
      this.callbacks.onHandShowdown?.(data);
    });

    this.socket.on('decision:start', (data) => {
      this.callbacks.onDecisionStart?.(data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  // Room management
  joinTournament(tournamentId: string) {
    this.socket?.emit('join_tournament', { tournament_id: tournamentId });
  }

  leaveTournament(tournamentId: string) {
    this.socket?.emit('leave_tournament', { tournament_id: tournamentId });
  }

  subscribeTable(tableId: string) {
    this.socket?.emit('subscribe_table', { table_id: tableId });
  }

  unsubscribeTable(tableId: string) {
    this.socket?.emit('unsubscribe_table', { table_id: tableId });
  }

  // Update callbacks
  setCallbacks(callbacks: SocketEventCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }
}

// Singleton instance
export const socketClient = new SocketClient();
