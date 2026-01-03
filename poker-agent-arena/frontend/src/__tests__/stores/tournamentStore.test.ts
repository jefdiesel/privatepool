/**
 * Tests for Tournament Store (Zustand)
 */

import { act } from '@testing-library/react';
import {
  useTournamentStore,
  selectCurrentTable,
  selectMySeat,
  selectActivePlayers,
} from '@/stores/tournamentStore';

// Reset store before each test
beforeEach(() => {
  useTournamentStore.getState().reset();
});

describe('TournamentStore', () => {
  describe('setTournament', () => {
    it('should set current tournament', () => {
      const tournament = {
        id: 'tournament-1',
        on_chain_id: 1,
        status: 'registration' as const,
        max_players: 27,
        registered_players: 10,
        starting_stack: 10000,
        starts_at: '2024-01-01T12:00:00Z',
        blind_structure_name: 'standard',
        total_points_prize: 20000,
        blind_structure: { name: 'standard', levels: [] },
        payout_structure: [],
        created_at: '2024-01-01T00:00:00Z',
        registration_opens_at: '2024-01-01T00:00:00Z',
        completed_at: null,
        winner_wallet: null,
        results_hash: null,
        user_registered: false,
        user_tier: null,
        user_agent_name: null,
      };

      act(() => {
        useTournamentStore.getState().setTournament(tournament);
      });

      expect(useTournamentStore.getState().currentTournament).toEqual(tournament);
    });

    it('should clear tournament when set to null', () => {
      act(() => {
        useTournamentStore.getState().setTournament(null);
      });

      expect(useTournamentStore.getState().currentTournament).toBeNull();
    });
  });

  describe('updateTableState', () => {
    it('should add a new table state', () => {
      const tableState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [],
        pot: 0,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', tableState);
      });

      expect(useTournamentStore.getState().tables['table-1']).toEqual(tableState);
    });

    it('should update existing table state', () => {
      const initialState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [],
        pot: 0,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      const updatedState = {
        ...initialState,
        pot: 500,
        betting_round: 'flop' as const,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', initialState);
        useTournamentStore.getState().updateTableState('table-1', updatedState);
      });

      expect(useTournamentStore.getState().tables['table-1'].pot).toBe(500);
      expect(useTournamentStore.getState().tables['table-1'].betting_round).toBe('flop');
    });
  });

  describe('removeTable', () => {
    it('should remove a table', () => {
      const tableState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [],
        pot: 0,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', tableState);
        useTournamentStore.getState().removeTable('table-1');
      });

      expect(useTournamentStore.getState().tables['table-1']).toBeUndefined();
    });
  });

  describe('setMyAgent', () => {
    it('should set my agent info', () => {
      const agent = {
        tableId: 'table-1',
        seatPosition: 3,
        stack: 10000,
        status: 'active' as const,
        holeCards: ['Ah', 'Kh'],
      };

      act(() => {
        useTournamentStore.getState().setMyAgent(agent);
      });

      expect(useTournamentStore.getState().myAgent).toEqual(agent);
    });

    it('should clear my agent when set to null', () => {
      act(() => {
        useTournamentStore.getState().setMyAgent(null);
      });

      expect(useTournamentStore.getState().myAgent).toBeNull();
    });
  });

  describe('updateMyAgent', () => {
    it('should update agent partial properties', () => {
      const agent = {
        tableId: 'table-1',
        seatPosition: 3,
        stack: 10000,
        status: 'active' as const,
      };

      act(() => {
        useTournamentStore.getState().setMyAgent(agent);
        useTournamentStore.getState().updateMyAgent({ stack: 9500, status: 'folded' });
      });

      expect(useTournamentStore.getState().myAgent?.stack).toBe(9500);
      expect(useTournamentStore.getState().myAgent?.status).toBe('folded');
    });

    it('should not update when myAgent is null', () => {
      act(() => {
        useTournamentStore.getState().setMyAgent(null);
        useTournamentStore.getState().updateMyAgent({ stack: 5000 });
      });

      expect(useTournamentStore.getState().myAgent).toBeNull();
    });
  });

  describe('setBlindLevel', () => {
    it('should set blind level', () => {
      act(() => {
        useTournamentStore.getState().setBlindLevel(3, 100, 200, 25);
      });

      const blindLevel = useTournamentStore.getState().blindLevel;
      expect(blindLevel).toEqual({
        level: 3,
        smallBlind: 100,
        bigBlind: 200,
        ante: 25,
      });
    });
  });

  describe('addElimination', () => {
    it('should add elimination record', () => {
      const beforeCount = useTournamentStore.getState().eliminations.length;

      act(() => {
        useTournamentStore.getState().addElimination('player1', 5, 'player2');
      });

      const eliminations = useTournamentStore.getState().eliminations;
      expect(eliminations.length).toBe(beforeCount + 1);
      expect(eliminations[0].wallet).toBe('player1');
      expect(eliminations[0].position).toBe(5);
      expect(eliminations[0].eliminatorWallet).toBe('player2');
      expect(eliminations[0].timestamp).toBeDefined();
    });

    it('should support null eliminator (blindout)', () => {
      act(() => {
        useTournamentStore.getState().addElimination('player3', 8, null);
      });

      const eliminations = useTournamentStore.getState().eliminations;
      expect(eliminations[0].eliminatorWallet).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      act(() => {
        useTournamentStore.getState().setMyAgent({
          tableId: 'table-1',
          seatPosition: 1,
          stack: 5000,
          status: 'active',
        });
        useTournamentStore.getState().addElimination('player1', 5, 'player2');
        useTournamentStore.getState().reset();
      });

      const state = useTournamentStore.getState();
      expect(state.currentTournament).toBeNull();
      expect(state.tables).toEqual({});
      expect(state.myAgent).toBeNull();
      expect(state.blindLevel).toBeNull();
      expect(state.eliminations).toEqual([]);
    });
  });
});

