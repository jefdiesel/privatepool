"use client";

import { useState, useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useWalletStore } from "@/stores/walletStore";
import { useTournaments } from "@/hooks/useTournament";
import {
  api,
  BlindLevel,
  BlindStructure,
  PayoutEntry,
  Tournament,
} from "@/lib/api";

const VALID_PLAYER_COUNTS = [9, 18, 27, 36, 45, 54];

const DEFAULT_PAYOUTS: PayoutEntry[] = [
  { rank: 1, points: 5000 },
  { rank: 2, points: 3000 },
  { rank: 3, points: 2000 },
  { rank: 4, points: 1000 },
  { rank: 5, points: 500 },
  { rank: 6, points: 500 },
];

export default function AdminPage() {
  const { connected, publicKey, signMessage } = useWallet();
  const { isAuthenticated, isAdmin, authenticate } = useWalletStore();
  const { tournaments, loading: loadingTournaments, refetch } = useTournaments({
    status: "upcoming",
  });

  // Form state
  const [maxPlayers, setMaxPlayers] = useState(27);
  const [startingStack, setStartingStack] = useState(10000);
  const [blindTemplate, setBlindTemplate] = useState("standard");
  const [startsAt, setStartsAt] = useState("");
  const [payouts, setPayouts] = useState<PayoutEntry[]>(DEFAULT_PAYOUTS);
  const [blindTemplates, setBlindTemplates] = useState<Record<string, BlindLevel[]>>({});

  // UI state
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Load blind templates
  useEffect(() => {
    if (isAdmin) {
      api.admin.getBlindTemplates().then((data) => {
        setBlindTemplates(data.templates);
      }).catch(() => {
        // Ignore error - templates are optional
      });
    }
  }, [isAdmin]);

  const handleAuthenticate = async () => {
    if (!signMessage) return;
    await authenticate(signMessage);
  };

  const handleCreateTournament = async () => {
    if (!startsAt) {
      setCreateError("Please set a start time");
      return;
    }

    setIsCreating(true);
    setCreateError(null);
    setCreateSuccess(false);

    try {
      const levels = blindTemplates[blindTemplate] || [];
      const blindStructure: BlindStructure = {
        name: blindTemplate,
        levels,
      };

      await api.admin.createTournament({
        max_players: maxPlayers,
        starting_stack: startingStack,
        blind_structure: blindStructure,
        payout_structure: payouts,
        starts_at: new Date(startsAt).toISOString(),
      });

      setCreateSuccess(true);
      refetch();
      setTimeout(() => setCreateSuccess(false), 3000);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create tournament");
    } finally {
      setIsCreating(false);
    }
  };

  const handleStartRegistration = async (tournamentId: string) => {
    setActionLoading(tournamentId);
    try {
      await api.admin.startRegistration(tournamentId);
      refetch();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to start registration");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelTournament = async (tournamentId: string) => {
    if (!confirm("Are you sure you want to cancel this tournament?")) return;

    setActionLoading(tournamentId);
    try {
      await api.admin.cancelTournament(tournamentId);
      refetch();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to cancel tournament");
    } finally {
      setActionLoading(null);
    }
  };

  const updatePayout = (rank: number, points: number) => {
    setPayouts((prev) =>
      prev.map((p) => (p.rank === rank ? { ...p, points } : p))
    );
  };

  const addPayout = () => {
    const nextRank = payouts.length + 1;
    setPayouts([...payouts, { rank: nextRank, points: 100 }]);
  };

  const removePayout = (rank: number) => {
    if (payouts.length <= 1) return;
    setPayouts(payouts.filter((p) => p.rank !== rank).map((p, i) => ({ ...p, rank: i + 1 })));
  };

  if (!connected) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Admin Dashboard</h1>
          <p className="text-slate-400 mb-8">
            Connect your admin wallet to access the dashboard.
          </p>
          <WalletMultiButton className="!bg-felt hover:!bg-felt-light !rounded-lg" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Admin Dashboard</h1>
          <p className="text-slate-400 mb-8">
            Sign a message to authenticate as admin.
          </p>
          <button
            onClick={handleAuthenticate}
            className="bg-accent-gold text-black font-semibold px-6 py-3 rounded-lg hover:bg-yellow-400 transition-colors"
          >
            Authenticate
          </button>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-3xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-slate-400 mb-4">
            This wallet is not authorized to access the admin dashboard.
          </p>
          <p className="text-slate-500 text-sm font-mono">
            Connected: {publicKey?.toString().slice(0, 8)}...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold text-white mb-8">Admin Dashboard</h1>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Create Tournament */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            Create Tournament
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-slate-400 text-sm mb-2">
                Max Players
              </label>
              <select
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(Number(e.target.value))}
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
              >
                {VALID_PLAYER_COUNTS.map((count) => (
                  <option key={count} value={count}>
                    {count} Players ({count / 9} tables)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 text-sm mb-2">
                Starting Stack
              </label>
              <input
                type="number"
                value={startingStack}
                onChange={(e) => setStartingStack(Number(e.target.value))}
                min={1000}
                step={1000}
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-slate-400 text-sm mb-2">
                Blind Structure
              </label>
              <select
                value={blindTemplate}
                onChange={(e) => setBlindTemplate(e.target.value)}
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
              >
                <option value="turbo">Turbo (6 min levels)</option>
                <option value="standard">Standard (12 min levels)</option>
                <option value="deep_stack">Deep Stack (20 min levels)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 text-sm mb-2">
                Start Time
              </label>
              <input
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
                className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
              />
            </div>

            {createError && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-400 text-sm">{createError}</p>
              </div>
            )}

            {createSuccess && (
              <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                <p className="text-green-400 text-sm">Tournament created!</p>
              </div>
            )}

            <button
              onClick={handleCreateTournament}
              disabled={isCreating}
              className="w-full bg-felt text-white font-semibold py-3 rounded-lg hover:bg-felt-light transition-colors disabled:opacity-50"
            >
              {isCreating ? "Creating..." : "Create Tournament"}
            </button>
          </div>
        </div>

        {/* Upcoming Tournaments */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">
              Upcoming Tournaments
            </h2>
            <button
              onClick={() => refetch()}
              className="text-slate-400 hover:text-white"
              disabled={loadingTournaments}
            >
              <svg
                className={`w-5 h-5 ${loadingTournaments ? "animate-spin" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            {loadingTournaments ? (
              <div className="animate-pulse space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className="h-24 bg-slate-700/50 rounded-lg"></div>
                ))}
              </div>
            ) : tournaments.length > 0 ? (
              tournaments.map((tournament) => (
                <TournamentCard
                  key={tournament.id}
                  tournament={tournament}
                  onStartRegistration={handleStartRegistration}
                  onCancel={handleCancelTournament}
                  isLoading={actionLoading === tournament.id}
                />
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                No upcoming tournaments
              </div>
            )}
          </div>
        </div>

        {/* Payout Structure */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">
              Payout Structure
            </h2>
            <button
              onClick={addPayout}
              className="text-accent-gold hover:text-yellow-400 text-sm"
            >
              + Add Position
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {payouts.map((payout) => (
              <div key={payout.rank} className="text-center relative group">
                <p className="text-slate-400 text-sm mb-1">
                  {payout.rank === 1
                    ? "1st"
                    : payout.rank === 2
                    ? "2nd"
                    : payout.rank === 3
                    ? "3rd"
                    : `${payout.rank}th`}
                </p>
                <input
                  type="number"
                  value={payout.points}
                  onChange={(e) => updatePayout(payout.rank, Number(e.target.value))}
                  min={0}
                  step={100}
                  className="w-full bg-slate-700 text-white text-center rounded-lg px-2 py-2 border border-slate-600 focus:border-accent-gold focus:outline-none"
                />
                <p className="text-accent-gold text-xs mt-1">POINTS</p>
                {payouts.length > 1 && (
                  <button
                    onClick={() => removePayout(payout.rank)}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    x
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-700">
            <p className="text-slate-400 text-sm">
              Total Prize Pool:{" "}
              <span className="text-accent-gold font-bold">
                {payouts.reduce((sum, p) => sum + p.points, 0).toLocaleString()} POINTS
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function TournamentCard({
  tournament,
  onStartRegistration,
  onCancel,
  isLoading,
}: {
  tournament: Tournament;
  onStartRegistration: (id: string) => void;
  onCancel: (id: string) => void;
  isLoading: boolean;
}) {
  const getStatusBadge = () => {
    switch (tournament.status) {
      case "created":
        return (
          <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">
            Created
          </span>
        );
      case "registration":
        return (
          <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs">
            Registration
          </span>
        );
      case "in_progress":
        return (
          <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded text-xs">
            In Progress
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-4 bg-slate-700/50 rounded-lg">
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className="text-white font-medium">Tournament #{tournament.on_chain_id}</p>
          <p className="text-slate-400 text-sm">
            {tournament.registered_players}/{tournament.max_players} players
          </p>
          <p className="text-slate-500 text-xs">
            Starts: {new Date(tournament.starts_at).toLocaleString()}
          </p>
        </div>
        {getStatusBadge()}
      </div>
      <div className="flex gap-2">
        {tournament.status === "created" && (
          <button
            onClick={() => onStartRegistration(tournament.id)}
            disabled={isLoading}
            className="flex-1 bg-accent-gold text-black text-sm font-medium py-2 rounded hover:bg-yellow-400 transition-colors disabled:opacity-50"
          >
            {isLoading ? "..." : "Open Registration"}
          </button>
        )}
        {(tournament.status === "created" || tournament.status === "registration") && (
          <button
            onClick={() => onCancel(tournament.id)}
            disabled={isLoading}
            className="flex-1 bg-slate-600 text-white text-sm font-medium py-2 rounded hover:bg-slate-500 transition-colors disabled:opacity-50"
          >
            {isLoading ? "..." : "Cancel"}
          </button>
        )}
        {tournament.status === "in_progress" && (
          <a
            href={`/tournaments/${tournament.id}/live`}
            className="flex-1 bg-green-600 text-white text-sm font-medium py-2 rounded hover:bg-green-500 transition-colors text-center"
          >
            Watch Live
          </a>
        )}
      </div>
    </div>
  );
}
