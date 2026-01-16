"use client";

import { useEffect } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { useWalletStore } from "@/stores/walletStore";

/**
 * Syncs Solana wallet adapter state with the walletStore.
 * This bridges the gap between the external wallet connection
 * and our internal state management.
 */
export function WalletStateSync() {
  const { connected, publicKey } = useWallet();
  const setConnected = useWalletStore((state) => state.setConnected);

  useEffect(() => {
    // Sync wallet adapter state to our store whenever it changes
    setConnected(connected, publicKey?.toBase58() ?? null);
  }, [connected, publicKey, setConnected]);

  // This component doesn't render anything
  return null;
}
