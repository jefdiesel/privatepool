/**
 * Poker table seat component
 */

import { SeatState } from "@/lib/socket";
import { Card, CardBack } from "./Card";

interface SeatProps {
  seat: SeatState;
  isMyAgent?: boolean;
  isActionOn?: boolean;
  timeRemaining?: number;
}

function truncateWallet(wallet: string): string {
  return `${wallet.slice(0, 4)}...${wallet.slice(-3)}`;
}

function getStatusColor(status: string, isActionOn: boolean): string {
  if (isActionOn) return "ring-2 ring-accent-gold";
  switch (status) {
    case "folded":
      return "opacity-50";
    case "all_in":
      return "ring-2 ring-red-500";
    case "eliminated":
      return "opacity-30";
    default:
      return "";
  }
}

export function Seat({ seat, isMyAgent, isActionOn, timeRemaining }: SeatProps) {
  const isEmpty = !seat.wallet;
  const statusClass = !isEmpty ? getStatusColor(seat.status, !!isActionOn) : "";

  return (
    <div className={`relative ${statusClass} rounded-xl transition-all duration-300`}>
      {/* Seat background */}
      <div
        className={`w-32 h-40 rounded-xl flex flex-col items-center justify-center ${
          isEmpty
            ? "bg-slate-800/30 border border-slate-700 border-dashed"
            : isMyAgent
            ? "bg-felt border-2 border-accent-gold"
            : "bg-slate-800 border border-slate-600"
        }`}
      >
        {isEmpty ? (
          <span className="text-slate-500 text-sm">Empty</span>
        ) : (
          <>
            {/* Avatar */}
            <div className="w-12 h-12 bg-slate-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-2">
              {seat.agent_name?.[0]?.toUpperCase() || "?"}
            </div>

            {/* Name */}
            <p className="text-white text-sm font-medium truncate max-w-full px-2">
              {seat.agent_name || truncateWallet(seat.wallet || "")}
            </p>

            {/* Stack */}
            <p className="text-accent-gold text-xs font-mono">
              {seat.stack.toLocaleString()}
            </p>

            {/* Current bet */}
            {seat.current_bet > 0 && (
              <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-slate-900 text-white text-xs px-2 py-1 rounded-full">
                  {seat.current_bet.toLocaleString()}
                </span>
              </div>
            )}

            {/* Hole cards */}
            {seat.hole_cards && seat.hole_cards.length === 2 && (
              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 flex gap-1">
                <Card card={seat.hole_cards[0]} size="sm" />
                <Card card={seat.hole_cards[1]} size="sm" />
              </div>
            )}

            {/* Face-down cards for other players */}
            {!seat.hole_cards && seat.status === "active" && (
              <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 flex gap-1">
                <CardBack size="sm" />
                <CardBack size="sm" />
              </div>
            )}

            {/* Status badge */}
            {seat.status !== "active" && (
              <span
                className={`absolute top-1 right-1 text-xs px-1 py-0.5 rounded ${
                  seat.status === "folded"
                    ? "bg-slate-600 text-slate-300"
                    : seat.status === "all_in"
                    ? "bg-red-600 text-white"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {seat.status === "all_in" ? "ALL IN" : seat.status.toUpperCase()}
              </span>
            )}

            {/* Timer */}
            {isActionOn && timeRemaining !== undefined && (
              <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
                <div className="bg-accent-gold text-black text-xs font-bold px-2 py-1 rounded-full animate-pulse">
                  {timeRemaining}s
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
