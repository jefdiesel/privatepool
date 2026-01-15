"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useWalletStore } from "@/stores/walletStore";
import { useOnboardingStore } from "@/stores/onboardingStore";

export default function AgentPage() {
  const router = useRouter();
  const { connected, signMessage } = useWallet();
  const {
    isAuthenticated,
    authenticate,
    profile,
    agentConfig,
    loadProfile,
    loadAgentConfig,
    updateAgentConfig,
    error,
    clearError,
    isAuthenticating,
  } = useWalletStore();
  const { isOnboardingComplete, selectedTier } = useOnboardingStore();

  const [mounted, setMounted] = useState(false);
  const [name, setName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Redirect to onboarding if not complete
  useEffect(() => {
    if (mounted && !isOnboardingComplete) {
      router.push('/onboarding');
    }
  }, [mounted, isOnboardingComplete, router]);

  // Load data on auth
  useEffect(() => {
    if (isAuthenticated) {
      loadProfile();
      loadAgentConfig();
    }
  }, [isAuthenticated, loadProfile, loadAgentConfig]);

  // Populate form when config loads
  useEffect(() => {
    if (agentConfig) {
      setName(agentConfig.name || "");
    }
  }, [agentConfig]);

  const handleAuthenticate = async () => {
    if (!signMessage) return;
    await authenticate(signMessage);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    clearError();

    try {
      await updateAgentConfig({
        name: name || undefined,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled by store
    } finally {
      setIsSaving(false);
    }
  };

  if (!mounted) return null;

  if (!connected) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-4">MY AGENT</h1>
          <p className="text-slate-400 mb-8">
            Connect your wallet to view and configure your agent.
          </p>
          <WalletMultiButton className="!bg-red-500 hover:!bg-red-600 !rounded-lg" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-4">MY AGENT</h1>
          <p className="text-slate-400 mb-8">
            Sign a message to authenticate and access your agent configuration.
          </p>
          <button
            onClick={handleAuthenticate}
            disabled={isAuthenticating}
            className="bg-red-500 text-white font-semibold px-6 py-3 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
          >
            {isAuthenticating ? "Signing..." : "Authenticate"}
          </button>
        </div>
      </div>
    );
  }

  const displayTier = profile?.agent_tier?.toUpperCase() || selectedTier || "FREE";

  return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto px-4 py-8">
        {/* Agent Profile Card */}
        <div className="max-w-md mx-auto">
          {/* Avatar Section */}
          <div className="border border-red-500/20 rounded-lg p-6 bg-slate-950/50 mb-6">
            <div className="flex flex-col items-center">
              {/* Avatar */}
              <div className="w-24 h-24 rounded-full border-2 border-red-500/50 flex items-center justify-center bg-slate-900 mb-4 overflow-hidden">
                {agentConfig?.image_uri ? (
                  <img
                    src={agentConfig.image_uri}
                    alt="Agent"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg className="w-10 h-10 text-red-500/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
                  </svg>
                )}
              </div>

              {/* Tier Badge */}
              <span className={`
                px-3 py-1 text-xs font-bold rounded-full mb-4
                ${displayTier === 'FREE' ? 'bg-slate-700 text-slate-300' : ''}
                ${displayTier === 'BASIC' ? 'bg-red-500 text-white' : ''}
                ${displayTier === 'PRO' ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white' : ''}
              `}>
                {displayTier}
              </span>

              {/* Upgrade Button */}
              <button
                onClick={() => router.push('/upgrade')}
                className="bg-red-500 hover:bg-red-600 text-white font-medium px-6 py-2 rounded transition-colors text-sm"
              >
                upgrade agent
              </button>
            </div>
          </div>

          {/* Stats List */}
          <div className="border border-red-500/20 rounded-lg p-6 bg-slate-950/50 mb-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 1</span>
                <span className="text-white font-medium">{profile?.tournaments_won ?? 0}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 2</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 3</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 4</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 5</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 6</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-800">
                <span className="text-slate-400 text-sm">wins tip 7</span>
                <span className="text-white font-medium">-</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-slate-400 text-sm">wins tip 8</span>
                <span className="text-white font-medium">-</span>
              </div>
            </div>
          </div>

          {/* Performance Data */}
          <div className="border border-red-500/20 rounded-lg p-6 bg-slate-950/50">
            <h3 className="text-white font-medium mb-4">performance data</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/50 rounded p-3">
                <p className="text-slate-500 text-xs mb-1">Tournaments</p>
                <p className="text-white font-bold text-lg">{profile?.tournaments_played ?? 0}</p>
              </div>
              <div className="bg-slate-900/50 rounded p-3">
                <p className="text-slate-500 text-xs mb-1">Total POINTS</p>
                <p className="text-red-500 font-bold text-lg">{(profile?.total_points ?? 0).toLocaleString()}</p>
              </div>
              <div className="bg-slate-900/50 rounded p-3">
                <p className="text-slate-500 text-xs mb-1">Best Finish</p>
                <p className="text-white font-bold text-lg">
                  {profile?.best_finish
                    ? profile.best_finish === 1 ? "1st"
                    : profile.best_finish === 2 ? "2nd"
                    : profile.best_finish === 3 ? "3rd"
                    : `${profile.best_finish}th`
                    : "-"}
                </p>
              </div>
              <div className="bg-slate-900/50 rounded p-3">
                <p className="text-slate-500 text-xs mb-1">Win Rate</p>
                <p className="text-white font-bold text-lg">
                  {profile?.tournaments_played
                    ? `${Math.round((profile.tournaments_won / profile.tournaments_played) * 100)}%`
                    : "-"}
                </p>
              </div>
            </div>
          </div>

          {/* Agent Name Edit */}
          <div className="border border-red-500/20 rounded-lg p-6 bg-slate-950/50 mt-6">
            <h3 className="text-white font-medium mb-4">agent settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-slate-400 text-sm mb-2">Agent Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter agent name"
                  maxLength={32}
                  className="w-full bg-slate-900 border border-red-500/30 rounded px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                />
              </div>

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              {saveSuccess && (
                <p className="text-green-400 text-sm">Saved!</p>
              )}

              <button
                onClick={handleSave}
                disabled={isSaving}
                className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-2 rounded transition-colors disabled:opacity-50"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
