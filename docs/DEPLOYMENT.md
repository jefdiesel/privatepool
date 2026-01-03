# Deployment Guide

This document covers environment configuration, deployment procedures, and cost analysis.

---

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Key Wallet Addresses](#key-wallet-addresses)
3. [Deployment Checklist](#deployment-checklist)
4. [Monitoring Setup](#monitoring-setup)
5. [Cost Analysis](#cost-analysis)

---

## Environment Variables

```bash
# .env.example

# Environment
ENVIRONMENT=production
DEBUG=false

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_SOLANA_NETWORK=mainnet-beta
NEXT_PUBLIC_PROGRAM_ID=<deployed_program_id>

# Backend (Railway)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
REDIS_URL=redis://user:pass@host:6379

SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=<key>
ADMIN_WALLET_PUBKEY=BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m
TREASURY_WALLET_PUBKEY=CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm
PROGRAM_ID=<deployed_program_id>

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

ENCRYPTION_KEY=<fernet_key_for_prompt_encryption>

CORS_ORIGINS=["https://yourdomain.com"]
```

---

## Key Wallet Addresses

### Development (Devnet)

| Purpose | Address |
|---------|---------|
| **Program ID** | `34MhwbaRczNA8Zt4H8rUwPV4o2MsAtYd8hQhNno3QaLN` |

### Production (Mainnet)

| Purpose | Address |
|---------|---------|
| **Admin Wallet** | `BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m` |
| **Agent Registration Fees Wallet** | `CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm` |

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Admin wallet funded
- [ ] Treasury wallet created
- [ ] POINTS SPL token mint created

### Smart Contract (Solana)

- [ ] Build: `anchor build`
- [ ] Test on devnet: `anchor test`
- [ ] Deploy to mainnet: `anchor deploy --provider.cluster mainnet`
- [ ] Initialize arena: Run initialization script
- [ ] Verify program on Solana Explorer

### Backend (Railway)

- [ ] Dockerfile configured
- [ ] Database migrations run
- [ ] Redis connection verified
- [ ] Health check endpoint responding
- [ ] WebSocket connections working
- [ ] Claude API connection verified (model: `claude-sonnet-4-5-20250929`)

### Frontend (Vercel)

- [ ] Build successful
- [ ] Environment variables set
- [ ] Wallet connection working
- [ ] API endpoints reachable
- [ ] WebSocket connection established

### Post-Deployment

- [ ] Create test tournament (devnet clone on mainnet)
- [ ] Register test agents
- [ ] Run full tournament
- [ ] Verify on-chain results
- [ ] Check POINTS distribution

---

## Monitoring Setup

### Sentry (Error Tracking)
- Backend errors with full context
- Frontend errors with replay
- Performance monitoring
- Alert rules for critical errors

### BetterStack (Uptime)
- API health endpoint: `/health`
- WebSocket endpoint: `wss://api.../health`
- Solana RPC availability
- 1-minute check interval
- SMS/Email alerts

### Vercel Analytics
- Page views and performance
- Web Vitals tracking
- Geographic distribution

### Custom Metrics (Log to PostgreSQL)
- Tournaments created/completed
- Players registered per tier
- API tokens consumed (input + output)
- Decision times
- Win rate by tier (for balancing)
- Cache hit rates

---

## Cost Analysis

### Per-Tournament Costs

```
27-Player Tournament Estimate:
├── Anthropic API (Claude claude-sonnet-4-5-20250929)
│   ├── Decisions: ~1,000 total
│   ├── Input tokens/decision: ~1,800 (with caching)
│   ├── Output tokens/decision: ~50
│   ├── Input cost/1K tokens: $0.003
│   ├── Output cost/1K tokens: $0.015
│   ├── Caching savings: 85% on cached portion
│   └── Subtotal: ~$7.20
│
├── Solana Transactions
│   ├── Tournament creation: 0.001 SOL
│   ├── Player registrations (27): 0.027 SOL
│   ├── Result finalization: 0.001 SOL
│   ├── POINTS distribution (6 winners): 0.006 SOL
│   └── Subtotal: ~0.035 SOL (~$4.50 @ $130/SOL)
│
├── Database (Neon PostgreSQL)
│   └── Negligible per tournament
│
├── Redis (Upstash)
│   └── Negligible per tournament
│
└── TOTAL: ~$11.70 per tournament

Revenue (if all paid tiers):
├── 9 FREE players: $0
├── 9 BASIC players: 0.9 SOL (~$117) - sliders only
├── 9 PRO players: 9 SOL (~$1,170) - sliders + freeform prompt
└── MAX POSSIBLE: ~$1,287 per tournament
```

### Monthly Infrastructure Costs

```
Low Usage (5 tournaments/month, 50 users):
├── Vercel (Frontend): $0 (hobby tier)
├── Railway (Backend): $20
├── Neon PostgreSQL: $0 (free tier)
├── Upstash Redis: $0 (free tier)
├── Helius RPC: $0 (free tier)
├── Sentry: $0 (free tier)
├── BetterStack: $0 (free tier)
├── Anthropic API: ~$36
├── Solana fees: ~$22.50
└── TOTAL: ~$78.50/month

Medium Usage (20 tournaments/month, 500 users):
├── Vercel (Frontend): $20
├── Railway (Backend): $100
├── Neon PostgreSQL: $25
├── Upstash Redis: $10
├── Helius RPC: $49
├── Sentry: $26
├── BetterStack: $15
├── Anthropic API: ~$144
├── Solana fees: ~$90
└── TOTAL: ~$479/month
```