describe('Selectors', () => {
  describe('selectCurrentTable', () => {
    it('should return table by id', () => {
      const tableState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [],
        pot: 100,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', tableState);
      });

      const state = useTournamentStore.getState();
      const result = selectCurrentTable(state, 'table-1');
      expect(result).toEqual(tableState);
    });

    it('should return null for null tableId', () => {
      const state = useTournamentStore.getState();
      const result = selectCurrentTable(state, null);
      expect(result).toBeNull();
    });
  });

  describe('selectMySeat', () => {
    it('should return my seat from table', () => {
      const seat = {
        position: 3,
        wallet: 'my-wallet',
        agent_name: 'MyAgent',
        agent_image: null,
        stack: 10000,
        current_bet: 0,
        status: 'active' as const,
        hole_cards: null,
      };

      const tableState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [seat],
        pot: 0,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', tableState);
        useTournamentStore.getState().setMyAgent({
          tableId: 'table-1',
          seatPosition: 3,
          stack: 10000,
          status: 'active',
        });
      });

      const state = useTournamentStore.getState();
      const result = selectMySeat(state);
      expect(result).toEqual(seat);
    });

    it('should return null when no agent', () => {
      const state = useTournamentStore.getState();
      const result = selectMySeat(state);
      expect(result).toBeNull();
    });
  });

  describe('selectActivePlayers', () => {
    it('should count active and all-in players', () => {
      const tableState = {
        table_id: 'table-1',
        tournament_id: 'tournament-1',
        seats: [
          { position: 0, status: 'active' as const, wallet: 'p1', agent_name: 'A1', agent_image: null, stack: 1000, current_bet: 0, hole_cards: null },
          { position: 1, status: 'folded' as const, wallet: 'p2', agent_name: 'A2', agent_image: null, stack: 1000, current_bet: 0, hole_cards: null },
          { position: 2, status: 'all_in' as const, wallet: 'p3', agent_name: 'A3', agent_image: null, stack: 0, current_bet: 1000, hole_cards: null },
          { position: 3, status: 'eliminated' as const, wallet: 'p4', agent_name: 'A4', agent_image: null, stack: 0, current_bet: 0, hole_cards: null },
          { position: 4, status: 'active' as const, wallet: 'p5', agent_name: 'A5', agent_image: null, stack: 1000, current_bet: 0, hole_cards: null },
        ],
        pot: 0,
        community_cards: [],
        betting_round: 'preflop' as const,
        button_position: 0,
        current_position: null,
      };

      act(() => {
        useTournamentStore.getState().updateTableState('table-1', tableState);
      });

      const state = useTournamentStore.getState();
      const result = selectActivePlayers(state, 'table-1');
      expect(result).toBe(3); // 2 active + 1 all_in
    });

    it('should return 0 for non-existent table', () => {
      const state = useTournamentStore.getState();
      const result = selectActivePlayers(state, 'non-existent');
      expect(result).toBe(0);
    });
  });
});
