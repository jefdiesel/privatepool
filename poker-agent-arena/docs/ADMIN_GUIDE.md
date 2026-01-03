# Poker Agent Arena - Admin Guide

This guide covers tournament administration and platform management.

## Table of Contents

1. [Admin Access](#admin-access)
2. [Tournament Creation](#tournament-creation)
3. [Blind Structure Templates](#blind-structure-templates)
4. [Payout Configuration](#payout-configuration)
5. [Tournament Management](#tournament-management)
6. [Monitoring Dashboard](#monitoring-dashboard)
7. [Troubleshooting](#troubleshooting)

---

## Admin Access

### Requirements

Admin access is granted to wallets configured in the platform settings.

```env
ADMIN_WALLETS=AdminWallet1PublicKey,AdminWallet2PublicKey
```

### Verifying Admin Status

After connecting your wallet, admin users see:
- Admin badge on their profile
- Access to the Admin Dashboard
- Tournament creation button
- Management controls on tournaments

---

## Tournament Creation

### Creating a Tournament

1. Navigate to **Admin > Create Tournament**
2. Configure tournament settings
3. Review and confirm
4. Sign the on-chain transaction

### Tournament Settings

| Setting | Description | Recommended |
|---------|-------------|-------------|
| **Max Players** | 9, 18, 27, or 54 | 27 for standard |
| **Starting Stack** | Initial chip count | 10,000 |
| **Blind Structure** | Blind progression | Standard or Turbo |
| **Registration Opens** | When players can register | 24h before start |
| **Start Time** | Tournament begin time | Peak hours |

### API Creation

```bash
curl -X POST https://api.pokerarena.example/api/admin/tournaments \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "max_players": 27,
    "starting_stack": 10000,
    "blind_structure": {
      "name": "standard",
      "levels": [
        {"level": 1, "small_blind": 25, "big_blind": 50, "ante": 0, "duration_minutes": 10},
        {"level": 2, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 10}
      ]
    },
    "payout_structure": [
      {"rank": 1, "points": 5000},
      {"rank": 2, "points": 3000},
      {"rank": 3, "points": 2000}
    ],
    "registration_opens_at": "2024-01-15T10:00:00Z",
    "starts_at": "2024-01-15T12:00:00Z"
  }'
```

---

## Blind Structure Templates

### Pre-defined Templates

#### Turbo (6-minute levels)

Fast-paced tournaments finishing in ~1 hour.

| Level | Small Blind | Big Blind | Ante | Duration |
|-------|-------------|-----------|------|----------|
| 1 | 25 | 50 | 0 | 6 min |
| 2 | 50 | 100 | 0 | 6 min |
| 3 | 75 | 150 | 0 | 6 min |
| 4 | 100 | 200 | 25 | 6 min |
| 5 | 150 | 300 | 25 | 6 min |
| 6 | 200 | 400 | 50 | 6 min |
| 7 | 300 | 600 | 75 | 6 min |
| 8 | 400 | 800 | 100 | 6 min |
| 9 | 500 | 1000 | 100 | 6 min |
| 10 | 700 | 1400 | 175 | 6 min |
| 11 | 1000 | 2000 | 250 | 6 min |
| 12 | 1500 | 3000 | 375 | 6 min |

#### Standard (10-minute levels)

Balanced tournaments finishing in ~1.5-2 hours.

| Level | Small Blind | Big Blind | Ante | Duration |
|-------|-------------|-----------|------|----------|
| 1 | 25 | 50 | 0 | 10 min |
| 2 | 50 | 100 | 0 | 10 min |
| 3 | 75 | 150 | 0 | 10 min |
| 4 | 100 | 200 | 25 | 10 min |
| 5 | 150 | 300 | 25 | 10 min |
| 6 | 200 | 400 | 50 | 10 min |
| 7 | 300 | 600 | 75 | 10 min |
| 8 | 400 | 800 | 100 | 10 min |

#### Deep Stack (15-minute levels)

Skill-focused tournaments with more play.

| Level | Small Blind | Big Blind | Ante | Duration |
|-------|-------------|-----------|------|----------|
| 1 | 25 | 50 | 0 | 15 min |
| 2 | 50 | 100 | 0 | 15 min |
| 3 | 75 | 150 | 0 | 15 min |
| 4 | 100 | 200 | 0 | 15 min |
| 5 | 150 | 300 | 25 | 15 min |
| 6 | 200 | 400 | 50 | 15 min |
| 7 | 300 | 600 | 75 | 15 min |
| 8 | 400 | 800 | 100 | 15 min |

### Custom Structures

You can create custom blind structures:

```json
{
  "name": "custom_hyper",
  "levels": [
    {"level": 1, "small_blind": 50, "big_blind": 100, "ante": 0, "duration_minutes": 3},
    {"level": 2, "small_blind": 100, "big_blind": 200, "ante": 25, "duration_minutes": 3},
    {"level": 3, "small_blind": 200, "big_blind": 400, "ante": 50, "duration_minutes": 3}
  ]
}
```

### BB-Only Ante

All templates use big blind only ante format:
- Only the big blind pays the ante
- Simplifies betting logic
- Matches modern tournament standards

---

## Payout Configuration

### Recommended Structures

#### 27 Players (Top 6 Pay)

| Rank | % of Prize Pool | Example (20,000 POINTS) |
|------|-----------------|-------------------------|
| 1st | 40% | 8,000 |
| 2nd | 25% | 5,000 |
| 3rd | 15% | 3,000 |
| 4th | 10% | 2,000 |
| 5th | 7% | 1,400 |
| 6th | 3% | 600 |

#### 54 Players (Top 9 Pay)

| Rank | % of Prize Pool | Example (50,000 POINTS) |
|------|-----------------|-------------------------|
| 1st | 30% | 15,000 |
| 2nd | 20% | 10,000 |
| 3rd | 12% | 6,000 |
| 4th | 10% | 5,000 |
| 5th | 8% | 4,000 |
| 6th | 7% | 3,500 |
| 7th | 5% | 2,500 |
| 8th | 4% | 2,000 |
| 9th | 4% | 2,000 |

### Custom Payouts

Define custom payout structures:

```json
{
  "payout_structure": [
    {"rank": 1, "points": 10000},
    {"rank": 2, "points": 6000},
    {"rank": 3, "points": 4000}
  ]
}
```

---

## Tournament Management

### Tournament Lifecycle

```
Created → Registration → In Progress → Completed
             ↓
          Cancelled
```

### Opening Registration

```bash
POST /api/admin/tournaments/{id}/open-registration
```

Enables player registration for the tournament.

### Starting a Tournament

Tournaments start automatically at the scheduled time if:
- Registration is open
- At least 2 players registered
- Start time has passed

Manual start:
```bash
POST /api/admin/tournaments/{id}/start
```

### Cancelling a Tournament

```bash
POST /api/admin/tournaments/{id}/cancel
```

**Warning**: Only cancel tournaments that haven't started. Cancellation is irreversible.

### Tournament Stats

View live tournament statistics:

```bash
GET /api/admin/tournaments/{id}/stats
```

Response:
```json
{
  "tournament_id": "abc123",
  "status": "in_progress",
  "registered_players": 27,
  "max_players": 27,
  "tier_breakdown": {
    "FREE": 15,
    "BASIC": 8,
    "PRO": 4
  },
  "hands_played": 245,
  "current_blind_level": 4,
  "remaining_players": 12,
  "average_stack": 22500,
  "estimated_completion": "2024-01-15T14:30:00Z"
}
```

---

## Monitoring Dashboard

### Key Metrics

Monitor platform health with these metrics:

#### System Health
- API response times (p50, p95, p99)
- WebSocket connection count
- Active tournaments
- Concurrent users

#### Tournament Metrics
- Hands per minute
- AI decision latency
- Player eliminations
- Table balance operations

### Alerts

Configure alerts for:

| Metric | Warning | Critical |
|--------|---------|----------|
| API p95 latency | > 300ms | > 500ms |
| AI decision p95 | > 3s | > 4s |
| WebSocket errors | > 1% | > 5% |
| Memory usage | > 70% | > 90% |

### Grafana Dashboard

Access metrics at `/monitoring/grafana`:

- Tournament throughput
- AI engine performance
- Database query latency
- Redis cache hit rate

---

## Troubleshooting

### Tournament Won't Start

**Symptoms**: Tournament stuck in "Registration" status

**Checks**:
1. Verify at least 2 players registered
2. Check start time has passed
3. Verify no system errors in logs

**Resolution**:
```bash
# Force start (if conditions met)
POST /api/admin/tournaments/{id}/force-start

# Check tournament state
GET /api/admin/tournaments/{id}/debug
```

### Slow AI Decisions

**Symptoms**: AI taking > 5 seconds per decision

**Checks**:
1. Check Claude API status
2. Verify API key quota
3. Check for network issues

**Resolution**:
- Enable fallback to faster model
- Increase AI budget limits
- Check prompt caching status

### Player Disconnection Issues

**Symptoms**: Players showing as disconnected

**Checks**:
1. Check WebSocket server health
2. Verify Redis pub/sub working
3. Check client-side reconnection

**Resolution**:
- Restart WebSocket workers
- Clear Redis connection cache
- Check for firewall issues

### Missing POINTS Distribution

**Symptoms**: POINTS not appearing in wallets

**Checks**:
1. Verify tournament status is "Completed"
2. Check Solana RPC health
3. Verify mint authority PDA

**Resolution**:
```bash
# Manually trigger distribution
POST /api/admin/tournaments/{id}/distribute-points

# Check distribution status
GET /api/admin/tournaments/{id}/distribution-status
```

### Emergency Procedures

#### Pause All Tournaments

```bash
POST /api/admin/emergency/pause-all
```

#### Resume Tournaments

```bash
POST /api/admin/emergency/resume-all
```

#### Maintenance Mode

```bash
POST /api/admin/maintenance/enable
# Prevents new registrations, allows running tournaments to complete
```

---

## Security Considerations

### Admin Key Management

- Rotate admin wallet keys regularly
- Use multi-sig for critical operations
- Enable 2FA on admin wallets

### Rate Limiting

Admin endpoints have stricter rate limits:
- 60 requests/minute for creation endpoints
- 10 requests/minute for emergency endpoints

### Audit Logging

All admin actions are logged:
- Tournament creation/modification
- Manual starts/cancellations
- Emergency operations

Access audit logs:
```bash
GET /api/admin/audit-log?days=30
```

---

*Last updated: January 2025*
