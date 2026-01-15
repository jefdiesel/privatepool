# Free Agent Poker - Frontend Build Directions for Replit

## Project Overview

**Free Agent Poker (FAP)** is an AI poker tournament platform on Solana. Users create AI poker agents, customize their strategy, and compete in autonomous tournaments. This document provides complete directions for building and deploying the frontend.

---

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Wallet**: Solana Wallet Adapter
- **Real-time**: Socket.IO
- **Package Manager**: npm

---

## Project Structure

```
poker-agent-arena/
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages
│   │   │   ├── page.tsx            # Root redirect
│   │   │   ├── layout.tsx          # Root layout with providers
│   │   │   ├── globals.css         # Global styles
│   │   │   ├── providers.tsx       # Wallet/context providers
│   │   │   ├── onboarding/         # Onboarding flow pages
│   │   │   │   ├── page.tsx        # Home with VHS logo
│   │   │   │   ├── tos/page.tsx    # Terms of Service
│   │   │   │   ├── tier/page.tsx   # Tier selection
│   │   │   │   └── agent/page.tsx  # Agent setup
│   │   │   ├── tournaments/        # Tournament pages
│   │   │   │   ├── page.tsx        # Tournament list
│   │   │   │   └── [id]/           # Dynamic tournament routes
│   │   │   │       ├── page.tsx    # Tournament details
│   │   │   │       └── live/page.tsx # Live tournament view
│   │   │   ├── agent/page.tsx      # My Agent profile
│   │   │   ├── leaderboard/page.tsx # Leaderboard
│   │   │   ├── upgrade/page.tsx    # Upgrade tier
│   │   │   └── admin/page.tsx      # Admin dashboard
│   │   ├── components/             # Reusable components
│   │   │   ├── AppShell.tsx        # Main layout shell
│   │   │   ├── SliderControl.tsx   # Strategy slider
│   │   │   ├── SettingsPanel.tsx   # Live settings panel
│   │   │   ├── poker/              # Poker-specific components
│   │   │   │   ├── PokerTable.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Seat.tsx
│   │   │   └── wallet/
│   │   │       └── WalletButton.tsx
│   │   ├── stores/                 # Zustand state stores
│   │   │   ├── walletStore.ts      # Wallet/auth state
│   │   │   ├── tournamentStore.ts  # Tournament state
│   │   │   └── onboardingStore.ts  # Onboarding flow state
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useTournament.ts
│   │   │   └── useSocket.ts
│   │   └── lib/                    # Utilities
│   │       ├── api.ts              # API client
│   │       └── socket.ts           # Socket.IO client
│   ├── public/
│   │   ├── logo.png                # FAP logo (must be added manually)
│   │   └── terms-of-service.html   # TOS content
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── .replit                         # Replit run configuration
└── replit.nix                      # Nix dependencies
```

---

## User Flow

### 1. Onboarding Flow (First-time users)

```
/ (root) → /onboarding → /onboarding/tier → /onboarding/agent → /tournaments
```

| Step | Page | Description |
|------|------|-------------|
| 1 | `/onboarding` | Landing with VHS-animated logo, TOS checkbox. Click anywhere to continue after accepting. |
| 2 | `/onboarding/tos` | Full Terms of Service (linked from checkbox) |
| 3 | `/onboarding/tier` | Select agent tier: FREE (0 SOL), BASIC (0.1 SOL), or PRO (1 SOL) |
| 4 | `/onboarding/agent` | Enter agent name, connect wallet, authenticate |
| 5 | `/tournaments` | Main app - tournament list |

### 2. Main App Flow (Returning users)

```
/ (root) → /tournaments (if onboarding complete)
```

**Navigation tabs**: TOURNAMENTS | MY AGENT | LEADERBOARD

| Page | Description |
|------|-------------|
| `/tournaments` | Browse and filter tournaments by status |
| `/tournaments/[id]` | Tournament details, registration |
| `/tournaments/[id]/live` | Live tournament view with poker table, real-time slider controls |
| `/agent` | Agent profile, stats, name editing, upgrade button |
| `/leaderboard` | Global rankings with featured 1st place |
| `/upgrade` | Tier upgrade flow |

---

## Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background | `#000000` | Page backgrounds |
| Primary Red | `#EF4444` | Buttons, accents, borders |
| Red Hover | `#DC2626` | Button hover states |
| Text Primary | `#FFFFFF` | Headings, important text |
| Text Secondary | `#94A3B8` | Body text, labels |
| Text Muted | `#475569` | Placeholder, disabled |
| Card Background | `rgba(2,6,23,0.5)` | Card/panel backgrounds |
| Border | `rgba(239,68,68,0.2)` | Card borders |

### Typography

- Font: Inter (system fallback: sans-serif)
- Headings: Bold, uppercase for page titles
- Body: Regular weight

### Component Patterns

**Buttons**:
```css
/* Primary */
bg-red-500 hover:bg-red-600 text-white rounded px-4 py-2

/* Secondary */
bg-slate-900 border border-red-500/20 text-white rounded px-4 py-2
```

**Cards/Panels**:
```css
border border-red-500/20 rounded-lg p-6 bg-slate-950/50
```

**Inputs**:
```css
bg-slate-900 border border-red-500/30 rounded px-4 py-2 text-white
focus:border-red-500 focus:outline-none
```

---

## Key Components

### AppShell (`components/AppShell.tsx`)
- Wraps all pages (except onboarding)
- Header with logo, navigation tabs, wallet button
- Footer with branding

### Onboarding Home (`app/onboarding/page.tsx`)
- VHS-style effects: scanlines, glitch animation, color shift
- Animated logo display
- TOS checkbox with link
- "Click anywhere to continue" prompt

### Tier Selection (`app/onboarding/tier/page.tsx`)
- Three tier cards side by side
- Visual selection state (scale + border highlight)
- Feature lists per tier

### SliderControl (`components/SliderControl.tsx`)
- 1-10 scale slider for aggression/tightness
- Visual distinction between active (green) and pending (amber) values
- Used in live tournament view for BASIC/PRO tiers

### SettingsPanel (`components/SettingsPanel.tsx`)
- Contains both sliders + confirm button
- Shows "changes will take effect next hand" after confirm
- Only visible for BASIC/PRO tier users during live play

### PokerTable (`components/poker/PokerTable.tsx`)
- 9-seat oval table visualization
- Center shows pot, community cards, betting round
- Seats show player status, stack, current bet

---

## State Management

### onboardingStore (Zustand + persist)
```typescript
interface OnboardingState {
  hasAgreedToTOS: boolean;
  selectedTier: 'FREE' | 'BASIC' | 'PRO' | null;
  agentName: string;
  agentImageUrl: string | null;
  isOnboardingComplete: boolean;
  currentStep: 'home' | 'tos' | 'tier' | 'agent' | 'complete';
}
```
- Persisted to localStorage under key `fap-onboarding`
- Used by route guards to redirect incomplete users

### walletStore (Zustand)
```typescript
interface WalletState {
  connected: boolean;
  publicKey: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  sessionToken: string | null;
  profile: UserProfile | null;
  agentConfig: AgentConfig | null;
}
```
- Handles Solana wallet connection
- Message signing for authentication
- JWT token management

### tournamentStore (Zustand)
```typescript
interface TournamentState {
  currentTournament: TournamentDetail | null;
  tables: Record<string, TableState>;
  myAgent: MyAgentInfo | null;
  liveSettings: LiveSettings | null;
  blindLevel: number;
  eliminations: Elimination[];
}
```
- Live tournament data
- Real-time slider settings (active/pending/confirmed)

---

## API Integration

### Base URL
```
Backend API: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/nonce?wallet={wallet}` | Get signing nonce |
| POST | `/api/auth/verify` | Verify signature, get JWT |
| GET | `/api/auth/me` | Get user profile |
| GET | `/api/tournaments` | List tournaments |
| GET | `/api/tournaments/{id}` | Tournament details |
| POST | `/api/tournaments/{id}/register` | Register for tournament |
| GET | `/api/leaderboard` | Get leaderboard |
| GET | `/api/agent` | Get agent config |
| PUT | `/api/agent` | Update agent config |
| GET | `/api/live-settings/{tournamentId}` | Get live slider settings |
| PUT | `/api/live-settings/{tournamentId}` | Update pending settings |
| POST | `/api/live-settings/{tournamentId}/confirm` | Confirm settings |

