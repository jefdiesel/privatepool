/**
 * k6 Load Test: AI Decision Latency
 *
 * Tests AI decision-making endpoint performance.
 * Sustains 10 decisions per second to simulate tournament play.
 *
 * Thresholds:
 * - AI p50 < 2s
 * - AI p95 < 4s
 * - AI p99 < 5s
 *
 * Run: k6 run ai_decision_latency.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const aiDecisions = new Counter('ai_decisions');
const aiDecisionLatency = new Trend('ai_decision_latency', true);
const aiErrors = new Rate('ai_errors');
const aiTimeouts = new Counter('ai_timeouts');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AI_DECISION_TIMEOUT = 10000; // 10 second timeout

export const options = {
  scenarios: {
    // Sustain 10 decisions per second
    constant_rate: {
      executor: 'constant-arrival-rate',
      rate: 10, // 10 iterations per timeUnit
      timeUnit: '1s',
      duration: '10m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },

  thresholds: {
    ai_decision_latency: [
      'p(50)<2000',  // 50th percentile < 2s
      'p(95)<4000',  // 95th percentile < 4s
      'p(99)<5000',  // 99th percentile < 5s
    ],
    ai_errors: ['rate<0.05'], // Error rate < 5%
  },
};

// Generate mock auth header
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer mock-ai-token-${__VU}`,
  };
}

// Sample hand states for testing
const SAMPLE_HAND_STATES = [
  {
    // Strong hand preflop
    hand_id: 'hand_001',
    betting_round: 'preflop',
    pot: 150,
    current_bet: 100,
    min_raise: 100,
    hole_cards: ['Ah', 'Ad'],
    community_cards: [],
    position: 'button',
    stack: 9900,
    players_active: 4,
    valid_actions: ['fold', 'call', 'raise'],
  },
  {
    // Medium hand on flop
    hand_id: 'hand_002',
    betting_round: 'flop',
    pot: 450,
    current_bet: 200,
    min_raise: 200,
    hole_cards: ['Kd', 'Qd'],
    community_cards: ['Jd', '9h', '5d'],
    position: 'cutoff',
    stack: 8500,
    players_active: 3,
    valid_actions: ['fold', 'call', 'raise'],
  },
  {
    // Drawing hand on turn
    hand_id: 'hand_003',
    betting_round: 'turn',
    pot: 1200,
    current_bet: 400,
    min_raise: 400,
    hole_cards: ['9h', '8h'],
    community_cards: ['7h', '6c', '2s', 'Ah'],
    position: 'big_blind',
    stack: 6000,
    players_active: 2,
    valid_actions: ['fold', 'call', 'raise'],
  },
  {
    // All-in situation
    hand_id: 'hand_004',
    betting_round: 'river',
    pot: 5000,
    current_bet: 2500,
    min_raise: 2500,
    hole_cards: ['Ac', 'Kc'],
    community_cards: ['Qc', 'Jc', '4d', '8s', 'Tc'],
    position: 'small_blind',
    stack: 3000,
    players_active: 2,
    valid_actions: ['fold', 'call'],
  },
  {
    // Check opportunity
    hand_id: 'hand_005',
    betting_round: 'flop',
    pot: 200,
    current_bet: 0,
    min_raise: 50,
    hole_cards: ['7c', '7d'],
    community_cards: ['As', 'Kh', '3c'],
    position: 'under_the_gun',
    stack: 9800,
    players_active: 5,
    valid_actions: ['check', 'raise'],
  },
];

// Agent tier configurations
const AGENT_TIERS = ['FREE', 'BASIC', 'PRO'];

// Select random hand state
function selectHandState() {
  return SAMPLE_HAND_STATES[Math.floor(Math.random() * SAMPLE_HAND_STATES.length)];
}

// Select random agent tier
function selectAgentTier() {
  return AGENT_TIERS[Math.floor(Math.random() * AGENT_TIERS.length)];
}

// Build decision request
function buildDecisionRequest() {
  const handState = selectHandState();
  const tier = selectAgentTier();

  return {
    tournament_id: 'load-test-tournament',
    table_id: `table-${__VU}`,
    hand_state: handState,
    agent_tier: tier,
    agent_config: {
      sliders: tier !== 'FREE' ? {
        aggression: Math.floor(Math.random() * 100),
        bluff_frequency: Math.floor(Math.random() * 100),
        tightness: Math.floor(Math.random() * 100),
        position_awareness: Math.floor(Math.random() * 100),
      } : null,
      custom_prompt: tier === 'PRO' ? 'Be aggressive with strong hands.' : null,
    },
  };
}

// Request AI decision
function requestAIDecision() {
  const request = buildDecisionRequest();
  const start = Date.now();

  const res = http.post(
    `${BASE_URL}/api/internal/ai/decision`,
    JSON.stringify(request),
    {
      headers: getAuthHeaders(),
      timeout: AI_DECISION_TIMEOUT,
      tags: { name: 'ai_decision' },
    }
  );

  const latency = Date.now() - start;
  aiDecisionLatency.add(latency);
  aiDecisions.add(1);

  // Check for timeout
  if (latency >= AI_DECISION_TIMEOUT) {
    aiTimeouts.add(1);
  }

  const success = check(res, {
    'ai decision status 200': (r) => r.status === 200,
    'ai decision has action': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.action && ['fold', 'check', 'call', 'raise'].includes(body.action);
      } catch {
        return false;
      }
    },
    'ai decision latency < 5s': () => latency < 5000,
  });

  aiErrors.add(!success);

  return res;
}

// Validate AI response format
function validateAIResponse(res) {
  if (res.status !== 200) {
    return false;
  }

  try {
    const body = JSON.parse(res.body);

    // Required fields
    if (!body.action) return false;
    if (!['fold', 'check', 'call', 'raise'].includes(body.action)) return false;

    // Raise must have amount
    if (body.action === 'raise' && typeof body.amount !== 'number') {
      return false;
    }

    // Optional fields
    if (body.reasoning && typeof body.reasoning !== 'string') {
      return false;
    }

    return true;
  } catch {
    return false;
  }
}

// Main test function
export default function () {
  const res = requestAIDecision();

  // Additional validation
  const valid = validateAIResponse(res);
  if (!valid) {
    aiErrors.add(true);
  }

  // Log slow decisions for debugging
  if (res && res.timings && res.timings.duration > 4000) {
    console.log(`Slow AI decision: ${res.timings.duration}ms (VU ${__VU})`);
  }
}

// Setup function
export function setup() {
  console.log('Starting AI decision latency test');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Target: 10 decisions/second sustained');

  // Warm up the AI service
  console.log('Warming up AI service...');
  for (let i = 0; i < 3; i++) {
    const warmupReq = buildDecisionRequest();
    http.post(
      `${BASE_URL}/api/internal/ai/decision`,
      JSON.stringify(warmupReq),
      {
        headers: getAuthHeaders(),
        timeout: 30000,
      }
    );
    sleep(1);
  }
  console.log('Warmup complete');

  return { startTime: Date.now() };
}

// Teardown function
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Test completed in ${duration.toFixed(2)} seconds`);
}

// Custom summary
export function handleSummary(data) {
  const summary = {
    'AI Decision Load Test Summary': {
      'Total Decisions': data.metrics.ai_decisions?.values?.count || 0,
      'Error Rate': `${((data.metrics.ai_errors?.values?.rate || 0) * 100).toFixed(2)}%`,
      'Timeouts': data.metrics.ai_timeouts?.values?.count || 0,
      'Latency p50': `${(data.metrics.ai_decision_latency?.values?.['p(50)'] || 0).toFixed(0)}ms`,
      'Latency p95': `${(data.metrics.ai_decision_latency?.values?.['p(95)'] || 0).toFixed(0)}ms`,
      'Latency p99': `${(data.metrics.ai_decision_latency?.values?.['p(99)'] || 0).toFixed(0)}ms`,
    },
  };

  return {
    stdout: JSON.stringify(summary, null, 2),
  };
}
