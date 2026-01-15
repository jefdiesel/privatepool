"use client";

import { usePathname } from "next/navigation";
import { useOnboardingStore } from "@/stores/onboardingStore";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useEffect, useState } from "react";
import Link from "next/link";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const { isOnboardingComplete } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Onboarding pages - no shell
  const isOnboardingPage = pathname.startsWith("/onboarding");

  // Admin page has its own layout
  const isAdminPage = pathname.startsWith("/admin");

  // Live tournament has its own layout
  const isLivePage = pathname.includes("/live");

  // Show minimal shell during onboarding
  if (isOnboardingPage) {
    return <>{children}</>;
  }

  // Main app shell with navigation
  return (
    <div className="min-h-screen flex flex-col bg-black">
      {/* Header */}
      <header className="border-b border-red-500/20 bg-black/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          {/* Logo */}
          <Link href="/tournaments" className="flex items-center gap-2">
            <img
              src="/logo.png"
              alt="FAP"
              className="h-8 w-auto"
              onError={(e) => {
                // Fallback if logo not found
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            <span className="text-lg font-bold text-red-500 hidden sm:inline">
              FREEAGENTPOKER
            </span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-4 md:gap-6">
            <Link
              href="/tournaments"
              className={`text-sm transition-colors ${
                pathname === "/tournaments" || pathname.startsWith("/tournaments/")
                  ? "text-red-500 font-medium"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              TOURNAMENTS
            </Link>
            <Link
              href="/agent"
              className={`text-sm transition-colors ${
                pathname === "/agent"
                  ? "text-red-500 font-medium"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              MY AGENT
            </Link>
            <Link
              href="/leaderboard"
              className={`text-sm transition-colors ${
                pathname === "/leaderboard"
                  ? "text-red-500 font-medium"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              LEADERBOARD
            </Link>
          </nav>

          {/* Wallet */}
          {mounted && (
            <div className="hidden sm:block">
              <WalletMultiButton className="!bg-red-500 hover:!bg-red-600 !rounded !py-2 !px-4 !text-sm !h-auto" />
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-red-500/10 bg-black py-6">
        <div className="container mx-auto px-4 text-center text-slate-600 text-xs">
          <p>FREEAGENTPOKER™ - AI Poker Tournaments on Solana</p>
        </div>
      </footer>
    </div>
  );
}
