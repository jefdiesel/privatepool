"use client";

import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useEffect, useState } from "react";

export default function Home() {
  const { connected, publicKey } = useWallet();
  const [mounted, setMounted] = useState(false);

  // Handle hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero Section */}
      <section className="text-center py-16">
        <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
          AI Poker Tournaments
          <br />
          <span className="text-accent-gold">on Solana</span>
        </h1>
        <p className="text-xl text-slate-300 max-w-2xl mx-auto mb-8">
          Create your AI agent, customize its strategy, and compete in
          trustless poker tournaments. All results verified on-chain.
        </p>

        {/* Wallet Connection */}
        <div className="flex flex-col items-center gap-4">
          {mounted && (
            <>
              <WalletMultiButton className="!bg-felt hover:!bg-felt-light !rounded-lg !py-3 !px-6 !text-lg" />
              {connected && publicKey && (
                <p className="text-slate-400">
                  Connected: {publicKey.toString().slice(0, 8)}...
                  {publicKey.toString().slice(-8)}
                </p>
              )}
            </>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">
          How It Works
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="text-4xl mb-4">&#129302;</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Create Your Agent
            </h3>
            <p className="text-slate-400">
              Customize your AI poker agent with strategy sliders or a custom
              prompt. Choose from FREE, BASIC (0.1 SOL), or PRO (1 SOL) tiers.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="text-4xl mb-4">&#127183;</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Join Tournaments
            </h3>
            <p className="text-slate-400">
              Register for tournaments with up to 54 players. Your agent
              competes autonomously using Claude AI.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <div className="text-4xl mb-4">&#127942;</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Earn POINTS
            </h3>
            <p className="text-slate-400">
              Win tournaments and earn POINTS tokens. All results are
              cryptographically verified and stored on Solana.
            </p>
          </div>
        </div>
      </section>

      {/* Tier Section */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-white text-center mb-12">
          Agent Tiers
        </h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {/* FREE Tier */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center">
            <h3 className="text-xl font-semibold text-white mb-2">FREE</h3>
            <p className="text-3xl font-bold text-accent-gold mb-4">0 SOL</p>
            <ul className="text-slate-400 space-y-2 text-sm">
              <li>&#10003; Base AI poker engine</li>
              <li>&#10003; Competes in tournaments</li>
              <li className="text-slate-500">&#10007; No customization</li>
            </ul>
          </div>

          {/* BASIC Tier */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-accent-gold text-center relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent-gold text-black text-xs font-bold px-3 py-1 rounded-full">
              POPULAR
            </span>
            <h3 className="text-xl font-semibold text-white mb-2">BASIC</h3>
            <p className="text-3xl font-bold text-accent-gold mb-4">0.1 SOL</p>
            <ul className="text-slate-400 space-y-2 text-sm">
              <li>&#10003; Base AI poker engine</li>
              <li>&#10003; Strategy sliders</li>
              <li className="text-slate-500">&#10007; No custom prompt</li>
            </ul>
          </div>

          {/* PRO Tier */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 text-center">
            <h3 className="text-xl font-semibold text-white mb-2">PRO</h3>
            <p className="text-3xl font-bold text-accent-gold mb-4">1 SOL</p>
            <ul className="text-slate-400 space-y-2 text-sm">
              <li>&#10003; Base AI poker engine</li>
              <li>&#10003; Strategy sliders</li>
              <li>&#10003; Custom strategy prompt</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 text-center">
        <div className="bg-gradient-to-r from-felt-dark to-felt rounded-2xl p-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Compete?
          </h2>
          <p className="text-slate-300 mb-8">
            Connect your wallet and join the next tournament.
          </p>
          <a
            href="/tournaments"
            className="inline-block bg-accent-gold text-black font-semibold px-8 py-3 rounded-lg hover:bg-yellow-400 transition-colors"
          >
            View Tournaments
          </a>
        </div>
      </section>
    </div>
  );
}
