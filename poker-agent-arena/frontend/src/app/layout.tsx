import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Poker Agent Arena",
  description: "AI Poker Tournament Platform on Solana",
  keywords: ["poker", "ai", "solana", "tournament", "blockchain"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">
        <Providers>
          <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
              <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">&#127183;</span>
                  <span className="text-xl font-bold text-white">
                    Poker Agent Arena
                  </span>
                </div>
                <nav className="hidden md:flex items-center gap-6">
                  <a
                    href="/tournaments"
                    className="text-slate-300 hover:text-white transition-colors"
                  >
                    Tournaments
                  </a>
                  <a
                    href="/leaderboard"
                    className="text-slate-300 hover:text-white transition-colors"
                  >
                    Leaderboard
                  </a>
                  <a
                    href="/agent"
                    className="text-slate-300 hover:text-white transition-colors"
                  >
                    My Agent
                  </a>
                </nav>
                <div id="wallet-button" />
              </div>
            </header>

            {/* Main content */}
            <main className="flex-1">{children}</main>

            {/* Footer */}
            <footer className="border-t border-slate-800 bg-slate-900/50 py-8">
              <div className="container mx-auto px-4 text-center text-slate-400 text-sm">
                <p>Poker Agent Arena - AI Poker Tournaments on Solana</p>
                <p className="mt-2">
                  Built with Next.js, Anchor, and Claude AI
                </p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
