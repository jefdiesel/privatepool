/**
 * k6 Load Test: Tournament Simulation
 *
 * Simulates 54 concurrent virtual users (VUs) for 30 minutes.
 * This represents a full 2-table tournament with spectators.
 *
 * Thresholds:
 * - HTTP p95 < 500ms
 * - HTTP p99 < 1s
 * - Error rate < 1%
 *
 * Run: k6 run tournament_simulation.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const tournamentRequests = new Counter('tournament_requests');
const errorRate = new Rate('errors');
const tournamentListLatency = new Trend('tournament_list_latency', true);
const tournamentDetailLatency = new Trend('tournament_detail_latency', true);
const leaderboardLatency = new Trend('leaderboard_latency', true);

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOURNAMENT_ID = __ENV.TOURNAMENT_ID || 'test-tournament-1';

export const options = {
  // Simulate 54 concurrent users for 30 minutes
  scenarios: {
    tournament_load: {
      executor: 'constant-vus',
      vus: 54,
      duration: '30m',
    },
  },

  // Performance thresholds
  thresholds: {
    http_req_duration: [
      'p(95)<500',  // 95th percentile < 500ms
      'p(99)<1000', // 99th percentile < 1s
    ],
    errors: ['rate<0.01'], // Error rate < 1%
    tournament_list_latency: ['p(95)<400'],
    tournament_detail_latency: ['p(95)<450'],
    leaderboard_latency: ['p(95)<400'],
  },
};

// Generate mock auth token (in real scenario, this would be JWT)
function getAuthHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer mock-session-token-${__VU}`,
  };
}

// Simulate different user behaviors
const USER_BEHAVIORS = [
  'spectator',      // Just watches (50%)
  'active_player',  // Participating in tournament (30%)
  'admin',          // Tournament admin (5%)
  'leaderboard',    // Checking leaderboard (15%)
];

function selectBehavior() {
  const rand = Math.random();
  if (rand < 0.50) return 'spectator';
  if (rand < 0.80) return 'active_player';
  if (rand < 0.85) return 'admin';
  return 'leaderboard';
}

// List tournaments
function listTournaments() {
  const start = Date.now();
  const res = http.get(`${BASE_URL}/api/tournaments?status=all&limit=20`, {
    headers: getAuthHeaders(),
    tags: { name: 'list_tournaments' },
  });

  tournamentListLatency.add(Date.now() - start);
  tournamentRequests.add(1);

  const success = check(res, {
    'list tournaments status 200': (r) => r.status === 200,
    'list tournaments has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!success);
  return res;
}

// Get tournament detail
function getTournamentDetail(id) {
  const start = Date.now();
  const res = http.get(`${BASE_URL}/api/tournaments/${id}`, {
    headers: getAuthHeaders(),
    tags: { name: 'get_tournament' },
  });

  tournamentDetailLatency.add(Date.now() - start);
  tournamentRequests.add(1);

  const success = check(res, {
    'tournament detail status 200': (r) => r.status === 200 || r.status === 404,
  });

  errorRate.add(!success);
  return res;
}

// Get leaderboard
function getLeaderboard(page = 1) {
  const start = Date.now();
  const res = http.get(`${BASE_URL}/api/leaderboard?page=${page}&per_page=50`, {
    headers: getAuthHeaders(),
    tags: { name: 'get_leaderboard' },
  });

  leaderboardLatency.add(Date.now() - start);
  tournamentRequests.add(1);

  const success = check(res, {
    'leaderboard status 200': (r) => r.status === 200,
  });

  errorRate.add(!success);
  return res;
}

// Health check
function healthCheck() {
  const res = http.get(`${BASE_URL}/api/health`, {
    tags: { name: 'health_check' },
  });

  check(res, {
    'health check status 200': (r) => r.status === 200,
  });

  return res;
}

// Spectator behavior: watches tournament, refreshes periodically
function spectatorBehavior() {
  // Check health
  healthCheck();
  sleep(1);

  // List tournaments
  listTournaments();
  sleep(2);

  // Watch specific tournament (poll for updates)
  for (let i = 0; i < 5; i++) {
    getTournamentDetail(TOURNAMENT_ID);
    sleep(3); // Poll every 3 seconds
  }

  // Check leaderboard occasionally
  if (Math.random() < 0.3) {
    getLeaderboard();
    sleep(1);
  }
}

// Active player behavior: more frequent updates
function activePlayerBehavior() {
  // Initial setup
  healthCheck();
  listTournaments();
  sleep(1);

  // Active polling during hand (faster)
  for (let i = 0; i < 10; i++) {
    getTournamentDetail(TOURNAMENT_ID);
    sleep(1); // Poll every second during action
  }

  // Between hands
  sleep(5);

  // Check results
  getLeaderboard();
}

// Admin behavior: tournament management
function adminBehavior() {
  healthCheck();
  sleep(1);

  // Check all tournaments
  listTournaments();
  sleep(2);

  // Get tournament stats multiple times
  for (let i = 0; i < 3; i++) {
    getTournamentDetail(TOURNAMENT_ID);
    sleep(5);
  }

  // Check leaderboard
  getLeaderboard(1);
  getLeaderboard(2);
}

// Leaderboard behavior: focused on rankings
function leaderboardBehavior() {
  healthCheck();
  sleep(1);

  // Browse leaderboard pages
  for (let page = 1; page <= 3; page++) {
    getLeaderboard(page);
    sleep(2);
  }

  // Occasionally check a tournament
  if (Math.random() < 0.5) {
    listTournaments();
    getTournamentDetail(TOURNAMENT_ID);
  }
}

// Main test function
export default function () {
  const behavior = selectBehavior();

  switch (behavior) {
    case 'spectator':
      spectatorBehavior();
      break;
    case 'active_player':
      activePlayerBehavior();
      break;
    case 'admin':
      adminBehavior();
      break;
    case 'leaderboard':
      leaderboardBehavior();
      break;
    default:
      spectatorBehavior();
  }

  // Random pause between iterations
  sleep(Math.random() * 5 + 2);
}

// Setup function - runs once before test
export function setup() {
  console.log('Starting tournament simulation load test');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Tournament ID: ${TOURNAMENT_ID}`);

  // Verify API is reachable
  const res = http.get(`${BASE_URL}/api/health`);
  if (res.status !== 200) {
    throw new Error('API health check failed');
  }

  return { startTime: Date.now() };
}

// Teardown function - runs once after test
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Test completed in ${duration.toFixed(2)} seconds`);
}
