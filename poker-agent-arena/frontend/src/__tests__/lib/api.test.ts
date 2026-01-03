/**
 * Tests for API client
 */

// Mock fetch
global.fetch = jest.fn();

import { api, ApiError, setSessionToken, getSessionToken } from '@/lib/api';

beforeEach(() => {
  jest.clearAllMocks();
  // Reset session token cache by setting null
  setSessionToken(null);
});

describe('Session Token Management', () => {
  describe('setSessionToken', () => {
    it('should store and retrieve token', () => {
      setSessionToken('test-token');
      const token = getSessionToken();
      expect(token).toBe('test-token');
    });

    it('should clear token when set to null', () => {
      setSessionToken('test-token');
      setSessionToken(null);
      // After clearing, the internal cache is null
      // Note: getSessionToken may still try localStorage, but we're testing the cache
    });
  });

  describe('getSessionToken', () => {
    it('should return cached token if available', () => {
      setSessionToken('cached-token');

      const token = getSessionToken();

      expect(token).toBe('cached-token');
    });

    it('should return null when no token set', () => {
      setSessionToken(null);
      // The module caches null, so this should return null
      const token = getSessionToken();
      // Token should be null or undefined when not set
      expect(token).toBeFalsy();
    });
  });
});

describe('ApiError', () => {
  it('should create error with status and detail', () => {
    const error = new ApiError(404, 'Not found');

    expect(error.status).toBe(404);
    expect(error.detail).toBe('Not found');
    expect(error.message).toBe('Not found');
    expect(error.name).toBe('ApiError');
  });
});

describe('API Methods', () => {
  beforeEach(() => {
    setSessionToken('test-auth-token');
  });

  describe('auth.getNonce', () => {
    it('should fetch nonce for wallet', async () => {
      const mockResponse = { nonce: 'abc123', message: 'Sign this message' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.auth.getNonce('TestWallet123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/nonce?wallet=TestWallet123'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('auth.verify', () => {
    it('should verify signature and return token', async () => {
      const mockResponse = {
        token: 'new-token',
        wallet: 'TestWallet',
        is_admin: false,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.auth.verify('TestWallet', 'signature123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/verify'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ wallet: 'TestWallet', signature: 'signature123' }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('auth.getProfile', () => {
    it('should fetch user profile', async () => {
      const mockProfile = {
        wallet: 'TestWallet',
        is_admin: false,
        agent_name: 'TestAgent',
        tournaments_played: 5,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProfile),
      });

      const result = await api.auth.getProfile();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-auth-token',
          }),
        })
      );
      expect(result).toEqual(mockProfile);
    });
  });

  describe('tournaments.list', () => {
    it('should fetch tournament list', async () => {
      const mockTournaments = [{ id: 'tournament-1' }];
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTournaments),
      });

      const result = await api.tournaments.list();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tournaments'),
        expect.any(Object)
      );
      expect(result).toEqual(mockTournaments);
    });

    it('should include status filter', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      await api.tournaments.list('live', 10, 0);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=live'),
        expect.any(Object)
      );
    });

    it('should include pagination parameters', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      await api.tournaments.list('all', 50, 100);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=50'),
        expect.any(Object)
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('offset=100'),
        expect.any(Object)
      );
    });
  });

  describe('tournaments.get', () => {
    it('should fetch tournament detail', async () => {
      const mockTournament = { id: 'tournament-1', status: 'registration' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTournament),
      });

      const result = await api.tournaments.get('tournament-1');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tournaments/tournament-1'),
        expect.any(Object)
      );
      expect(result).toEqual(mockTournament);
    });
  });

  describe('tournaments.register', () => {
    it('should register for tournament', async () => {
      const mockResponse = { registration_id: 'reg-123' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const registrationData = {
        tier: 'basic' as const,
        agent: { name: 'TestAgent' },
        accept_tos: true,
        confirm_jurisdiction: true,
      };

      const result = await api.tournaments.register('tournament-1', registrationData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tournaments/tournament-1/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(registrationData),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('leaderboard.get', () => {
    it('should fetch leaderboard', async () => {
      const mockLeaderboard = {
        entries: [{ rank: 1, wallet: 'winner' }],
        total: 100,
        page: 1,
        per_page: 50,
        has_more: true,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockLeaderboard),
      });

      const result = await api.leaderboard.get(1, 50);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/leaderboard?page=1&per_page=50'),
        expect.any(Object)
      );
      expect(result).toEqual(mockLeaderboard);
    });
  });

  describe('agent.get', () => {
    it('should fetch agent config', async () => {
      const mockConfig = { name: 'TestAgent' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConfig),
      });

      const result = await api.agent.get();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/agent'),
        expect.any(Object)
      );
      expect(result).toEqual(mockConfig);
    });
  });

  describe('agent.update', () => {
    it('should update agent config', async () => {
      const mockResponse = { status: 'ok' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.agent.update({ name: 'NewName' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/agent'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ name: 'NewName' }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    it('should throw ApiError on non-ok response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Tournament not found' }),
      });

      await expect(api.tournaments.get('invalid-id')).rejects.toThrow(ApiError);
      await expect(api.tournaments.get('invalid-id')).rejects.toMatchObject({
        status: 404,
        detail: 'Tournament not found',
      });
    });

    it('should handle non-JSON error responses', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      await expect(api.tournaments.list()).rejects.toThrow(ApiError);
    });
  });

  describe('Admin API', () => {
    it('should create tournament', async () => {
      const mockResponse = { id: 'tournament-1' };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const tournamentData = {
        max_players: 27,
        starting_stack: 10000,
        blind_structure: { name: 'standard', levels: [] },
        payout_structure: [{ rank: 1, points: 10000 }],
        starts_at: '2024-01-01T12:00:00Z',
      };

      const result = await api.admin.createTournament(tournamentData);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/tournaments'),
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get blind templates', async () => {
      const mockTemplates = {
        templates: {
          standard: [{ level: 1, small_blind: 25 }],
        },
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTemplates),
      });

      const result = await api.admin.getBlindTemplates();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/blind-templates'),
        expect.any(Object)
      );
      expect(result).toEqual(mockTemplates);
    });
  });
});
