"use client";

import { useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useEffect, useState } from "react";

interface WalletButtonProps {
  className?: string;
}

export function WalletButton({ className = "" }: WalletButtonProps) {
  const { connected, publicKey, disconnect } = useWallet();
  const [mounted, setMounted] = useState(false);

  // Handle hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button
        className={`bg-felt text-white px-4 py-2 rounded-lg ${className}`}
        disabled
      >
        Loading...
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <WalletMultiButton
        className={`!bg-felt hover:!bg-felt-light !rounded-lg !transition-colors ${className}`}
      />
      {connected && publicKey && (
        <button
          onClick={disconnect}
          className="text-slate-400 hover:text-white text-sm transition-colors"
          title="Disconnect wallet"
        >
          &#10005;
        </button>
      )}
    </div>
  );
}

export function WalletAddress() {
  const { publicKey } = useWallet();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !publicKey) {
    return null;
  }

  const address = publicKey.toString();
  const shortened = `${address.slice(0, 4)}...${address.slice(-4)}`;

  return (
    <span
      className="text-slate-400 text-sm font-mono"
      title={address}
    >
      {shortened}
    </span>
  );
}