### Authentication
- Bearer token in Authorization header
- Token stored in sessionStorage
- Auto-refresh on page load if token exists

---

## WebSocket Events

### Connection
```javascript
socket.connect(SOCKET_URL, { auth: { token: sessionToken } });
socket.emit('join:tournament', { tournamentId });
```

### Events to Listen

| Event | Data | Description |
|-------|------|-------------|
| `table:state` | TableState | Full table state update |
| `hand:start` | HandInfo | New hand started |
| `action:request` | ActionRequest | Player action needed |
| `player:action` | PlayerAction | Action taken |
| `hand:result` | HandResult | Hand completed |
| `player:eliminated` | Elimination | Player eliminated |
| `settings:confirmed` | SettingsConfirmed | Settings confirmed |
| `settings:applied` | SettingsApplied | Settings took effect |

---

## Environment Variables

Create these in Replit Secrets:

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_SOCKET_URL` | WebSocket server URL |
| `NEXT_PUBLIC_SOLANA_NETWORK` | `devnet` or `mainnet-beta` |
| `NEXT_PUBLIC_SOLANA_RPC` | Solana RPC endpoint |

---

## Build & Run Commands

### Development
```bash
cd poker-agent-arena/frontend
npm install
npm run dev
```

### Production Build
```bash
cd poker-agent-arena/frontend
npm run build
npm start
```

### Replit Configuration

The `.replit` file is configured to:
1. Install dependencies on first run
2. Build for production
3. Start the Next.js server on port 3000
4. Map external port 80 → internal port 3000

---

## Deployment Checklist

1. **Add Logo**: Place the FAP wolf logo image at `frontend/public/logo.png`

2. **Configure Secrets**: Add all environment variables in Replit Secrets tab

3. **Run Initial Build**: Let Replit run `npm install && npm run build`

4. **Verify Routes**: Test each page loads correctly:
   - `/onboarding` - Should show VHS logo
   - `/tournaments` - Should redirect to onboarding if incomplete
   - `/agent` - Should show wallet connect prompt

5. **Test Wallet Connection**: Connect a Phantom/Solflare wallet

6. **Select Deployment Type**: Use "Reserved VM" for WebSocket support

7. **Custom Domain (Optional)**: Configure DNS if using custom domain

---

## Known Behaviors

1. **Onboarding Persistence**: Onboarding state is saved to localStorage. To reset, clear localStorage key `fap-onboarding`.

2. **Route Guards**: All main app pages redirect to `/onboarding` if `isOnboardingComplete` is false.

3. **Wallet Authentication**: Users must:
   - Connect wallet (Phantom/Solflare)
   - Sign a message to authenticate
   - JWT token is stored for subsequent requests

4. **Live Slider Controls**:
   - Only visible during live tournament play
   - Only available for BASIC/PRO tier users
   - Changes are "pending" until confirmed
   - Confirmed changes apply at next hand start

5. **Image Upload**: Currently disabled. Avatar placeholder shown. Implementation pending external storage setup.

---

## Tier Features Reference

| Feature | FREE | BASIC | PRO |
|---------|------|-------|-----|
| Base AI engine | ✓ | ✓ | ✓ |
| Tournament access | ✓ | ✓ | ✓ |
| Leaderboard tracking | ✓ | ✓ | ✓ |
| Real-time sliders | ✗ | ✓ | ✓ |
| Custom strategy prompt | ✗ | ✗ | ✓ |

---

## File Dependencies

When modifying files, be aware of these dependencies:

| File | Depends On |
|------|------------|
| `app/*/page.tsx` | `stores/onboardingStore.ts` (route guards) |
| `AppShell.tsx` | `stores/onboardingStore.ts`, `WalletMultiButton` |
| `SettingsPanel.tsx` | `SliderControl.tsx`, `stores/tournamentStore.ts` |
| `app/tournaments/[id]/live/page.tsx` | `PokerTable`, `SettingsPanel`, `useSocket` |
| `lib/api.ts` | Environment variables, `stores/walletStore.ts` |

---

## Support

For issues with:
- **Wallet connection**: Check Solana network configuration
- **API errors**: Verify backend is running and API URL is correct
- **WebSocket issues**: Ensure Reserved VM deployment type
- **Styling issues**: Check Tailwind classes and globals.css

---

*Last updated: Generated from wireframe implementation*
