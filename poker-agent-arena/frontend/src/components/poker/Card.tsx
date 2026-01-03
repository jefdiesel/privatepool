/**
 * Playing card component
 */

interface CardProps {
  card: string; // e.g., "Ah", "Kd", "7c", "2s"
  size?: "sm" | "md" | "lg";
  faceDown?: boolean;
}

const SUITS: Record<string, { symbol: string; color: string }> = {
  h: { symbol: "\u2665", color: "text-red-500" },
  d: { symbol: "\u2666", color: "text-red-500" },
  c: { symbol: "\u2663", color: "text-slate-900" },
  s: { symbol: "\u2660", color: "text-slate-900" },
};

const RANKS: Record<string, string> = {
  A: "A",
  K: "K",
  Q: "Q",
  J: "J",
  T: "10",
  "9": "9",
  "8": "8",
  "7": "7",
  "6": "6",
  "5": "5",
  "4": "4",
  "3": "3",
  "2": "2",
};

const SIZES = {
  sm: "w-8 h-12 text-xs",
  md: "w-12 h-16 text-sm",
  lg: "w-16 h-22 text-base",
};

export function Card({ card, size = "md", faceDown = false }: CardProps) {
  const sizeClass = SIZES[size];

  if (faceDown || !card) {
    return (
      <div
        className={`${sizeClass} bg-gradient-to-br from-blue-800 to-blue-900 rounded-lg border-2 border-blue-700 flex items-center justify-center`}
      >
        <div className="w-3/4 h-3/4 border border-blue-600 rounded opacity-50" />
      </div>
    );
  }

  const rank = card[0];
  const suit = card[1]?.toLowerCase();
  const suitInfo = SUITS[suit] || SUITS.s;
  const displayRank = RANKS[rank] || rank;

  return (
    <div
      className={`${sizeClass} bg-white rounded-lg border border-slate-300 shadow-sm flex flex-col items-center justify-center font-bold`}
    >
      <span className={suitInfo.color}>{displayRank}</span>
      <span className={`${suitInfo.color} text-lg`}>{suitInfo.symbol}</span>
    </div>
  );
}

export function CardBack({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  return <Card card="" size={size} faceDown />;
}
