"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useWallet } from "@solana/wallet-adapter-react";
import { useSocket } from "@/hooks/useSocket";
import { useTournament } from "@/hooks/useTournament";
import { useTournamentStore, LiveSettings } from "@/stores/tournamentStore";
import { useWalletStore } from "@/stores/walletStore";
import { PokerTable } from "@/components/poker/PokerTable";
import SettingsPanel from "@/components/SettingsPanel";
import { TableState } from "@/lib/socket";
import { api } from "@/lib/api";

export default function LiveTournamentPage() {
  const params = useParams();
  const tournamentId = params.id as string;
  const { connected, publicKey } = useWallet();
  const { isAuthenticated } = useWalletStore();
  const { tournament, loading: tournamentLoading } = useTournament(tournamentId);

  const {
    tables,
    myAgent,
    liveSettings,
    blindLevel,
    eliminations,
    setTournament,
    updateTableState,
    setMyAgent,
    setLiveSettings,
    confirmSettings,
    applySettings,
    setBlindLevel,
    addElimination,
    reset,
  } = useTournamentStore();

  const [currentTableId, setCurrentTableId] = useState<string | null>(null);
  const [actionOnWallet, setActionOnWallet] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [notifications, setNotifications] = useState<string[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(true);

  const addNotification = useCallback((message: string) => {
    setNotifications((prev) => [...prev.slice(-4), message]);
    setTimeout(() => {
      setNotifications((prev) => prev.slice(1));
    }, 5000);
  }, []);

  // Socket connection with callbacks
  const { isConnected, error: socketError } = useSocket({
    autoConnect: isAuthenticated,
    tournamentId,
    tableId: currentTableId || undefined,
    callbacks: {
      onTournamentStarted: (event) => {
        addNotification("Tournament has started!");
        // Find my table assignment
        if (publicKey) {
          const myAssignment = event.table_assignments.find(
            (a) => a.wallet === publicKey.toBase58()
          );
          if (myAssignment) {
            setCurrentTableId(myAssignment.table_id);
            setMyAgent({
              tableId: myAssignment.table_id,
              seatPosition: myAssignment.seat,
              stack: tournament?.starting_stack || 10000,
              status: "active",
            });
          }
        }
      },
      onLevelUp: (event) => {
        setBlindLevel(
          event.level,
          event.small_blind,
          event.big_blind,
          event.ante
        );
        addNotification(`Blinds increased to ${event.small_blind}/${event.big_blind}`);
      },
      onTournamentCompleted: () => {
        addNotification("Tournament completed!");
      },
      onPlayerEliminated: (event) => {
        addElimination(event.wallet, event.position, event.eliminator_wallet);
        if (publicKey && event.wallet === publicKey.toBase58()) {
          addNotification(`You finished in ${event.position}${getOrdinal(event.position)} place!`);
          setMyAgent(null);
        } else {
          addNotification(`Player eliminated: #${event.position}`);
        }
      },
      onPlayerMoved: (event) => {
        if (publicKey && event.wallet === publicKey.toBase58()) {
          setCurrentTableId(event.to_table_id);
          setMyAgent({
            tableId: event.to_table_id,
            seatPosition: event.new_seat,
            stack: myAgent?.stack || 0,
            status: "active",
          });
          addNotification("You have been moved to a new table");
        }
      },
      onTableState: (state: TableState) => {
        updateTableState(state.table_id, state);
      },
      onHandDeal: (event) => {
        if (myAgent) {
          setMyAgent({
            ...myAgent,
            holeCards: event.hole_cards,
          });
        }
      },
      onHandAction: (event) => {
        addNotification(
          `${event.wallet.slice(0, 6)}... ${event.action}${event.amount ? ` ${event.amount}` : ""}`
        );
      },
      onDecisionStart: (event) => {
        setActionOnWallet(event.wallet);
        setTimeRemaining(event.timeout_seconds);
      },
      onHandShowdown: (event) => {
        event.winners.forEach((winner) => {
          addNotification(
            `${winner.wallet.slice(0, 6)}... wins ${winner.amount} with ${winner.hand_rank}`
          );
        });
        setActionOnWallet(null);
        setTimeRemaining(null);
      },
      onSettingsConfirmed: (event) => {
        confirmSettings(event.aggression, event.tightness);
        addNotification("Settings confirmed - will apply next hand");
      },
      onSettingsApplied: (event) => {
        applySettings(event.aggression, event.tightness);
        addNotification("New settings are now active");
      },
    },
  });

  // Timer countdown
  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev === null || prev <= 0) {
          clearInterval(interval);
          return null;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeRemaining]);

  // Update tournament in store
  useEffect(() => {
    if (tournament) {
      setTournament(tournament);
    }
    return () => reset();
  }, [tournament, setTournament, reset]);

  // Fetch live settings for BASIC/PRO tier users
  useEffect(() => {
    async function fetchLiveSettings() {
      if (!tournament || !isAuthenticated) {
        setSettingsLoading(false);
        return;
      }

      // Check if user has slider access (BASIC or PRO tier)
      const userTier = tournament.user_tier?.toLowerCase();
      if (!userTier || userTier === "free") {
        setSettingsLoading(false);
        setLiveSettings(null);
        return;
      }

      try {
        const response = await api.liveSettings.get(tournamentId);
        setLiveSettings({
          activeAggression: response.active_aggression,
          activeTightness: response.active_tightness,
          pendingAggression: response.pending_aggression,
          pendingTightness: response.pending_tightness,
          confirmedAggression: response.confirmed_aggression,
          confirmedTightness: response.confirmed_tightness,
          confirmedAt: response.confirmed_at,
        });
      } catch (error) {
        console.error("Failed to fetch live settings:", error);
        // Initialize with defaults if fetch fails but user has access
        setLiveSettings({
          activeAggression: 5,
          activeTightness: 5,
          pendingAggression: null,
          pendingTightness: null,
          confirmedAggression: null,
          confirmedTightness: null,
          confirmedAt: null,
        });
      } finally {
        setSettingsLoading(false);
      }
    }

    fetchLiveSettings();
  }, [tournament, tournamentId, isAuthenticated, setLiveSettings]);

  // Handlers for settings panel
  const handleSettingsUpdate = useCallback(
    async (aggression: number, tightness: number) => {
      await api.liveSettings.update(tournamentId, aggression, tightness);
      // Update local state optimistically
      setLiveSettings(
        liveSettings
          ? {
              ...liveSettings,
              pendingAggression: aggression,
              pendingTightness: tightness,
            }
          : null
      );
    },
    [tournamentId, liveSettings, setLiveSettings]
  );

  const handleSettingsConfirm = useCallback(async () => {
    await api.liveSettings.confirm(tournamentId);
    // The socket event will update the state
  }, [tournamentId]);

  const currentTable = currentTableId ? tables[currentTableId] : null;
  const myWallet = publicKey?.toBase58();

  if (tournamentLoading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-64 mb-8"></div>
          <div className="aspect-[16/10] bg-slate-800/50 rounded-3xl"></div>
        </div>
      </div>
    );
  }

  if (!tournament) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <p className="text-slate-400 mb-4">Tournament not found</p>
        <Link href="/tournaments" className="text-accent-gold hover:underline">
          Back to tournaments
        </Link>
      </div>
    );
  }

  if (tournament.status !== "in_progress") {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h1 className="text-3xl font-bold text-white mb-4">
          Tournament #{tournament.on_chain_id}
        </h1>
        <p className="text-slate-400 mb-4">
          {tournament.status === "completed"
            ? "This tournament has ended."
            : "This tournament has not started yet."}
        </p>
        <Link
          href={`/tournaments/${tournamentId}`}
          className="text-accent-gold hover:underline"
        >
          View tournament details
        </Link>
      </div>
    );
  }

  if (!connected || !isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h1 className="text-3xl font-bold text-white mb-4">Live Tournament</h1>
        <p className="text-slate-400 mb-4">
          Connect your wallet and authenticate to view the live tournament.
        </p>
        <Link
          href={`/tournaments/${tournamentId}`}
          className="text-accent-gold hover:underline"
        >
          Back to tournament
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-3">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link
              href={`/tournaments/${tournamentId}`}
              className="text-slate-400 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <h1 className="text-white font-bold">Tournament #{tournament.on_chain_id}</h1>
              <p className="text-slate-400 text-sm">
                {tournament.registered_players} players
              </p>
            </div>
          </div>

          {/* Connection status */}
          <div className="flex items-center gap-4">
            <span
              className={`flex items-center gap-2 text-sm ${
                isConnected ? "text-green-400" : "text-red-400"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-400" : "bg-red-400"
                }`}
              />
              {isConnected ? "Connected" : "Disconnected"}
            </span>

            {blindLevel && (
              <div className="text-sm">
                <span className="text-slate-400">Blinds:</span>
                <span className="text-white ml-2">
                  {blindLevel.smallBlind}/{blindLevel.bigBlind}
                </span>
                {blindLevel.ante > 0 && (
                  <span className="text-slate-400 ml-1">
                    (ante {blindLevel.ante})
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Main table area */}
          <div className="lg:col-span-3">
            {currentTable ? (
              <PokerTable
                tableState={currentTable}
                myWallet={myWallet}
                actionOnWallet={actionOnWallet || undefined}
                timeRemaining={timeRemaining || undefined}
              />
            ) : (
              <div className="aspect-[16/10] bg-slate-800/50 rounded-3xl flex items-center justify-center">
                <p className="text-slate-400">Waiting for table assignment...</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* My Agent */}
            {myAgent && (
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-semibold mb-2">My Agent</h3>
                <p className="text-accent-gold text-2xl font-bold">
                  {myAgent.stack.toLocaleString()}
                </p>
                <p className="text-slate-400 text-sm">
                  Table: {myAgent.tableId.slice(0, 8)}...
                </p>
                <p className="text-slate-400 text-sm">Seat: {myAgent.seatPosition + 1}</p>
              </div>
            )}

            {/* Live Settings Panel (BASIC/PRO only) */}
            {tournament?.user_tier &&
              tournament.user_tier.toLowerCase() !== "free" &&
              liveSettings && (
                <SettingsPanel
                  settings={liveSettings}
                  tier={tournament.user_tier.toLowerCase() as "basic" | "pro"}
                  isLoading={settingsLoading}
                  onUpdate={handleSettingsUpdate}
                  onConfirm={handleSettingsConfirm}
                />
              )}

            {/* Upgrade prompt for FREE tier */}
            {tournament?.user_tier?.toLowerCase() === "free" && (
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-semibold mb-2">Agent Controls</h3>
                <p className="text-slate-400 text-sm mb-3">
                  Upgrade to 0.1 SOL tier to adjust your agent&apos;s strategy in real-time.
                </p>
                <p className="text-xs text-slate-500">
                  BASIC and PRO tier agents can adjust aggression and tightness during play.
                </p>
              </div>
            )}

            {/* Recent eliminations */}
            {eliminations.length > 0 && (
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-semibold mb-2">Eliminations</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {eliminations.slice(-5).reverse().map((e, i) => (
                    <div key={i} className="text-sm">
                      <span className="text-slate-400">#{e.position}</span>
                      <span className="text-white ml-2">
                        {e.wallet.slice(0, 6)}...
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Notifications */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-semibold mb-2">Activity</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {notifications.length > 0 ? (
                  notifications.map((msg, i) => (
                    <p key={i} className="text-slate-400 text-sm">
                      {msg}
                    </p>
                  ))
                ) : (
                  <p className="text-slate-500 text-sm">No recent activity</p>
                )}
              </div>
            </div>

            {socketError && (
              <div className="bg-red-500/20 rounded-xl p-4 border border-red-500/50">
                <p className="text-red-400 text-sm">{socketError}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function getOrdinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}
