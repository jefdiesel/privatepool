"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useOnboardingStore, AgentTier } from "@/stores/onboardingStore";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";

interface TierUpgradeCardProps {
  tier: AgentTier;
  name: string;
  price: string;
  features: string[];
  currentTier: AgentTier;
  onSelect: () => void;
}

function TierUpgradeCard({ tier, name, price, features, currentTier, onSelect }: TierUpgradeCardProps) {
  const isCurrent = tier === currentTier;
  const isUpgrade = (
    (currentTier === 'FREE' && (tier === 'BASIC' || tier === 'PRO')) ||
    (currentTier === 'BASIC' && tier === 'PRO')
  );
  const isDowngrade = (
    (currentTier === 'PRO' && (tier === 'BASIC' || tier === 'FREE')) ||
    (currentTier === 'BASIC' && tier === 'FREE')
  );

  return (
    <div className={`
      relative border rounded-lg p-6 transition-all duration-300
      ${isCurrent
        ? 'border-green-500/50 bg-green-500/5'
        : isUpgrade
          ? 'border-red-500/30 bg-slate-900/50 hover:border-red-500 hover:bg-slate-900/80 cursor-pointer'
          : 'border-slate-700/30 bg-slate-900/30 opacity-50'
      }
    `}
    onClick={isUpgrade ? onSelect : undefined}
    >
      {/* Current Badge */}
      {isCurrent && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold rounded-full bg-green-500 text-white">
          CURRENT
        </div>
      )}

      {/* Tier Badge */}
      <div className={`
        inline-block px-3 py-1 text-xs font-bold rounded-full mb-4
        ${tier === 'FREE' ? 'bg-slate-700 text-slate-300' : ''}
        ${tier === 'BASIC' ? 'bg-red-500 text-white' : ''}
        ${tier === 'PRO' ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white' : ''}
      `}>
        {tier}
      </div>

      {/* Name */}
      <h3 className="text-white text-lg font-semibold">{name}</h3>

      {/* Price */}
      <p className="text-2xl font-bold text-red-500 mt-2">{price}</p>

      {/* Features */}
      <ul className="mt-4 space-y-2">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-slate-400">
            <span className="text-green-500">✓</span>
            {feature}
          </li>
        ))}
      </ul>

      {/* Action */}
      <div className="mt-6">
        {isCurrent ? (
          <span className="text-green-500 text-sm">Your current tier</span>
        ) : isUpgrade ? (
          <span className="text-red-500 text-sm font-medium">Click to upgrade →</span>
        ) : isDowngrade ? (
          <span className="text-slate-500 text-sm">Downgrade not available</span>
        ) : null}
      </div>
    </div>
  );
}

const TIERS_DATA: { tier: AgentTier; name: string; price: string; features: string[] }[] = [
  {
    tier: 'FREE',
    name: 'good boy bot',
    price: 'FREE',
    features: [
      'Basic poker AI',
      'Tournament access',
      'Leaderboard tracking',
    ],
  },
  {
    tier: 'BASIC',
    name: 'heart crush bot',
    price: '0.1 SOL',
    features: [
      'Everything in FREE',
      'Real-time slider controls',
      'Aggression & tightness tuning',
    ],
  },
  {
    tier: 'PRO',
    name: 'expensive ables',
    price: '1 SOL',
    features: [
      'Everything in BASIC',
      'Custom strategy prompt',
      'Maximum AI customization',
    ],
  },
];

export default function UpgradePage() {
  const router = useRouter();
  const { connected, publicKey } = useWallet();
  const { isOnboardingComplete, selectedTier, selectTier } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [selectedUpgrade, setSelectedUpgrade] = useState<AgentTier | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isOnboardingComplete) {
      router.push('/onboarding');
    }
  }, [mounted, isOnboardingComplete, router]);

  const currentTier = selectedTier || 'FREE';

  const handleUpgrade = async (tier: AgentTier) => {
    setSelectedUpgrade(tier);
    setUpgrading(true);

    // TODO: Implement actual payment/upgrade logic
    // For now, just update the store
    setTimeout(() => {
      selectTier(tier);
      setUpgrading(false);
      setSelectedUpgrade(null);
      router.push('/agent');
    }, 1500);
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-red-500/20 bg-black/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => router.push("/agent")}
            className="text-red-500 hover:text-red-400 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <h1 className="text-red-500 font-bold text-lg">UPGRADE AGENT</h1>
          <div className="w-16" />
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Intro */}
          <div className="text-center mb-8">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Upgrade Your Agent</h2>
            <p className="text-slate-400">
              Unlock more features and customize your poker AI
            </p>
          </div>

          {/* Wallet Connection Check */}
          {!connected && (
            <div className="text-center mb-8 p-6 border border-red-500/20 rounded-lg bg-slate-950/50">
              <p className="text-slate-400 mb-4">Connect your wallet to upgrade</p>
              <WalletMultiButton className="!bg-red-500 hover:!bg-red-600 !rounded" />
            </div>
          )}

          {/* Tier Cards */}
          <div className="grid md:grid-cols-3 gap-6">
            {TIERS_DATA.map((tierData) => (
              <TierUpgradeCard
                key={tierData.tier}
                {...tierData}
                currentTier={currentTier}
                onSelect={() => handleUpgrade(tierData.tier)}
              />
            ))}
          </div>

          {/* Upgrading Modal */}
          {upgrading && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
              <div className="bg-slate-900 border border-red-500/20 rounded-lg p-8 text-center">
                <div className="w-12 h-12 border-2 border-red-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-white font-medium">Upgrading to {selectedUpgrade}...</p>
                <p className="text-slate-400 text-sm mt-2">Please wait</p>
              </div>
            </div>
          )}

          {/* Info Section */}
          <div className="mt-12 border border-red-500/20 rounded-lg p-6 bg-slate-950/50">
            <h3 className="text-white font-medium mb-4">Upgrade Information</h3>
            <div className="space-y-3 text-sm text-slate-400">
              <p>• Upgrades are permanent for the duration of your account</p>
              <p>• Payment is processed via Solana blockchain</p>
              <p>• New features are available immediately after upgrade</p>
              <p>• Real-time controls can be adjusted during live tournament play</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
