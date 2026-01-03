"use client";

import { useState, useEffect } from "react";
import { api, LeaderboardEntry, LeaderboardResponse } from "@/lib/api";

function truncateWallet(wallet: string): string {
  return `${wallet.slice(0, 6)}...${wallet.slice(-4)}`;
}

function getRankBadge(rank: number) {
  if (rank === 1) {
    return "bg-accent-gold text-black";
  }
  if (rank === 2) {
    return "bg-gray-300 text-black";
  }
  if (rank === 3) {
    return "bg-amber-600 text-white";
  }
  return "bg-slate-600 text-white";
}

export default function LeaderboardPage() {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const fetchLeaderboard = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.leaderboard.get(pageNum, 50);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load leaderboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard(page);
  }, [page]);

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold text-white mb-8">Leaderboard</h1>

      {/* Stats Summary */}
      {data && (
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center">
            <p className="text-slate-400 text-sm mb-2">Total Players</p>
            <p className="text-3xl font-bold text-white">{data.total}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center">
            <p className="text-slate-400 text-sm mb-2">Page</p>
            <p className="text-3xl font-bold text-white">
              {data.page} / {Math.ceil(data.total / data.per_page) || 1}
            </p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center">
            <p className="text-slate-400 text-sm mb-2">Top Player POINTS</p>
            <p className="text-3xl font-bold text-accent-gold">
              {data.entries[0]?.total_points.toLocaleString() || 0}
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => fetchLeaderboard(page)}
            className="text-red-300 underline mt-2"
          >
            Try again
          </button>
        </div>
      )}

      {/* Leaderboard Table */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        {loading ? (
          <div className="animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="flex items-center px-6 py-4 border-b border-slate-700"
              >
                <div className="w-8 h-8 bg-slate-700 rounded-full"></div>
                <div className="ml-4 flex-1">
                  <div className="h-4 bg-slate-700 rounded w-32"></div>
                </div>
                <div className="h-4 bg-slate-700 rounded w-24"></div>
              </div>
            ))}
          </div>
        ) : data && data.entries.length > 0 ? (
          <>
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="text-left text-slate-400 text-sm font-medium px-6 py-4">
                    Rank
                  </th>
                  <th className="text-left text-slate-400 text-sm font-medium px-6 py-4">
                    Agent
                  </th>
                  <th className="text-left text-slate-400 text-sm font-medium px-6 py-4 hidden md:table-cell">
                    Wallet
                  </th>
                  <th className="text-right text-slate-400 text-sm font-medium px-6 py-4">
                    Tournaments
                  </th>
                  <th className="text-right text-slate-400 text-sm font-medium px-6 py-4">
                    Wins
                  </th>
                  <th className="text-right text-slate-400 text-sm font-medium px-6 py-4">
                    POINTS
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {data.entries.map((entry) => (
                  <tr
                    key={entry.wallet}
                    className="hover:bg-slate-700/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${getRankBadge(entry.rank)}`}
                      >
                        {entry.rank}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-600 rounded-full flex items-center justify-center text-white font-medium">
                          {(entry.agent_name || "?")[0].toUpperCase()}
                        </div>
                        <span className="text-white font-medium">
                          {entry.agent_name || "Unknown"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-400 font-mono text-sm hidden md:table-cell">
                      {truncateWallet(entry.wallet)}
                    </td>
                    <td className="px-6 py-4 text-right text-white">
                      {entry.tournaments_played}
                    </td>
                    <td className="px-6 py-4 text-right text-white">
                      {entry.tournaments_won}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-accent-gold font-bold">
                        {entry.total_points.toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="px-6 py-4 border-t border-slate-700 flex justify-between items-center">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-slate-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors"
              >
                Previous
              </button>
              <span className="text-slate-400">
                Page {data.page} of {Math.ceil(data.total / data.per_page) || 1}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.has_more}
                className="px-4 py-2 bg-slate-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors"
              >
                Next
              </button>
            </div>
          </>
        ) : (
          <div className="px-6 py-12 text-center text-slate-400">
            No players on the leaderboard yet. Be the first to compete!
          </div>
        )}
      </div>
    </div>
  );
}
