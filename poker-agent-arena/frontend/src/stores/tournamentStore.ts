/**
 * Tournament state store using Zustand
 */

import { create } from 'zustand';
import { TournamentDetail } from '@/lib/api';
import { TableState, SeatState } from '@/lib/socket';

interface MyAgent {
  tableId: string;
  seatPosition: number;
  stack: number;
  status: 'active' | 'folded' | 'all_in' | 'eliminated';
  holeCards?: string[];
}

interface TournamentState {
  // Current tournament
  currentTournament: TournamentDetail | null;

  // Tables (Map doesn't work well with Zustand, use Record instead)
  tables: Record<string, TableState>;

  // My agent info
  myAgent: MyAgent | null;

  // Current blind level
  blindLevel: {
    level: number;
    smallBlind: number;
    bigBlind: number;
    ante: number;
  } | null;

  // Eliminations log
  eliminations: {
    wallet: string;
    position: number;
    eliminatorWallet: string | null;
    timestamp: number;
  }[];

  // Actions
  setTournament: (tournament: TournamentDetail | null) => void;
  updateTableState: (tableId: string, state: TableState) => void;
  removeTable: (tableId: string) => void;
  setMyAgent: (agent: MyAgent | null) => void;
  updateMyAgent: (updates: Partial<MyAgent>) => void;
  setBlindLevel: (level: number, smallBlind: number, bigBlind: number, ante: number) => void;
  addElimination: (wallet: string, position: number, eliminatorWallet: string | null) => void;
  reset: () => void;
}

const initialState = {
  currentTournament: null,
  tables: {},
  myAgent: null,
  blindLevel: null,
  eliminations: [],
};

export const useTournamentStore = create<TournamentState>((set) => ({
  ...initialState,

  setTournament: (tournament) =>
    set({ currentTournament: tournament }),

  updateTableState: (tableId, state) =>
    set((prev) => ({
      tables: { ...prev.tables, [tableId]: state },
    })),

  removeTable: (tableId) =>
    set((prev) => {
      const { [tableId]: removed, ...rest } = prev.tables;
      return { tables: rest };
    }),

  setMyAgent: (agent) =>
    set({ myAgent: agent }),

  updateMyAgent: (updates) =>
    set((prev) => ({
      myAgent: prev.myAgent ? { ...prev.myAgent, ...updates } : null,
    })),

  setBlindLevel: (level, smallBlind, bigBlind, ante) =>
    set({
      blindLevel: { level, smallBlind, bigBlind, ante },
    }),

  addElimination: (wallet, position, eliminatorWallet) =>
    set((prev) => ({
      eliminations: [
        ...prev.eliminations,
        { wallet, position, eliminatorWallet, timestamp: Date.now() },
      ],
    })),

  reset: () => set(initialState),
}));

// Selectors
export const selectCurrentTable = (state: TournamentState, tableId: string | null) =>
  tableId ? state.tables[tableId] : null;

export const selectMySeat = (state: TournamentState): SeatState | null => {
  if (!state.myAgent) return null;
  const table = state.tables[state.myAgent.tableId];
  if (!table) return null;
  return table.seats.find((s) => s.position === state.myAgent!.seatPosition) ?? null;
};

export const selectActivePlayers = (state: TournamentState, tableId: string): number => {
  const table = state.tables[tableId];
  if (!table) return 0;
  return table.seats.filter((s) => s.status === 'active' || s.status === 'all_in').length;
};
