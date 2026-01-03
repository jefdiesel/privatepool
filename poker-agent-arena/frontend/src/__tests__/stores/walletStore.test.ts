/**
 * Tests for Wallet Store (Zustand)
 */

import { act } from '@testing-library/react';
import { useWalletStore, selectIsConnected, selectIsAuthenticated, selectIsAdmin } from '@/stores/walletStore';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock api module
jest.mock('@/lib/api', () => ({
  api: {
    auth: {
      getNonce: jest.fn(),
      verify: jest.fn(),
      getProfile: jest.fn(),
    },
    agent: {
      get: jest.fn(),
      update: jest.fn(),
    },
  },
  setSessionToken: jest.fn(),
  getSessionToken: jest.fn(),
}));

import { api, setSessionToken, getSessionToken } from '@/lib/api';

// Reset store before each test
beforeEach(() => {
  // Reset store state manually
  act(() => {
    useWalletStore.setState({
      connected: false,
      publicKey: null,
      isAuthenticated: false,
      isAdmin: false,
      sessionToken: null,
      profile: null,
      agentConfig: null,
      isAuthenticating: false,
      isLoadingProfile: false,
      error: null,
    });
  });
  jest.clearAllMocks();
});

describe('WalletStore', () => {
  describe('setConnected', () => {
    it('should set connected state and public key', () => {
      act(() => {
        useWalletStore.getState().setConnected(true, 'TestPublicKey123');
      });

      expect(useWalletStore.getState().connected).toBe(true);
      expect(useWalletStore.getState().publicKey).toBe('TestPublicKey123');
    });

    it('should clear auth state when disconnected', () => {
      // First connect and authenticate
      act(() => {
        useWalletStore.setState({
          connected: true,
          publicKey: 'TestPublicKey123',
          isAuthenticated: true,
          isAdmin: false,
          sessionToken: 'token123',
        });
      });

      // Then disconnect
      act(() => {
        useWalletStore.getState().setConnected(false, null);
      });

      const state = useWalletStore.getState();
      expect(state.connected).toBe(false);
      expect(state.publicKey).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.sessionToken).toBeNull();
      expect(state.profile).toBeNull();
    });

    it('should check for existing session on connect', async () => {
      (getSessionToken as jest.Mock).mockReturnValue('existing-token');
      (api.auth.getProfile as jest.Mock).mockResolvedValue({
        wallet: 'TestWallet',
        is_admin: false,
      });

      await act(async () => {
        useWalletStore.getState().setConnected(true, 'TestPublicKey123');
        // Wait for async profile load
        await new Promise((resolve) => setTimeout(resolve, 10));
      });

      expect(getSessionToken).toHaveBeenCalled();
    });
  });

  describe('authenticate', () => {
    it('should fail if wallet not connected', async () => {
      const mockSignMessage = jest.fn();

      const result = await act(async () => {
        return useWalletStore.getState().authenticate(mockSignMessage);
      });

      expect(result).toBe(false);
      expect(useWalletStore.getState().error).toBe('Wallet not connected');
    });

    it('should authenticate successfully', async () => {
      (api.auth.getNonce as jest.Mock).mockResolvedValue({
        nonce: 'test-nonce',
        message: 'Sign this message',
      });
      (api.auth.verify as jest.Mock).mockResolvedValue({
        token: 'test-token',
        wallet: 'TestWallet',
        is_admin: true,
      });
      (api.auth.getProfile as jest.Mock).mockResolvedValue({
        wallet: 'TestWallet',
        is_admin: true,
      });

      // Create a non-zero signature (zeros have special handling in base58)
      const mockSignature = new Uint8Array(64);
      for (let i = 0; i < 64; i++) {
        mockSignature[i] = i + 1;
      }
      const mockSignMessage = jest.fn().mockResolvedValue(mockSignature);

      // First connect
      act(() => {
        useWalletStore.setState({
          connected: true,
          publicKey: 'TestPublicKey123',
        });
      });

      let result: boolean = false;
      await act(async () => {
        result = await useWalletStore.getState().authenticate(mockSignMessage);
      });

      expect(api.auth.getNonce).toHaveBeenCalledWith('TestPublicKey123');
      expect(mockSignMessage).toHaveBeenCalled();
      expect(api.auth.verify).toHaveBeenCalled();
      expect(setSessionToken).toHaveBeenCalledWith('test-token');
      expect(result).toBe(true);

      const state = useWalletStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.isAdmin).toBe(true);
      expect(state.sessionToken).toBe('test-token');
    });

    it('should handle authentication error', async () => {
      (api.auth.getNonce as jest.Mock).mockRejectedValue(new Error('Network error'));

      const mockSignMessage = jest.fn();

      act(() => {
        useWalletStore.setState({
          connected: true,
          publicKey: 'TestPublicKey123',
        });
      });

      const result = await act(async () => {
        return useWalletStore.getState().authenticate(mockSignMessage);
      });

      expect(result).toBe(false);
      expect(useWalletStore.getState().error).toBe('Network error');
      expect(useWalletStore.getState().isAuthenticating).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear all auth state', () => {
      act(() => {
        useWalletStore.setState({
          connected: true,
          publicKey: 'TestPublicKey123',
          isAuthenticated: true,
          isAdmin: true,
          sessionToken: 'test-token',
          profile: { wallet: 'TestWallet', is_admin: true } as any,
          agentConfig: { name: 'TestAgent' } as any,
        });
      });

      act(() => {
        useWalletStore.getState().logout();
      });

      const state = useWalletStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isAdmin).toBe(false);
      expect(state.sessionToken).toBeNull();
      expect(state.profile).toBeNull();
      expect(state.agentConfig).toBeNull();
      expect(setSessionToken).toHaveBeenCalledWith(null);
    });
  });

  describe('loadProfile', () => {
    it('should load profile successfully', async () => {
      const mockProfile = {
        wallet: 'TestWallet',
        is_admin: false,
        agent_name: 'TestAgent',
        agent_image_uri: null,
        agent_tier: 'FREE',
        tournaments_played: 5,
        tournaments_won: 1,
        total_points: 1000,
        best_finish: 1,
      };
      (api.auth.getProfile as jest.Mock).mockResolvedValue(mockProfile);

      await act(async () => {
        await useWalletStore.getState().loadProfile();
      });

      const state = useWalletStore.getState();
      expect(state.profile).toEqual(mockProfile);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isAdmin).toBe(false);
      expect(state.isLoadingProfile).toBe(false);
    });

    it('should handle load profile error', async () => {
      (api.auth.getProfile as jest.Mock).mockRejectedValue(new Error('Unauthorized'));

      await expect(
        act(async () => {
          await useWalletStore.getState().loadProfile();
        })
      ).rejects.toThrow('Unauthorized');

      expect(useWalletStore.getState().isLoadingProfile).toBe(false);
    });
  });

  describe('loadAgentConfig', () => {
    it('should load agent config', async () => {
      const mockConfig = {
        name: 'TestAgent',
        image_uri: 'https://example.com/avatar.jpg',
        sliders: {
          aggression: 50,
          bluff_frequency: 30,
          tightness: 60,
          position_awareness: 70,
        },
        custom_prompt: null,
      };
      (api.agent.get as jest.Mock).mockResolvedValue(mockConfig);

      await act(async () => {
        await useWalletStore.getState().loadAgentConfig();
      });

      expect(useWalletStore.getState().agentConfig).toEqual(mockConfig);
    });

    it('should silently handle agent config error', async () => {
      (api.agent.get as jest.Mock).mockRejectedValue(new Error('Not found'));

      await act(async () => {
        await useWalletStore.getState().loadAgentConfig();
      });

      // Should not throw, just leave agentConfig as is
      expect(useWalletStore.getState().agentConfig).toBeNull();
    });
  });

  describe('updateAgentConfig', () => {
    it('should update agent config', async () => {
      (api.agent.update as jest.Mock).mockResolvedValue({ status: 'ok' });
      (api.agent.get as jest.Mock).mockResolvedValue({
        name: 'UpdatedAgent',
        sliders: null,
      });

      await act(async () => {
        await useWalletStore.getState().updateAgentConfig({ name: 'UpdatedAgent' });
      });

      expect(api.agent.update).toHaveBeenCalledWith({ name: 'UpdatedAgent' });
      expect(api.agent.get).toHaveBeenCalled();
    });

    it('should set error on update failure', async () => {
      (api.agent.update as jest.Mock).mockRejectedValue(new Error('Update failed'));

      await expect(
        act(async () => {
          await useWalletStore.getState().updateAgentConfig({ name: 'NewName' });
        })
      ).rejects.toThrow('Update failed');

      expect(useWalletStore.getState().error).toBe('Update failed');
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      act(() => {
        useWalletStore.setState({ error: 'Some error' });
        useWalletStore.getState().clearError();
      });

      expect(useWalletStore.getState().error).toBeNull();
    });
  });
});

describe('Selectors', () => {
  describe('selectIsConnected', () => {
    it('should return connected state', () => {
      act(() => {
        useWalletStore.setState({ connected: true });
      });

      const state = useWalletStore.getState();
      expect(selectIsConnected(state)).toBe(true);
    });
  });

  describe('selectIsAuthenticated', () => {
    it('should return authenticated state', () => {
      act(() => {
        useWalletStore.setState({ isAuthenticated: true });
      });

      const state = useWalletStore.getState();
      expect(selectIsAuthenticated(state)).toBe(true);
    });
  });

  describe('selectIsAdmin', () => {
    it('should return admin state', () => {
      act(() => {
        useWalletStore.setState({ isAdmin: true });
      });

      const state = useWalletStore.getState();
      expect(selectIsAdmin(state)).toBe(true);
    });
  });
});
