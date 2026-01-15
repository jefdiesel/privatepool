"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useOnboardingStore } from "@/stores/onboardingStore";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useWalletStore } from "@/stores/walletStore";

export default function AgentSetup() {
  const router = useRouter();
  const { connected, publicKey, signMessage } = useWallet();
  const { authenticate, isAuthenticated, isAuthenticating, updateAgentConfig, error } = useWalletStore();
  const {
    hasAgreedToTOS,
    selectedTier,
    agentName,
    setAgentName,
    completeOnboarding,
    setCurrentStep,
    isOnboardingComplete,
  } = useOnboardingStore();

  const [mounted, setMounted] = useState(false);
  const [localName, setLocalName] = useState(agentName || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    setCurrentStep('agent');
  }, [setCurrentStep]);

  useEffect(() => {
    if (mounted) {
      if (isOnboardingComplete) {
        router.push('/tournaments');
      } else if (!hasAgreedToTOS) {
        router.push('/onboarding');
      } else if (!selectedTier) {
        router.push('/onboarding/tier');
      }
    }
  }, [mounted, hasAgreedToTOS, selectedTier, isOnboardingComplete, router]);

  const handleAuthenticate = async () => {
    if (!signMessage) return;
    await authenticate(signMessage);
  };

  const handleContinue = async () => {
    if (!localName.trim()) {
      setSubmitError("Please enter an agent name");
      return;
    }

    if (!connected || !publicKey) {
      setSubmitError("Please connect your wallet first");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Authenticate if not already
      if (!isAuthenticated && signMessage) {
        const success = await authenticate(signMessage);
        if (!success) {
          setSubmitError("Failed to authenticate wallet");
          setIsSubmitting(false);
          return;
        }
      }

      // Update agent config with name
      await updateAgentConfig({ agent_name: localName.trim() });

      // Save to onboarding store and complete
      setAgentName(localName.trim());
      completeOnboarding();

      // Navigate to tournaments
      router.push('/tournaments');
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to save agent");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!mounted || !hasAgreedToTOS || !selectedTier) return null;

  return (
    <div className="min-h-screen bg-black">
      {/* Header with Navigation */}
      <div className="border-b border-red-500/20 bg-black/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.push("/onboarding/tier")}
              className="text-red-500 hover:text-red-400 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Back
            </button>

            {/* Tab Navigation */}
            <div className="flex items-center gap-4 text-sm">
              <span className="text-slate-600">TOURNAMENTS</span>
              <span className="text-red-500 font-medium">MY AGENT</span>
              <span className="text-slate-600">LEADERBOARD</span>
            </div>

            <div className="w-16" />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-white text-center mb-8">MY AGENT</h1>

          {/* Avatar Placeholder */}
          <div className="flex justify-center mb-8">
            <div className="w-32 h-32 rounded-full border-2 border-dashed border-red-500/50 flex items-center justify-center bg-slate-900/50">
              <div className="text-center">
                <svg className="w-8 h-8 text-red-500/50 mx-auto mb-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="8" r="4" />
                  <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
                </svg>
                <span className="text-red-500/50 text-xs">upload agent<br />pic</span>
              </div>
            </div>
          </div>

          {/* Agent Name Input */}
          <div className="mb-8">
            <label className="block text-slate-400 text-sm mb-2">agent name:</label>
            <input
              type="text"
              value={localName}
              onChange={(e) => setLocalName(e.target.value)}
              placeholder="Enter your agent's name"
              maxLength={32}
              className="w-full bg-slate-900 border border-red-500/30 rounded px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
            />
          </div>

          {/* Wallet Connection */}
          {!connected ? (
            <div className="mb-6">
              <p className="text-slate-400 text-sm text-center mb-3">Connect your wallet to continue</p>
              <div className="flex justify-center">
                <WalletMultiButton className="!bg-red-500 hover:!bg-red-600 !rounded !py-2 !px-6" />
              </div>
            </div>
          ) : !isAuthenticated ? (
            <div className="mb-6">
              <p className="text-slate-400 text-sm text-center mb-3">Sign message to authenticate</p>
              <div className="flex justify-center">
                <button
                  onClick={handleAuthenticate}
                  disabled={isAuthenticating}
                  className="bg-red-500 hover:bg-red-600 text-white font-semibold px-6 py-2 rounded transition-colors disabled:opacity-50"
                >
                  {isAuthenticating ? "Signing..." : "Sign to Authenticate"}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-green-500 text-sm text-center mb-6">
              ✓ Wallet connected: {publicKey?.toString().slice(0, 8)}...
            </p>
          )}

          {/* Error Display */}
          {(submitError || error) && (
            <p className="text-red-400 text-sm text-center mb-4">
              {submitError || error}
            </p>
          )}

          {/* Continue Button */}
          <div className="text-center">
            <button
              onClick={handleContinue}
              disabled={!localName.trim() || !connected || isSubmitting}
              className={`
                px-8 py-3 rounded font-semibold transition-all duration-200
                ${localName.trim() && connected && !isSubmitting
                  ? 'bg-red-500 hover:bg-red-600 text-white cursor-pointer'
                  : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                }
              `}
            >
              {isSubmitting ? 'Saving...' : 'continue'}
            </button>
          </div>

          {/* Tier Display */}
          <div className="mt-8 text-center">
            <span className={`
              px-3 py-1 text-xs font-bold rounded-full
              ${selectedTier === 'FREE' ? 'bg-slate-700 text-slate-300' : ''}
              ${selectedTier === 'BASIC' ? 'bg-red-500 text-white' : ''}
              ${selectedTier === 'PRO' ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white' : ''}
            `}>
              {selectedTier} TIER SELECTED
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
