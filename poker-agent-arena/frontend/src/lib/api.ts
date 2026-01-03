/**
 * API client for Poker Agent Arena backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface Tournament {
  id: string;
  on_chain_id: number;
  status: 'created' | 'registration' | 'in_progress' | 'completed' | 'cancelled';
  max_players: number;
  registered_players: number;
  starting_stack: number;
  starts_at: string;
  blind_structure_name: string;
  total_points_prize: number;
}

export interface TournamentDetail extends Tournament {
  blind_structure: BlindStructure;
  payout_structure: PayoutEntry[];
  created_at: string;
  registration_opens_at: string | null;
  completed_at: string | null;
  winner_wallet: string | null;
  results_hash: string | null;
  user_registered: boolean;
  user_tier: string | null;
  user_agent_name: string | null;
}

export interface BlindLevel {
  level: number;
  small_blind: number;
  big_blind: number;
  ante: number;
  duration_minutes: number;
}

export interface BlindStructure {
  name: string;
  levels: BlindLevel[];
}

export interface PayoutEntry {
  rank: number;
  points: number;
}

export interface AgentSliders {
  aggression: number;
  bluff_frequency: number;
  tightness: number;
  position_awareness: number;
}

export interface AgentConfig {
  name: string;
  image_uri?: string | null;
  sliders?: AgentSliders | null;
  custom_prompt?: string | null;
}

export interface RegistrationRequest {
  tier: 'free' | 'basic' | 'pro';
  agent: AgentConfig;
  accept_tos: boolean;
  confirm_jurisdiction: boolean;
  payment_signature?: string | null;
}

export interface RegistrationResponse {
  registration_id: string;
  tournament_id: string;
  wallet: string;
  tier: string;
  agent_name: string;
  registered_at: string;
  prompt_hash: string;
}

export interface LeaderboardEntry {
  rank: number;
  wallet: string;
  agent_name: string | null;
  total_points: number;
  tournaments_played: number;
  tournaments_won: number;
  best_finish: number | null;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface UserProfile {
  wallet: string;
  is_admin: boolean;
  agent_name: string | null;
  agent_image_uri: string | null;
  agent_tier: string | null;
  tournaments_played: number;
  tournaments_won: number;
  total_points: number;
  best_finish: number | null;
}

export interface PlayerResult {
  rank: number;
  wallet: string;
  agent_name: string;
  points_awarded: number;
  hands_played: number;
  eliminations: number;
}

export interface TournamentResults {
  tournament_id: string;
  status: string;
  completed_at: string | null;
  results_hash: string | null;
  results: PlayerResult[];
}

// API Error
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

// Token storage
let sessionToken: string | null = null;

export function setSessionToken(token: string | null) {
  sessionToken = token;
  if (token) {
    localStorage.setItem('session_token', token);
  } else {
    localStorage.removeItem('session_token');
  }
}

export function getSessionToken(): string | null {
  if (sessionToken) return sessionToken;
  if (typeof window !== 'undefined') {
    sessionToken = localStorage.getItem('session_token');
  }
  return sessionToken;
}

// Fetch helpers
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getSessionToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, data.detail || 'API request failed');
  }

  return response.json();
}

// API methods
export const api = {
  // Auth
  auth: {
    getNonce: (wallet: string) =>
      apiFetch<{ nonce: string; message: string }>(`/api/auth/nonce?wallet=${wallet}`),

    verify: (wallet: string, signature: string) =>
      apiFetch<{ token: string; wallet: string; is_admin: boolean }>('/api/auth/verify', {
        method: 'POST',
        body: JSON.stringify({ wallet, signature }),
      }),

    getProfile: () => apiFetch<UserProfile>('/api/auth/me'),

    logout: () => apiFetch<{ status: string }>('/api/auth/logout', { method: 'POST' }),
  },

  // Tournaments
  tournaments: {
    list: (status?: 'upcoming' | 'live' | 'completed' | 'all', limit = 20, offset = 0) => {
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      params.set('limit', limit.toString());
      params.set('offset', offset.toString());
      return apiFetch<Tournament[]>(`/api/tournaments?${params}`);
    },

    get: (id: string) => apiFetch<TournamentDetail>(`/api/tournaments/${id}`),

    register: (id: string, data: RegistrationRequest) =>
      apiFetch<RegistrationResponse>(`/api/tournaments/${id}/register`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    getResults: (id: string) => apiFetch<TournamentResults>(`/api/tournaments/${id}/results`),
  },

  // Agent
  agent: {
    get: () => apiFetch<AgentConfig | null>('/api/agent'),

    update: (data: Partial<AgentConfig>) =>
      apiFetch<{ status: string }>('/api/agent', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },

  // Leaderboard
  leaderboard: {
    get: (page = 1, perPage = 50) =>
      apiFetch<LeaderboardResponse>(`/api/leaderboard?page=${page}&per_page=${perPage}`),

    getPlayer: (wallet: string) =>
      apiFetch<LeaderboardEntry | null>(`/api/leaderboard/player/${wallet}`),
  },

  // Admin
  admin: {
    createTournament: (data: {
      max_players: number;
      starting_stack: number;
      blind_structure: BlindStructure;
      payout_structure: PayoutEntry[];
      registration_opens_at?: string;
      starts_at: string;
    }) =>
      apiFetch<TournamentDetail>('/api/admin/tournaments', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    startRegistration: (id: string) =>
      apiFetch<{ status: string; tournament_id: string }>(
        `/api/admin/tournaments/${id}/start`,
        { method: 'POST' }
      ),

    cancelTournament: (id: string) =>
      apiFetch<{ status: string; tournament_id: string }>(
        `/api/admin/tournaments/${id}/cancel`,
        { method: 'POST' }
      ),

    getBlindTemplates: () =>
      apiFetch<{ templates: Record<string, BlindLevel[]> }>('/api/admin/blind-templates'),

    getTournamentStats: (id: string) =>
      apiFetch<{
        tournament_id: string;
        status: string;
        registered_players: number;
        max_players: number;
        tier_breakdown: Record<string, number>;
        hands_played: number;
        starts_at: string | null;
        completed_at: string | null;
      }>(`/api/admin/tournaments/${id}/stats`),
  },
};
