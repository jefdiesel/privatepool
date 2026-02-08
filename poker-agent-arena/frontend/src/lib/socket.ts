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

export interface SettingsConfirmedEvent {
  tournament_id: string;
  wallet: string;
  aggression: number;
  tightness: number;
  message: string;
}

export interface SettingsAppliedEvent {
  tournament_id: string;
  wallet: string;
  aggression: number;
  tightness: number;
  message: string;
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

  // Live settings events
  onSettingsConfirmed?: (event: SettingsConfirmedEvent) => void;
  onSettingsApplied?: (event: SettingsAppliedEvent) => void;
}

interface ReconnectionState {
  currentTournamentId: string | null;
  subscribedTables: Set<string>;
  lastEventTimestamp: number;
}

class SocketClient {
  private socket: Socket | null = null;
  private callbacks: SocketEventCallbacks = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectionState: ReconnectionState = {
    currentTournamentId: null,
    subscribedTables: new Set(),
    lastEventTimestamp: 0,
  };
  private isReconnecting = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

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
      reconnectionDelayMax: 10000,
      randomizationFactor: 0.5,
      timeout: 20000,
    });

    this.setupEventListeners();
  }

  private handleReconnection() {
    if (!this.socket?.connected) return;

    console.log('Socket reconnected, restoring state...');
    this.isReconnecting = false;

    // Rejoin tournament room if we were in one
    if (this.reconnectionState.currentTournamentId) {
      this.joinTournament(this.reconnectionState.currentTournamentId);
    }

    // Resubscribe to tables
    this.reconnectionState.subscribedTables.forEach((tableId) => {
      this.subscribeTable(tableId);
    });

    // Request state sync for missed events
    if (this.reconnectionState.currentTournamentId) {
      this.socket.emit('request_state_sync', {
        tournament_id: this.reconnectionState.currentTournamentId,
        last_event_timestamp: this.reconnectionState.lastEventTimestamp,
      });
    }
  }

  private scheduleReconnect(delay: number) {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      if (!this.socket?.connected) {
        console.log(`Attempting manual reconnection...`);
        this.socket?.connect();
      }
    }, delay);
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('Socket connected');
      this.reconnectAttempts = 0;

      // Handle reconnection state restoration
      if (this.isReconnecting) {
        this.handleReconnection();
      }

      this.callbacks.onConnect?.();
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      this.isReconnecting = true;

      // Handle specific disconnect reasons
      if (reason === 'io server disconnect') {
        // Server initiated disconnect - may need to re-authenticate
        console.log('Server disconnected, attempting reconnect...');
        this.scheduleReconnect(1000);
      } else if (reason === 'transport close' || reason === 'transport error') {
        // Network issue - will auto-reconnect
        console.log('Network issue, auto-reconnecting...');
      }

      this.callbacks.onDisconnect?.();
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error.message);
      this.reconnectAttempts++;

      // Exponential backoff for connection errors
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Connection failed, retry in ${delay}ms (attempt ${this.reconnectAttempts})`);

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.callbacks.onError?.({
          code: 'max_reconnect_attempts',
          message: 'Unable to connect to server after multiple attempts',
        });
      }
    });

    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
      this.callbacks.onError?.(error);
    });

    this.socket.on('authenticated', (data) => {
      console.log('Socket authenticated');
      this.callbacks.onAuthenticated?.(data);
    });

    // State sync response handler
    this.socket.on('state_sync', (data) => {
      console.log('Received state sync:', data);
      // Update local state with synced data
      if (data.table_state) {
        this.callbacks.onTableState?.(data.table_state);
      }
      if (data.tournament_state) {
        // Handle tournament state update
      }
    });

    // Tournament events
    this.socket.on('tournament:started', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onTournamentStarted?.(data);
    });

    this.socket.on('tournament:level_up', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onLevelUp?.(data);
    });

    this.socket.on('tournament:completed', (data) => {
      this.updateEventTimestamp();
      // Clear reconnection state when tournament ends
      this.reconnectionState.currentTournamentId = null;
      this.reconnectionState.subscribedTables.clear();
      this.callbacks.onTournamentCompleted?.(data);
    });

    this.socket.on('player:eliminated', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onPlayerEliminated?.(data);
    });

    this.socket.on('player:moved', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onPlayerMoved?.(data);
    });

    // Table events
    this.socket.on('table:state', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onTableState?.(data);
    });

    this.socket.on('hand:new', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onHandNew?.(data);
    });

    this.socket.on('hand:deal', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onHandDeal?.(data);
    });

    this.socket.on('hand:community', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onHandCommunity?.(data);
    });

    this.socket.on('hand:action', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onHandAction?.(data);
    });

    this.socket.on('hand:showdown', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onHandShowdown?.(data);
    });

    this.socket.on('decision:start', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onDecisionStart?.(data);
    });

    // Live settings events
    this.socket.on('settings:confirmed', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onSettingsConfirmed?.(data);
    });

    this.socket.on('settings:applied', (data) => {
      this.updateEventTimestamp();
      this.callbacks.onSettingsApplied?.(data);
    });
  }

  private updateEventTimestamp() {
    this.reconnectionState.lastEventTimestamp = Date.now();
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Clear reconnection state
    this.reconnectionState = {
      currentTournamentId: null,
      subscribedTables: new Set(),
      lastEventTimestamp: 0,
    };
    this.isReconnecting = false;
    this.reconnectAttempts = 0;

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
    this.reconnectionState.currentTournamentId = tournamentId;
    this.socket?.emit('join_tournament', { tournament_id: tournamentId });
  }

  leaveTournament(tournamentId: string) {
    if (this.reconnectionState.currentTournamentId === tournamentId) {
      this.reconnectionState.currentTournamentId = null;
      this.reconnectionState.subscribedTables.clear();
    }
    this.socket?.emit('leave_tournament', { tournament_id: tournamentId });
  }

  subscribeTable(tableId: string) {
    this.reconnectionState.subscribedTables.add(tableId);
    this.socket?.emit('subscribe_table', { table_id: tableId });
  }

  unsubscribeTable(tableId: string) {
    this.reconnectionState.subscribedTables.delete(tableId);
    this.socket?.emit('unsubscribe_table', { table_id: tableId });
  }

  // Request full state sync after reconnection
  requestStateSync() {
    if (this.reconnectionState.currentTournamentId) {
      this.socket?.emit('request_state_sync', {
        tournament_id: this.reconnectionState.currentTournamentId,
        last_event_timestamp: this.reconnectionState.lastEventTimestamp,
      });
    }
  }

  // Update callbacks
  setCallbacks(callbacks: SocketEventCallbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }
}

// Singleton instance
export const socketClient = new SocketClient();
