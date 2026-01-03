/**
 * Wallet and authentication state store using Zustand
 */

import { create } from 'zustand';
import { api, setSessionToken, getSessionToken, UserProfile, AgentConfig } from '@/lib/api';

interface WalletState {
  // Connection state
  connected: boolean;
  publicKey: string | null;

  // Authentication state
  isAuthenticated: boolean;
  isAdmin: boolean;
  sessionToken: string | null;

  // User data
  profile: UserProfile | null;
  agentConfig: AgentConfig | null;

  // Loading states
  isAuthenticating: boolean;
  isLoadingProfile: boolean;

  // Error state
  error: string | null;

  // Actions
  setConnected: (connected: boolean, publicKey: string | null) => void;
  authenticate: (signMessage: (message: Uint8Array) => Promise<Uint8Array>) => Promise<boolean>;
  logout: () => void;
  loadProfile: () => Promise<void>;
  loadAgentConfig: () => Promise<void>;
  updateAgentConfig: (config: Partial<AgentConfig>) => Promise<void>;
  clearError: () => void;
}

export const useWalletStore = create<WalletState>((set, get) => ({
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

  setConnected: (connected, publicKey) => {
    set({ connected, publicKey });

    // Check for existing session on connect
    if (connected && publicKey) {
      const token = getSessionToken();
      if (token) {
        // Validate token by loading profile
        get().loadProfile().catch(() => {
          // Token invalid, clear it
          setSessionToken(null);
          set({ isAuthenticated: false, sessionToken: null });
        });
      }
    } else {
      // Disconnected, clear auth state
      set({
        isAuthenticated: false,
        isAdmin: false,
        sessionToken: null,
        profile: null,
        agentConfig: null,
      });
    }
  },

  authenticate: async (signMessage) => {
    const { publicKey } = get();
    if (!publicKey) {
      set({ error: 'Wallet not connected' });
      return false;
    }

    set({ isAuthenticating: true, error: null });

    try {
      // Get nonce
      const { message } = await api.auth.getNonce(publicKey);

      // Sign message
      const messageBytes = new TextEncoder().encode(message);
      const signatureBytes = await signMessage(messageBytes);

      // Convert signature to base58
      const signature = encodeBase58(signatureBytes);

      // Verify with backend
      const { token, is_admin } = await api.auth.verify(publicKey, signature);

      // Store session
      setSessionToken(token);

      set({
        isAuthenticated: true,
        isAdmin: is_admin,
        sessionToken: token,
        isAuthenticating: false,
      });

      // Load profile
      get().loadProfile();

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed';
      set({ error: message, isAuthenticating: false });
      return false;
    }
  },

  logout: () => {
    setSessionToken(null);
    set({
      isAuthenticated: false,
      isAdmin: false,
      sessionToken: null,
      profile: null,
      agentConfig: null,
    });
  },

  loadProfile: async () => {
    set({ isLoadingProfile: true });

    try {
      const profile = await api.auth.getProfile();
      set({
        profile,
        isAuthenticated: true,
        isAdmin: profile.is_admin,
        isLoadingProfile: false,
      });
    } catch (err) {
      set({ isLoadingProfile: false });
      throw err;
    }
  },

  loadAgentConfig: async () => {
    try {
      const config = await api.agent.get();
      set({ agentConfig: config });
    } catch {
      // Ignore errors - user might not have an agent config yet
    }
  },

  updateAgentConfig: async (config) => {
    try {
      await api.agent.update(config);
      // Reload config
      await get().loadAgentConfig();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update agent';
      set({ error: message });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));

// Helper to encode bytes to base58
function encodeBase58(bytes: Uint8Array): string {
  const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  const BASE = 58;

  if (bytes.length === 0) return '';

  // Count leading zeros
  let zeros = 0;
  for (let i = 0; i < bytes.length && bytes[i] === 0; i++) {
    zeros++;
  }

  // Convert to base58
  const size = Math.floor((bytes.length * 138) / 100) + 1;
  const b58 = new Uint8Array(size);

  for (let i = zeros; i < bytes.length; i++) {
    let carry = bytes[i];
    for (let j = size - 1; j >= 0; j--) {
      carry += 256 * b58[j];
      b58[j] = carry % BASE;
      carry = Math.floor(carry / BASE);
    }
  }

  // Skip leading zeros in base58
  let start = 0;
  while (start < size && b58[start] === 0) {
    start++;
  }

  // Build result string
  let result = ALPHABET[0].repeat(zeros);
  for (let i = start; i < size; i++) {
    result += ALPHABET[b58[i]];
  }

  return result;
}

// Selectors
export const selectIsConnected = (state: WalletState) => state.connected;
export const selectIsAuthenticated = (state: WalletState) => state.isAuthenticated;
export const selectIsAdmin = (state: WalletState) => state.isAdmin;
export const selectProfile = (state: WalletState) => state.profile;
