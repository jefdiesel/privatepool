"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, LeaderboardEntry, LeaderboardResponse } from "@/lib/api";
import { useOnboardingStore } from "@/stores/onboardingStore";

function truncateWallet(wallet: string): string {
  return `${wallet.slice(0, 6)}...${wallet.slice(-4)}`;
}

export default function LeaderboardPage() {
  const router = useRouter();
  const { isOnboardingComplete } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isOnboardingComplete) {
      router.push('/onboarding');
    }
  }, [mounted, isOnboardingComplete, router]);

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
    if (mounted) {
      fetchLeaderboard(page);
    }
  }, [page, mounted]);

  if (!mounted) return null;

  const firstPlace = data?.entries.find(e => e.rank === 1);
  const otherEntries = data?.entries.filter(e => e.rank !== 1) || [];

  return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">LEADERBOARD</h1>

        {/* Error State */}
        {error && (
          <div className="border border-red-500/30 bg-red-500/10 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
            <button
              onClick={() => fetchLeaderboard(page)}
              className="text-red-300 underline mt-2 text-sm"
            >
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div className="animate-pulse space-y-4">
            <div className="border border-red-500/20 rounded-lg p-8 bg-slate-950/50">
              <div className="flex flex-col items-center">
                <div className="w-20 h-20 bg-slate-800 rounded-full mb-4"></div>
                <div className="h-4 bg-slate-800 rounded w-32 mb-2"></div>
                <div className="h-6 bg-slate-800 rounded w-24"></div>
              </div>
            </div>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="border border-red-500/20 rounded-lg p-4 bg-slate-950/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 bg-slate-800 rounded"></div>
                    <div className="w-8 h-8 bg-slate-800 rounded-full"></div>
                    <div className="h-4 bg-slate-800 rounded w-32"></div>
                  </div>
                  <div className="h-4 bg-slate-800 rounded w-24"></div>
                </div>
              </div>
            ))}
          </div>
        ) : data && data.entries.length > 0 ? (
          <>
            {/* 1st Place Featured */}
            {firstPlace && (
              <div className="border border-red-500/30 rounded-lg p-8 bg-slate-950/50 mb-6">
                <div className="flex flex-col items-center">
                  {/* 1st Place Badge */}
                  <div className="text-xs text-red-500 font-bold mb-2">1st PLACE</div>

                  {/* Avatar */}
                  <div className="w-20 h-20 rounded-full border-2 border-red-500 flex items-center justify-center bg-slate-900 mb-3 overflow-hidden">
                    {firstPlace.image_uri ? (
                      <img
                        src={firstPlace.image_uri}
                        alt={firstPlace.agent_name || "Agent"}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-2xl font-bold text-red-500">
                        {(firstPlace.agent_name || "?")[0].toUpperCase()}
                      </span>
                    )}
                  </div>

                  {/* Name */}
                  <h3 className="text-white font-semibold text-lg mb-1">
                    {firstPlace.agent_name || "Unknown"}
                  </h3>

                  {/* Points */}
                  <p className="text-red-500 font-bold text-2xl">
                    {firstPlace.total_points.toLocaleString()} POINTS
                  </p>

                  {/* Stats */}
                  <div className="flex gap-6 mt-4 text-sm text-slate-400">
                    <span>{firstPlace.tournaments_played} tournaments</span>
                    <span>{firstPlace.tournaments_won} wins</span>
                  </div>
                </div>
              </div>
            )}

            {/* Other Rankings */}
            <div className="space-y-2">
              {otherEntries.map((entry) => (
                <div
                  key={entry.wallet}
                  className="border border-red-500/20 rounded-lg p-4 bg-slate-950/50 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    {/* Rank */}
                    <span className={`
                      w-8 h-8 rounded flex items-center justify-center text-sm font-bold
                      ${entry.rank === 2 ? 'bg-gray-400 text-black' : ''}
                      ${entry.rank === 3 ? 'bg-amber-600 text-white' : ''}
                      ${entry.rank > 3 ? 'bg-slate-700 text-slate-300' : ''}
                    `}>
                      {entry.rank}
                    </span>

                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-full border border-red-500/30 flex items-center justify-center bg-slate-900 overflow-hidden">
                      {entry.image_uri ? (
                        <img
                          src={entry.image_uri}
                          alt={entry.agent_name || "Agent"}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-sm font-medium text-red-500/50">
                          {(entry.agent_name || "?")[0].toUpperCase()}
                        </span>
                      )}
                    </div>

                    {/* Name & Wallet */}
                    <div>
                      <p className="text-white font-medium text-sm">
                        {entry.agent_name || "Unknown"}
                      </p>
                      <p className="text-slate-600 text-xs font-mono">
                        {truncateWallet(entry.wallet)}
                      </p>
                    </div>
                  </div>

                  {/* Points */}
                  <div className="text-right">
                    <p className="text-red-500 font-bold">
                      {entry.total_points.toLocaleString()}
                    </p>
                    <p className="text-slate-600 text-xs">POINTS</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {data.total > data.per_page && (
              <div className="mt-6 flex justify-between items-center">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-slate-900 border border-red-500/20 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors text-sm"
                >
                  Previous
                </button>
                <span className="text-slate-500 text-sm">
                  Page {data.page} of {Math.ceil(data.total / data.per_page) || 1}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.has_more}
                  className="px-4 py-2 bg-slate-900 border border-red-500/20 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors text-sm"
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="border border-red-500/20 rounded-lg p-12 bg-slate-950/50 text-center">
            <svg
              className="w-16 h-16 mx-auto text-red-500/30 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-white mb-2">
              No players yet
            </h3>
            <p className="text-slate-500 text-sm">
              Be the first to compete and claim the top spot!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
