"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useWallet } from "@solana/wallet-adapter-react";
import { useTournament } from "@/hooks/useTournament";
import { useWalletStore } from "@/stores/walletStore";
import { api, RegistrationRequest } from "@/lib/api";

type Tier = "free" | "basic" | "pro";

const TIER_INFO = {
  free: { name: "FREE", cost: "0 SOL", features: ["Base AI Engine"] },
  basic: {
    name: "BASIC",
    cost: "0.1 SOL",
    features: ["Base AI Engine", "Real-Time Slider Controls"],
  },
  pro: {
    name: "PRO",
    cost: "1 SOL",
    features: ["Base AI Engine", "Real-Time Slider Controls", "Custom Strategy Prompt"],
  },
};

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

function getStatusBadge(status: string) {
  switch (status) {
    case "registration":
      return (
        <span className="bg-green-500/20 text-green-400 px-4 py-2 rounded-full">
          Registration Open
        </span>
      );
    case "in_progress":
      return (
        <span className="bg-yellow-500/20 text-yellow-400 px-4 py-2 rounded-full">
          In Progress
        </span>
      );
    case "completed":
      return (
        <span className="bg-slate-500/20 text-slate-400 px-4 py-2 rounded-full">
          Completed
        </span>
      );
    case "created":
      return (
        <span className="bg-blue-500/20 text-blue-400 px-4 py-2 rounded-full">
          Coming Soon
        </span>
      );
    default:
      return null;
  }
}

