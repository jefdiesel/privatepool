"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/stores/onboardingStore";

export default function OnboardingHome() {
  const router = useRouter();
  const { hasAgreedToTOS, isOnboardingComplete, agreeTOS, setCurrentStep } = useOnboardingStore();
  const [tosChecked, setTosChecked] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setCurrentStep('home');
  }, [setCurrentStep]);

  useEffect(() => {
    if (mounted && isOnboardingComplete) {
      router.push('/tournaments');
    }
  }, [mounted, isOnboardingComplete, router]);

  const handleContinue = () => {
    if (tosChecked) {
      agreeTOS();
      router.push('/onboarding/tier');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleContinue();
    }
  };

  if (!mounted) return null;

  return (
    <div
      className="min-h-screen bg-black flex flex-col items-center justify-center relative overflow-hidden cursor-pointer"
      onClick={handleContinue}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* VHS Scanlines Overlay */}
      <div className="absolute inset-0 pointer-events-none vhs-scanlines" />

      {/* VHS Noise Overlay */}
      <div className="absolute inset-0 pointer-events-none vhs-noise opacity-[0.03]" />

      {/* Animated Logo Container */}
      <div className="relative vhs-glitch">
        {/* Main Logo */}
        <div className="relative">
          <img
            src="/logo.png"
            alt="Free Agent Poker"
            className="w-64 md:w-80 lg:w-96 h-auto vhs-color-shift"
          />

          {/* VHS Tracking Lines */}
          <div className="absolute inset-0 vhs-tracking pointer-events-none" />
        </div>
      </div>

      {/* TOS Agreement Checkbox */}
      <div className="mt-12 flex flex-col items-center gap-6 z-10">
        <label
          className="flex items-center gap-3 cursor-pointer group"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="relative">
            <input
              type="checkbox"
              checked={tosChecked}
              onChange={(e) => setTosChecked(e.target.checked)}
              className="sr-only"
            />
            <div className={`w-6 h-6 border-2 ${tosChecked ? 'border-red-500 bg-red-500' : 'border-red-500/50'} transition-all duration-200`}>
              {tosChecked && (
                <svg className="w-full h-full text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </div>
          </div>
          <span className="text-red-500 text-sm md:text-base font-medium">
            I agree to the{" "}
            <a
              href="/onboarding/tos"
              className="underline hover:text-red-400 transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              Terms of Service
            </a>
          </span>
        </label>

        {/* Continue Prompt */}
        <p className={`text-sm transition-all duration-300 ${tosChecked ? 'text-red-500 animate-pulse' : 'text-slate-600'}`}>
          {tosChecked ? 'click anywhere to continue...' : 'accept terms to continue'}
        </p>
      </div>

      {/* VHS Styles */}
      <style jsx>{`
        .vhs-scanlines {
          background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
          );
        }

        .vhs-noise {
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }

        .vhs-glitch {
          animation: vhs-glitch 8s infinite;
        }

        .vhs-color-shift {
          animation: color-shift 4s infinite;
        }

        .vhs-tracking {
          background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255, 255, 255, 0.03) 2px,
            rgba(255, 255, 255, 0.03) 4px
          );
          animation: tracking 0.5s infinite;
        }

        @keyframes vhs-glitch {
          0%, 100% {
            transform: translate(0);
          }
          2% {
            transform: translate(-2px, 1px);
          }
          4% {
            transform: translate(2px, -1px);
          }
          6% {
            transform: translate(0);
          }
          42% {
            transform: translate(0);
          }
          44% {
            transform: translate(-1px, 2px);
          }
          46% {
            transform: translate(1px, -1px);
          }
          48% {
            transform: translate(0);
          }
        }

        @keyframes color-shift {
          0%, 100% {
            filter: hue-rotate(0deg) saturate(1);
          }
          25% {
            filter: hue-rotate(-5deg) saturate(1.1);
          }
          50% {
            filter: hue-rotate(5deg) saturate(0.9);
          }
          75% {
            filter: hue-rotate(-3deg) saturate(1.05);
          }
        }

        @keyframes tracking {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(4px);
          }
        }
      `}</style>
    </div>
  );
}
