/**
 * Tests for useTournament hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useTournaments, useTournament, useTournamentResults } from '@/hooks/useTournament';

// Mock api module
jest.mock('@/lib/api', () => ({
  api: {
    tournaments: {
      list: jest.fn(),
      get: jest.fn(),
      getResults: jest.fn(),
    },
  },
  ApiError: class ApiError extends Error {
    constructor(public status: number, public detail: string) {
      super(detail);
      this.name = 'ApiError';
    }
  },
}));

import { api, ApiError } from '@/lib/api';

beforeEach(() => {
  jest.clearAllMocks();
});

describe('useTournaments', () => {
  const mockTournaments = [
    {
      id: 'tournament-1',
      on_chain_id: 1,
      status: 'registration',
      max_players: 27,
      registered_players: 10,
      starting_stack: 10000,
      starts_at: '2024-01-01T12:00:00Z',
      blind_structure_name: 'standard',
      total_points_prize: 20000,
    },
    {
      id: 'tournament-2',
      on_chain_id: 2,
      status: 'in_progress',
      max_players: 54,
      registered_players: 54,
      starting_stack: 15000,
      starts_at: '2024-01-02T12:00:00Z',
      blind_structure_name: 'turbo',
      total_points_prize: 50000,
    },
  ];

  it('should fetch tournaments on mount', async () => {
    (api.tournaments.list as jest.Mock).mockResolvedValue(mockTournaments);

    const { result } = renderHook(() => useTournaments());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.tournaments).toEqual(mockTournaments);
    expect(result.current.error).toBeNull();
    expect(api.tournaments.list).toHaveBeenCalledWith('all', 20, 0);
  });

  it('should not fetch when autoFetch is false', async () => {
    const { result } = renderHook(() => useTournaments({ autoFetch: false }));

    expect(result.current.loading).toBe(false);
    expect(result.current.tournaments).toEqual([]);
    expect(api.tournaments.list).not.toHaveBeenCalled();
  });

  it('should handle status filter', async () => {
    (api.tournaments.list as jest.Mock).mockResolvedValue([mockTournaments[0]]);

    const { result } = renderHook(() => useTournaments({ status: 'upcoming' }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.tournaments.list).toHaveBeenCalledWith('upcoming', 20, 0);
  });

  it('should handle pagination', async () => {
    (api.tournaments.list as jest.Mock).mockResolvedValue([]);

    const { result } = renderHook(() =>
      useTournaments({ limit: 10, offset: 20 })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.tournaments.list).toHaveBeenCalledWith('all', 10, 20);
  });

  it('should handle API error', async () => {
    (api.tournaments.list as jest.Mock).mockRejectedValue(
      new ApiError(500, 'Server error')
    );

    const { result } = renderHook(() => useTournaments());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Server error');
    expect(result.current.tournaments).toEqual([]);
  });

  it('should refetch when refetch is called', async () => {
    (api.tournaments.list as jest.Mock).mockResolvedValue(mockTournaments);

    const { result } = renderHook(() => useTournaments());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.tournaments.list).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refetch();
    });

    expect(api.tournaments.list).toHaveBeenCalledTimes(2);
  });
});

describe('useTournament', () => {
  const mockTournamentDetail = {
    id: 'tournament-1',
    on_chain_id: 1,
    status: 'registration',
    max_players: 27,
    registered_players: 10,
    starting_stack: 10000,
    starts_at: '2024-01-01T12:00:00Z',
    blind_structure_name: 'standard',
    total_points_prize: 20000,
    blind_structure: {
      name: 'standard',
      levels: [
        { level: 1, small_blind: 25, big_blind: 50, ante: 0, duration_minutes: 10 },
      ],
    },
    payout_structure: [
      { rank: 1, points: 10000 },
      { rank: 2, points: 5000 },
    ],
    created_at: '2024-01-01T00:00:00Z',
    registration_opens_at: '2024-01-01T00:00:00Z',
    completed_at: null,
    winner_wallet: null,
    results_hash: null,
    user_registered: false,
    user_tier: null,
    user_agent_name: null,
  };

  it('should fetch tournament detail', async () => {
    (api.tournaments.get as jest.Mock).mockResolvedValue(mockTournamentDetail);

    const { result } = renderHook(() => useTournament('tournament-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.tournament).toEqual(mockTournamentDetail);
    expect(api.tournaments.get).toHaveBeenCalledWith('tournament-1');
  });

  it('should not fetch when id is null', async () => {
    const { result } = renderHook(() => useTournament(null));

    expect(result.current.loading).toBe(false);
    expect(result.current.tournament).toBeNull();
    expect(api.tournaments.get).not.toHaveBeenCalled();
  });

  it('should not fetch when autoFetch is false', async () => {
    const { result } = renderHook(() =>
      useTournament('tournament-1', { autoFetch: false })
    );

    expect(result.current.loading).toBe(false);
    expect(api.tournaments.get).not.toHaveBeenCalled();
  });

  it('should handle error', async () => {
    (api.tournaments.get as jest.Mock).mockRejectedValue(
      new ApiError(404, 'Tournament not found')
    );

    const { result } = renderHook(() => useTournament('invalid-id'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Tournament not found');
    expect(result.current.tournament).toBeNull();
  });
});

describe('useTournamentResults', () => {
  const mockResults = {
    tournament_id: 'tournament-1',
    status: 'completed',
    completed_at: '2024-01-01T14:00:00Z',
    results_hash: 'abc123',
    results: [
      {
        rank: 1,
        wallet: 'winner-wallet',
        agent_name: 'WinnerAgent',
        points_awarded: 10000,
        hands_played: 150,
        eliminations: 5,
      },
      {
        rank: 2,
        wallet: 'second-wallet',
        agent_name: 'SecondAgent',
        points_awarded: 5000,
        hands_played: 145,
        eliminations: 3,
      },
    ],
  };

  it('should fetch tournament results', async () => {
    (api.tournaments.getResults as jest.Mock).mockResolvedValue(mockResults);

    const { result } = renderHook(() => useTournamentResults('tournament-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.results).toEqual(mockResults);
    expect(api.tournaments.getResults).toHaveBeenCalledWith('tournament-1');
  });

  it('should not fetch when id is null', async () => {
    const { result } = renderHook(() => useTournamentResults(null));

    expect(result.current.loading).toBe(false);
    expect(result.current.results).toBeNull();
    expect(api.tournaments.getResults).not.toHaveBeenCalled();
  });

  it('should handle error', async () => {
    (api.tournaments.getResults as jest.Mock).mockRejectedValue(
      new ApiError(500, 'Failed to fetch results')
    );

    const { result } = renderHook(() => useTournamentResults('tournament-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch results');
  });
});
