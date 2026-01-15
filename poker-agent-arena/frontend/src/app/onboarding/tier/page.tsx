"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useOnboardingStore, AgentTier } from "@/stores/onboardingStore";

interface TierCardProps {
  tier: AgentTier;
  name: string;
  price: string;
  features: { text: string; included: boolean }[];
  selected: boolean;
  onSelect: () => void;
}

function TierCard({ tier, name, price, features, selected, onSelect }: TierCardProps) {
  return (
    <div
      onClick={onSelect}
      className={`
        relative cursor-pointer transition-all duration-300
        border rounded-lg p-6 flex flex-col
        ${selected
          ? 'border-red-500 bg-red-500/10 scale-105'
          : 'border-slate-700 bg-slate-900/50 hover:border-red-500/50 hover:bg-slate-900/80'
        }
      `}
    >
      {/* Tier Badge */}
      <div className={`
        absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 text-xs font-bold rounded-full
        ${tier === 'FREE' ? 'bg-slate-700 text-slate-300' : ''}
        ${tier === 'BASIC' ? 'bg-red-500 text-white' : ''}
        ${tier === 'PRO' ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white' : ''}
      `}>
        {tier}
      </div>

      {/* Name */}
      <h3 className="text-white text-lg font-semibold mt-4 text-center">{name}</h3>

      {/* Price */}
      <p className="text-2xl font-bold text-red-500 mt-2 text-center">{price}</p>

      {/* Features */}
      <ul className="mt-6 space-y-3 flex-1">
        {features.map((feature, index) => (
          <li
            key={index}
            className={`flex items-start gap-2 text-sm ${feature.included ? 'text-slate-300' : 'text-slate-600'}`}
          >
            <span className={feature.included ? 'text-green-500' : 'text-slate-600'}>
              {feature.included ? '✓' : '✗'}
            </span>
            {feature.text}
          </li>
        ))}
      </ul>

      {/* Selection Indicator */}
      {selected && (
        <div className="mt-4 text-center">
          <span className="text-red-500 text-sm font-medium">Selected</span>
        </div>
      )}
    </div>
  );
}

const TIERS: { tier: AgentTier; name: string; price: string; features: { text: string; included: boolean }[] }[] = [
  {
    tier: 'FREE',
    name: 'good boy bot',
    price: 'FREE',
    features: [
      { text: 'completely free', included: true },
      { text: 'basic poker skills/strategy', included: true },
      { text: 'not real bright jr.', included: true },
      { text: 'great starter for the ride', included: true },
      { text: 'gets outdone like a dog', included: true },
      { text: 'real-time slider controls', included: false },
      { text: 'custom strategy prompt', included: false },
    ],
  },
  {
    tier: 'BASIC',
    name: 'heart crush bot',
    price: '0.1 SOL',
    features: [
      { text: 'unlock real-time adjustments', included: true },
      { text: 'tell the player', included: true },
      { text: 'just dropped', included: true },
      { text: 'flashiest finisher', included: true },
      { text: 'custom strategy prompt', included: false },
      { text: 'priority tournament seeding', included: false },
    ],
  },
  {
    tier: 'PRO',
    name: 'expensive ables',
    price: '1 SOL',
    features: [
      { text: 'custom only frees', included: true },
      { text: 'control the prompt', included: true },
      { text: 'words to heart betting', included: true },
      { text: 'hacked all NFT fixed', included: true },
      { text: 'beyond goal all i know', included: true },
      { text: 'domination mode', included: true },
    ],
  },
];

export default function TierSelection() {
  const router = useRouter();
  const { hasAgreedToTOS, selectedTier, selectTier, setCurrentStep, isOnboardingComplete } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);
  const [localSelection, setLocalSelection] = useState<AgentTier | null>(null);

  useEffect(() => {
    setMounted(true);
    setCurrentStep('tier');
  }, [setCurrentStep]);

  useEffect(() => {
    if (mounted) {
      if (isOnboardingComplete) {
        router.push('/tournaments');
      } else if (!hasAgreedToTOS) {
        router.push('/onboarding');
      }
    }
  }, [mounted, hasAgreedToTOS, isOnboardingComplete, router]);

  useEffect(() => {
    if (selectedTier) {
      setLocalSelection(selectedTier);
    }
  }, [selectedTier]);

  const handleContinue = () => {
    if (localSelection) {
      selectTier(localSelection);
      router.push('/onboarding/agent');
    }
  };

  if (!mounted || !hasAgreedToTOS) return null;

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-red-500/20 bg-black/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => router.push("/onboarding")}
            className="text-red-500 hover:text-red-400 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <h1 className="text-red-500 font-bold text-lg">BOT CREATION</h1>
          <div className="w-16" />
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Choose Your Bot Tier</h2>
          <p className="text-slate-400">Select a tier to determine your agent's capabilities</p>
        </div>

        {/* Tier Cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {TIERS.map((tierData) => (
            <TierCard
              key={tierData.tier}
              {...tierData}
              selected={localSelection === tierData.tier}
              onSelect={() => setLocalSelection(tierData.tier)}
            />
          ))}
        </div>

        {/* Continue Button */}
        <div className="mt-12 text-center">
          <button
            onClick={handleContinue}
            disabled={!localSelection}
            className={`
              px-8 py-3 rounded font-semibold transition-all duration-200
              ${localSelection
                ? 'bg-red-500 hover:bg-red-600 text-white cursor-pointer'
                : 'bg-slate-700 text-slate-500 cursor-not-allowed'
              }
            `}
          >
            continue
          </button>
        </div>
      </div>
    </div>
  );
}
