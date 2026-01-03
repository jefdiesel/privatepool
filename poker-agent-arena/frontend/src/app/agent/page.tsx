"use client";

import { useState, useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useWalletStore } from "@/stores/walletStore";
import { AgentSliders } from "@/lib/api";

function SliderInput({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-white">{value}</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="w-full accent-accent-gold disabled:opacity-50"
      />
    </div>
  );
}

export default function AgentPage() {
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
  } = useWalletStore();

  const [name, setName] = useState("");
  const [imageUri, setImageUri] = useState("");
  const [sliders, setSliders] = useState<AgentSliders>({
    aggression: 50,
    bluff_frequency: 30,
    tightness: 50,
    position_awareness: 70,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

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
      setImageUri(agentConfig.image_uri || "");
      if (agentConfig.sliders) {
        setSliders(agentConfig.sliders);
      }
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
        image_uri: imageUri || undefined,
        sliders,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled by store
    } finally {
      setIsSaving(false);
    }
  };

  if (!connected) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto text-center">
          <h1 className="text-3xl font-bold text-white mb-4">My Agent</h1>
          <p className="text-slate-400 mb-8">
            Connect your wallet to view and configure your agent.
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
          <h1 className="text-3xl font-bold text-white mb-4">My Agent</h1>
          <p className="text-slate-400 mb-8">
            Sign a message to authenticate and access your agent configuration.
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

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold text-white mb-8">My Agent</h1>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Agent Configuration */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            Agent Configuration
          </h2>

          {!agentConfig ? (
            <div className="text-center py-8">
              <p className="text-slate-400 mb-4">
                No agent configuration found.
              </p>
              <p className="text-slate-500 text-sm">
                Register for a tournament to create your first agent.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">
                  Agent Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Poker Agent"
                  maxLength={32}
                  className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
                />
              </div>

              {/* Avatar */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">
                  Avatar URL
                </label>
                <input
                  type="text"
                  value={imageUri}
                  onChange={(e) => setImageUri(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-accent-gold focus:outline-none"
                />
              </div>

              {/* Sliders */}
              <div className="pt-4 border-t border-slate-700">
                <h3 className="text-lg font-medium text-white mb-4">
                  Strategy Sliders
                  <span className="text-slate-400 text-sm ml-2">
                    (BASIC & PRO tiers)
                  </span>
                </h3>

                <div className="space-y-4">
                  <SliderInput
                    label="Aggression"
                    value={sliders.aggression}
                    onChange={(v) => setSliders({ ...sliders, aggression: v })}
                  />
                  <SliderInput
                    label="Bluff Frequency"
                    value={sliders.bluff_frequency}
                    onChange={(v) => setSliders({ ...sliders, bluff_frequency: v })}
                  />
                  <SliderInput
                    label="Tightness"
                    value={sliders.tightness}
                    onChange={(v) => setSliders({ ...sliders, tightness: v })}
                  />
                  <SliderInput
                    label="Position Awareness"
                    value={sliders.position_awareness}
                    onChange={(v) => setSliders({ ...sliders, position_awareness: v })}
                  />
                </div>
              </div>

              {/* Custom Prompt note */}
              <div className="pt-4 border-t border-slate-700">
                <p className="text-slate-400 text-sm">
                  Custom strategy prompts can only be set during tournament
                  registration (PRO tier).
                </p>
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              {saveSuccess && (
                <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                  <p className="text-green-400 text-sm">Configuration saved!</p>
                </div>
              )}

              <button
                onClick={handleSave}
                disabled={isSaving}
                className="w-full bg-felt text-white font-semibold py-3 rounded-lg hover:bg-felt-light transition-colors disabled:opacity-50"
              >
                {isSaving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="space-y-8">
          {/* Lifetime Stats */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-6">
              Lifetime Stats
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Tournaments</p>
                <p className="text-2xl font-bold text-white">
                  {profile?.tournaments_played ?? 0}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Wins</p>
                <p className="text-2xl font-bold text-white">
                  {profile?.tournaments_won ?? 0}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Total POINTS</p>
                <p className="text-2xl font-bold text-accent-gold">
                  {(profile?.total_points ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">Best Finish</p>
                <p className="text-2xl font-bold text-white">
                  {profile?.best_finish
                    ? profile.best_finish === 1
                      ? "1st"
                      : profile.best_finish === 2
                      ? "2nd"
                      : profile.best_finish === 3
                      ? "3rd"
                      : `${profile.best_finish}th`
                    : "-"}
                </p>
              </div>
            </div>
          </div>

          {/* Tier Info */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-6">
              Current Tier
            </h2>

            <div className="text-center py-4">
              <span className="inline-block px-4 py-2 bg-accent-gold/20 text-accent-gold rounded-full font-semibold text-lg">
                {profile?.agent_tier?.toUpperCase() || "FREE"}
              </span>
              <p className="text-slate-400 text-sm mt-4">
                Tier is set per tournament registration
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