export default function TournamentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const tournamentId = params.id as string;
  const { connected, signMessage } = useWallet();
  const { isAuthenticated, authenticate, publicKey } = useWalletStore();
  const { tournament, loading, error, refetch } = useTournament(tournamentId);

  // Registration form state
  const [selectedTier, setSelectedTier] = useState<Tier>("free");
  const [agentName, setAgentName] = useState("");
  const [customPrompt, setCustomPrompt] = useState("");
  const [acceptTos, setAcceptTos] = useState(false);
  const [confirmJurisdiction, setConfirmJurisdiction] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);

  const canRegister =
    tournament?.status === "registration" &&
    connected &&
    isAuthenticated &&
    !tournament.user_registered &&
    agentName.trim() &&
    acceptTos &&
    confirmJurisdiction;

  const handleAuthenticate = async () => {
    if (!signMessage) return;
    await authenticate(signMessage);
  };

  const handleRegister = async () => {
    if (!canRegister) return;

    setIsRegistering(true);
    setRegError(null);

    try {
      const request: RegistrationRequest = {
        tier: selectedTier,
        agent: {
          name: agentName.trim(),
          // Note: Sliders are now controlled via live settings during the tournament
          custom_prompt: selectedTier === "pro" ? customPrompt : undefined,
        },
        accept_tos: acceptTos,
        confirm_jurisdiction: confirmJurisdiction,
        // In production, this would include the payment signature for paid tiers
        payment_signature: selectedTier !== "free" ? "mock_signature" : undefined,
      };

      await api.tournaments.register(tournamentId, request);
      refetch();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setRegError(message);
    } finally {
      setIsRegistering(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-32 mb-8"></div>
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 h-64"></div>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 h-96"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !tournament) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 text-center">
          <p className="text-red-400 mb-4">{error || "Tournament not found"}</p>
          <Link href="/tournaments" className="text-red-300 underline">
            Back to tournaments
          </Link>
        </div>
      </div>
    );
  }

  const totalPrize = tournament.payout_structure.reduce(
    (sum, p) => sum + p.points,
    0
  );

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <Link
          href="/tournaments"
          className="text-slate-400 hover:text-white transition-colors inline-flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Tournaments
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-8">
          {/* Tournament Header */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  Tournament #{tournament.on_chain_id}
                </h1>
                <p className="text-slate-400">ID: {tournament.id}</p>
              </div>
              {getStatusBadge(tournament.status)}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-slate-400 text-sm">Players</p>
                <p className="text-2xl font-bold text-white">
                  {tournament.registered_players}/{tournament.max_players}
                </p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Starting Stack</p>
                <p className="text-2xl font-bold text-white">
                  {tournament.starting_stack.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Blind Structure</p>
                <p className="text-2xl font-bold text-white">
                  {tournament.blind_structure.name}
                </p>
              </div>
              <div>
                <p className="text-slate-400 text-sm">Prize Pool</p>
                <p className="text-2xl font-bold text-accent-gold">
                  {totalPrize.toLocaleString()} POINTS
                </p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-700">
              <p className="text-slate-400 text-sm">
                Starts: {formatDate(tournament.starts_at)}
              </p>
            </div>

            {tournament.status === "in_progress" && (
              <div className="mt-4">
                <Link
                  href={`/tournaments/${tournament.id}/live`}
                  className="inline-block bg-green-600 text-white font-semibold px-6 py-3 rounded-lg hover:bg-green-500 transition-colors"
                >
                  Watch Live
                </Link>
              </div>
            )}
          </div>

          {/* Blind Structure */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-4">
              Blind Structure
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-left py-2 px-2">Level</th>
                    <th className="text-right py-2 px-2">SB</th>
                    <th className="text-right py-2 px-2">BB</th>
                    <th className="text-right py-2 px-2">Ante</th>
                    <th className="text-right py-2 px-2">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {tournament.blind_structure.levels.slice(0, 8).map((level) => (
                    <tr key={level.level} className="text-white border-b border-slate-700/50">
                      <td className="py-2 px-2">{level.level}</td>
                      <td className="text-right py-2 px-2">{level.small_blind}</td>
                      <td className="text-right py-2 px-2">{level.big_blind}</td>
                      <td className="text-right py-2 px-2">{level.ante || "-"}</td>
                      <td className="text-right py-2 px-2">{level.duration_minutes}m</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tournament.blind_structure.levels.length > 8 && (
                <p className="text-slate-400 text-sm mt-2">
                  + {tournament.blind_structure.levels.length - 8} more levels
                </p>
              )}
            </div>
          </div>

          {/* Payout Structure */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-4">
              Payout Structure
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {tournament.payout_structure.map((payout) => (
                <div
                  key={payout.rank}
                  className="bg-slate-700/50 rounded-lg p-4 text-center"
                >
                  <p className="text-slate-400 text-sm">
                    {payout.rank === 1 ? "1st" : payout.rank === 2 ? "2nd" : payout.rank === 3 ? "3rd" : `${payout.rank}th`}
                  </p>
                  <p className="text-xl font-bold text-accent-gold">
                    {payout.points.toLocaleString()}
                  </p>
                  <p className="text-slate-400 text-xs">POINTS</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar - Registration */}
        <div>
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 sticky top-24">
            {tournament.user_registered ? (
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">
                  You&apos;re Registered!
                </h2>
                <p className="text-slate-400 mb-2">
                  Agent: {tournament.user_agent_name}
                </p>
                <p className="text-slate-400 text-sm">
                  Tier: {tournament.user_tier?.toUpperCase()}
                </p>
              </div>
            ) : tournament.status !== "registration" ? (
              <div className="text-center py-4">
                <p className="text-slate-400">
                  Registration is {tournament.status === "created" ? "not yet open" : "closed"}
                </p>
              </div>
            ) : (
              <>
                <h2 className="text-xl font-semibold text-white mb-4">
                  Join Tournament
                </h2>

                {!connected ? (
                  <p className="text-slate-400 text-center py-4">
                    Connect your wallet to register
                  </p>
                ) : !isAuthenticated ? (
                  <div className="text-center py-4">
                    <p className="text-slate-400 mb-4">
                      Sign a message to authenticate
                    </p>
                    <button
                      onClick={handleAuthenticate}
                      className="bg-accent-gold text-black font-semibold px-6 py-2 rounded-lg hover:bg-yellow-400 transition-colors"
                    >
                      Authenticate
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Tier Selection */}
                    <div>
                      <label className="block text-slate-400 text-sm mb-2">
                        Select Tier
                      </label>
                      <div className="space-y-2">
                        {(["free", "basic", "pro"] as Tier[]).map((tier) => (
                          <button
                            key={tier}
                            onClick={() => setSelectedTier(tier)}
                            className={`w-full text-left p-3 rounded-lg border transition-colors ${
                              selectedTier === tier
                                ? "bg-accent-gold/20 border-accent-gold text-white"
                                : "bg-slate-700/50 border-slate-600 text-slate-300 hover:border-slate-500"
                            }`}
                          >
                            <div className="flex justify-between">
                              <span className="font-medium">{TIER_INFO[tier].name}</span>
                              <span className="text-slate-400">{TIER_INFO[tier].cost}</span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                              {TIER_INFO[tier].features.join(" + ")}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Agent Name */}
                    <div>
                      <label className="block text-slate-400 text-sm mb-2">
                        Agent Name
                      </label>
                      <input
                        type="text"
                        value={agentName}
                        onChange={(e) => setAgentName(e.target.value)}
                        placeholder="My Poker Agent"
                        maxLength={32}
                        className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
                      />
                    </div>

                    {/* Real-Time Controls Note (BASIC and PRO) */}
                    {selectedTier !== "free" && (
                      <div className="bg-slate-700/50 rounded-lg p-3">
                        <p className="text-slate-300 text-sm font-medium mb-1">
                          Real-Time Slider Controls
                        </p>
                        <p className="text-slate-400 text-xs">
                          Adjust your agent&apos;s aggression and tightness during live tournament play.
                          Settings default to balanced (5/10) at tournament start.
                        </p>
                      </div>
                    )}

                    {/* Custom Prompt (PRO only) */}
                    {selectedTier === "pro" && (
                      <div>
                        <label className="block text-slate-400 text-sm mb-2">
                          Custom Strategy Prompt
                        </label>
                        <textarea
                          value={customPrompt}
                          onChange={(e) => setCustomPrompt(e.target.value)}
                          placeholder="Describe your agent's strategy..."
                          maxLength={2000}
                          rows={4}
                          className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none resize-none"
                        />
                        <p className="text-slate-500 text-xs mt-1">
                          {customPrompt.length}/2000 characters
                        </p>
                      </div>
                    )}

                    {/* Legal Checkboxes */}
                    <div className="space-y-2 pt-4 border-t border-slate-700">
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={acceptTos}
                          onChange={(e) => setAcceptTos(e.target.checked)}
                          className="mt-1 accent-accent-gold"
                        />
                        <span className="text-slate-400 text-sm">
                          I accept the Terms of Service
                        </span>
                      </label>
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={confirmJurisdiction}
                          onChange={(e) => setConfirmJurisdiction(e.target.checked)}
                          className="mt-1 accent-accent-gold"
                        />
                        <span className="text-slate-400 text-sm">
                          I confirm I am not in a restricted jurisdiction
                        </span>
                      </label>
                    </div>

                    {regError && (
                      <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                        <p className="text-red-400 text-sm">{regError}</p>
                      </div>
                    )}

                    <button
                      onClick={handleRegister}
                      disabled={!canRegister || isRegistering}
                      className="w-full bg-accent-gold text-black font-semibold py-3 rounded-lg hover:bg-yellow-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isRegistering ? "Registering..." : "Register Agent"}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
