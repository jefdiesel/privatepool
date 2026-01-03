/**
 * React hook for tournament data fetching
 */

import { useState, useEffect, useCallback } from 'react';
import { api, Tournament, TournamentDetail, TournamentResults, ApiError } from '@/lib/api';

interface UseTournamentsOptions {
  status?: 'upcoming' | 'live' | 'completed' | 'all';
  limit?: number;
  offset?: number;
  autoFetch?: boolean;
}

export function useTournaments(options: UseTournamentsOptions = {}) {
  const { status = 'all', limit = 20, offset = 0, autoFetch = true } = options;
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTournaments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.tournaments.list(status, limit, offset);
      setTournaments(data);
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Failed to fetch tournaments';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [status, limit, offset]);

  useEffect(() => {
    if (autoFetch) {
      fetchTournaments();
    }
  }, [autoFetch, fetchTournaments]);

  return {
    tournaments,
    loading,
    error,
    refetch: fetchTournaments,
  };
}

interface UseTournamentOptions {
  autoFetch?: boolean;
}

export function useTournament(id: string | null, options: UseTournamentOptions = {}) {
  const { autoFetch = true } = options;
  const [tournament, setTournament] = useState<TournamentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTournament = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.tournaments.get(id);
      setTournament(data);
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Failed to fetch tournament';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (autoFetch && id) {
      fetchTournament();
    }
  }, [autoFetch, id, fetchTournament]);

  return {
    tournament,
    loading,
    error,
    refetch: fetchTournament,
  };
}

export function useTournamentResults(id: string | null) {
  const [results, setResults] = useState<TournamentResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.tournaments.getResults(id);
      setResults(data);
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : 'Failed to fetch results';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchResults();
    }
  }, [id, fetchResults]);

  return {
    results,
    loading,
    error,
    refetch: fetchResults,
  };
}
