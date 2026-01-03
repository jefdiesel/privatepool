/**
 * Poker table component with 9 seats
 */

import { TableState, SeatState } from "@/lib/socket";
import { Card } from "./Card";
import { Seat } from "./Seat";

interface PokerTableProps {
  tableState: TableState;
  myWallet?: string;
  actionOnWallet?: string;
  timeRemaining?: number;
}

// Seat positions around an oval table (9-max)
// Positions are percentages from center
const SEAT_POSITIONS = [
  { top: "85%", left: "50%", transform: "translate(-50%, 0)" }, // Seat 0 (bottom center)
  { top: "70%", left: "15%", transform: "translate(-50%, 0)" }, // Seat 1 (bottom left)
  { top: "40%", left: "5%", transform: "translate(-50%, -50%)" }, // Seat 2 (left)
  { top: "10%", left: "15%", transform: "translate(-50%, 0)" }, // Seat 3 (top left)
  { top: "0%", left: "35%", transform: "translate(-50%, 0)" }, // Seat 4 (top)
  { top: "0%", left: "65%", transform: "translate(-50%, 0)" }, // Seat 5 (top)
  { top: "10%", left: "85%", transform: "translate(-50%, 0)" }, // Seat 6 (top right)
  { top: "40%", left: "95%", transform: "translate(-50%, -50%)" }, // Seat 7 (right)
  { top: "70%", left: "85%", transform: "translate(-50%, 0)" }, // Seat 8 (bottom right)
];

export function PokerTable({
  tableState,
  myWallet,
  actionOnWallet,
  timeRemaining,
}: PokerTableProps) {
  // Pad seats array to 9 if needed
  const seats: SeatState[] = [...tableState.seats];
  while (seats.length < 9) {
    seats.push({
      position: seats.length,
      wallet: null,
      agent_name: null,
      agent_image: null,
      stack: 0,
      current_bet: 0,
      status: "empty",
    });
  }

  return (
    <div className="relative w-full max-w-4xl mx-auto aspect-[16/10]">
      {/* Table felt */}
      <div className="absolute inset-[10%] bg-felt rounded-[50%] border-8 border-amber-900 shadow-2xl">
        {/* Inner ring */}
        <div className="absolute inset-4 border-2 border-amber-800/50 rounded-[50%]" />

        {/* Center area */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {/* Pot */}
          <div className="bg-slate-900/80 rounded-full px-6 py-2 mb-4">
            <span className="text-slate-400 text-sm">Pot:</span>
            <span className="text-accent-gold font-bold ml-2 text-lg">
              {tableState.pot.toLocaleString()}
            </span>
          </div>

          {/* Community cards */}
          {tableState.community_cards.length > 0 && (
            <div className="flex gap-2">
              {tableState.community_cards.map((card, i) => (
                <Card key={i} card={card} size="md" />
              ))}
            </div>
          )}

          {/* Betting round indicator */}
          <div className="mt-4">
            <span className="text-slate-300 text-sm uppercase tracking-wider">
              {tableState.betting_round}
            </span>
          </div>
        </div>
      </div>

      {/* Seats */}
      {seats.map((seat, index) => {
        const position = SEAT_POSITIONS[index];
        const isMyAgent = seat.wallet === myWallet;
        const isActionOn = seat.wallet === actionOnWallet;

        return (
          <div
            key={seat.position}
            className="absolute"
            style={{
              top: position.top,
              left: position.left,
              transform: position.transform,
            }}
          >
            <Seat
              seat={seat}
              isMyAgent={isMyAgent}
              isActionOn={isActionOn}
              timeRemaining={isActionOn ? timeRemaining : undefined}
            />
          </div>
        );
      })}
    </div>
  );
}
