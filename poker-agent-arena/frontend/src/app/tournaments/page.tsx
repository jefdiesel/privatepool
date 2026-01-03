"use client";

import { useState } from "react";
import Link from "next/link";
import { useTournaments } from "@/hooks/useTournament";
import { Tournament } from "@/lib/api";

type StatusFilter = "all" | "upcoming" | "live" | "completed";

function formatTimeUntil(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = date.getTime() - now.getTime();

  if (diff < 0) return "Started";

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `Starts in ${days}d`;
  }
  if (hours > 0) {
    return `Starts in ${hours}h ${minutes}m`;
  }
  return `Starts in ${minutes}m`;
}

function getStatusBadge(status: string) {
  switch (status) {
    case "registration":
      return (
        <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm">
          Registration Open
        </span>
      );
    case "in_progress":
      return (
        <span className="bg-yellow-500/20 text-yellow-400 px-3 py-1 rounded-full text-sm">
          In Progress
        </span>
      );
    case "completed":
      return (
        <span className="bg-slate-500/20 text-slate-400 px-3 py-1 rounded-full text-sm">
          Completed
        </span>
      );
    case "created":
      return (
        <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-sm">
          Coming Soon
        </span>
      );
    default:
      return null;
  }
}

function TournamentCard({ tournament }: { tournament: Tournament }) {
  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">
            Tournament #{tournament.on_chain_id}
          </h3>
          <p className="text-slate-400">
            {tournament.max_players} players max | {tournament.blind_structure_name}
          </p>
        </div>
        {getStatusBadge(tournament.status)}
      </div>

      <div className="flex flex-wrap gap-4 text-sm text-slate-400 mb-4">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
          </svg>
          {tournament.registered_players}/{tournament.max_players} registered
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" />
          </svg>
          {tournament.starting_stack.toLocaleString()} starting stack
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
          {formatTimeUntil(tournament.starts_at)}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          {tournament.total_points_prize.toLocaleString()} POINTS
        </span>
      </div>

      <div className="flex gap-3">
        <Link
          href={`/tournaments/${tournament.id}`}
          className="inline-block bg-accent-gold text-black font-semibold px-4 py-2 rounded-lg hover:bg-yellow-400 transition-colors"
        >
          View Details
        </Link>
        {tournament.status === "in_progress" && (
          <Link
            href={`/tournaments/${tournament.id}/live`}
            className="inline-block bg-green-600 text-white font-semibold px-4 py-2 rounded-lg hover:bg-green-500 transition-colors"
          >
            Watch Live
          </Link>
        )}
      </div>
    </div>
  );
}

export default function TournamentsPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const { tournaments, loading, error, refetch } = useTournaments({
    status: statusFilter,
    limit: 50,
  });

  const filterButtons: { label: string; value: StatusFilter }[] = [
    { label: "All", value: "all" },
    { label: "Upcoming", value: "upcoming" },
    { label: "Live", value: "live" },
    { label: "Completed", value: "completed" },
  ];

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Tournaments</h1>
        <button
          onClick={() => refetch()}
          className="text-slate-400 hover:text-white transition-colors"
          disabled={loading}
        >
          <svg
            className={`w-5 h-5 ${loading ? "animate-spin" : ""}`}
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

      {/* Filters */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => setStatusFilter(btn.value)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === btn.value
                ? "bg-felt text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => refetch()}
            className="text-red-300 underline mt-2"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && tournaments.length === 0 && (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 animate-pulse"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="h-6 bg-slate-700 rounded w-48 mb-2"></div>
                  <div className="h-4 bg-slate-700 rounded w-32"></div>
                </div>
                <div className="h-6 bg-slate-700 rounded w-24"></div>
              </div>
              <div className="flex gap-8">
                <div className="h-4 bg-slate-700 rounded w-24"></div>
                <div className="h-4 bg-slate-700 rounded w-32"></div>
                <div className="h-4 bg-slate-700 rounded w-28"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tournament List */}
      {!loading && tournaments.length > 0 && (
        <div className="grid gap-4">
          {tournaments.map((tournament) => (
            <TournamentCard key={tournament.id} tournament={tournament} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && tournaments.length === 0 && (
        <div className="bg-slate-800/50 rounded-xl p-12 border border-slate-700 text-center">
          <svg
            className="w-16 h-16 mx-auto text-slate-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
          <h3 className="text-xl font-semibold text-white mb-2">
            No tournaments found
          </h3>
          <p className="text-slate-400">
            {statusFilter === "all"
              ? "Check back soon for upcoming tournaments!"
              : `No ${statusFilter} tournaments at the moment.`}
          </p>
        </div>
      )}
    </div>
  );
}
