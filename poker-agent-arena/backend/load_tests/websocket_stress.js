/**
 * k6 Load Test: WebSocket Stress Test
 *
 * Ramps from 10 to 100 concurrent WebSocket connections.
 * Tests Socket.IO real-time event handling.
 *
 * Thresholds:
 * - WebSocket p95 < 100ms
 * - WebSocket p99 < 250ms
 *
 * Run: k6 run websocket_stress.js
 */

import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const wsConnections = new Counter('ws_connections');
const wsMessages = new Counter('ws_messages_received');
const wsMessageLatency = new Trend('ws_message_latency', true);
const wsConnectionTime = new Trend('ws_connection_time', true);
const wsErrors = new Rate('ws_errors');

// Configuration
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000/socket.io/';
const TOURNAMENT_ID = __ENV.TOURNAMENT_ID || 'test-tournament-1';
const TABLE_ID = __ENV.TABLE_ID || 'test-table-1';

export const options = {
  scenarios: {
    // Ramp from 10 to 100 connections
    ws_ramp: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '1m', target: 25 },   // Ramp to 25
        { duration: '2m', target: 50 },   // Ramp to 50
        { duration: '2m', target: 75 },   // Ramp to 75
        { duration: '2m', target: 100 },  // Ramp to 100
        { duration: '3m', target: 100 },  // Hold at 100
        { duration: '1m', target: 50 },   // Ramp down to 50
        { duration: '1m', target: 0 },    // Ramp down to 0
      ],
    },
  },

  thresholds: {
    ws_message_latency: [
      'p(95)<100',  // 95th percentile < 100ms
      'p(99)<250',  // 99th percentile < 250ms
    ],
    ws_connection_time: ['p(95)<1000'], // Connection < 1s
    ws_errors: ['rate<0.05'], // Error rate < 5%
  },
};

// Socket.IO protocol helpers
function encodeSocketIOPacket(type, data = null) {
  // Socket.IO packet types:
  // 0: CONNECT
  // 2: EVENT
  // 3: ACK
  // 4: ERROR
  if (data) {
    return `4${type}${JSON.stringify(data)}`;
  }
  return `4${type}`;
}

function decodeSocketIOPacket(message) {
  if (message.startsWith('0')) {
    // Engine.IO OPEN packet
    return { type: 'open', data: JSON.parse(message.slice(1)) };
  }
  if (message.startsWith('40')) {
    // Socket.IO CONNECT
    return { type: 'connect', namespace: '/' };
  }
  if (message.startsWith('42')) {
    // Socket.IO EVENT
    try {
      const data = JSON.parse(message.slice(2));
      return { type: 'event', name: data[0], data: data[1] };
    } catch {
      return { type: 'event', raw: message };
    }
  }
  if (message === '2') {
    // Engine.IO PING
    return { type: 'ping' };
  }
  if (message === '3') {
    // Engine.IO PONG
    return { type: 'pong' };
  }
  return { type: 'unknown', raw: message };
}

// Generate mock session token
function getSessionToken() {
  return `mock-ws-token-${__VU}-${Date.now()}`;
}

// WebSocket test function
export default function () {
  const token = getSessionToken();
  const connectStart = Date.now();

  // Build Socket.IO handshake URL
  const url = `${WS_URL}?EIO=4&transport=websocket&token=${token}`;

  let connected = false;
  let messagesReceived = 0;
  let lastMessageTime = Date.now();

  const response = ws.connect(url, {
    tags: { name: 'websocket' },
  }, function (socket) {
    // Track connection time
    socket.on('open', function () {
      wsConnectionTime.add(Date.now() - connectStart);
      wsConnections.add(1);
    });

    // Handle messages
    socket.on('message', function (message) {
      const now = Date.now();
      const latency = now - lastMessageTime;
      lastMessageTime = now;

      const packet = decodeSocketIOPacket(message);
      messagesReceived++;
      wsMessages.add(1);

      // Track latency for real events (not protocol messages)
      if (packet.type === 'event') {
        wsMessageLatency.add(latency);
      }

      // Handle Engine.IO ping
      if (packet.type === 'ping') {
        socket.send('3'); // Pong
      }

      // Handle Socket.IO connect
      if (packet.type === 'connect') {
        connected = true;

        // Join tournament room
        const joinEvent = ['join_tournament', { tournament_id: TOURNAMENT_ID }];
        socket.send(encodeSocketIOPacket('2', joinEvent));

        // Subscribe to table
        const subscribeEvent = ['subscribe_table', { table_id: TABLE_ID }];
        socket.send(encodeSocketIOPacket('2', subscribeEvent));
      }

      // Handle table state updates
      if (packet.type === 'event' && packet.name === 'table_state') {
        // Simulate processing time
        const processStart = Date.now();
        // Process state...
        const processTime = Date.now() - processStart;
        wsMessageLatency.add(processTime);
      }
    });

    // Handle errors
    socket.on('error', function (e) {
      wsErrors.add(true);
      console.error(`WS Error (VU ${__VU}): ${e.message}`);
    });

    // Handle close
    socket.on('close', function () {
      if (!connected) {
        wsErrors.add(true);
      }
    });

    // Keep connection alive and simulate user activity
    const duration = 30; // seconds
    const iterations = duration;

    for (let i = 0; i < iterations; i++) {
      // Wait for messages
      socket.setTimeout(function () {
        // Periodically request state refresh
        if (i % 10 === 0 && connected) {
          const refreshEvent = ['request_table_state', { table_id: TABLE_ID }];
          socket.send(encodeSocketIOPacket('2', refreshEvent));
        }
      }, 1000 * i);
    }

    // Close after duration
    socket.setTimeout(function () {
      if (connected) {
        // Leave tournament
        const leaveEvent = ['leave_tournament', { tournament_id: TOURNAMENT_ID }];
        socket.send(encodeSocketIOPacket('2', leaveEvent));
      }
      socket.close();
    }, 1000 * duration);
  });

  // Verify connection was successful
  check(response, {
    'WebSocket connected': (r) => r && r.status === 101,
  });

  if (!response || response.status !== 101) {
    wsErrors.add(true);
  }

  // Random pause before next connection
  sleep(Math.random() * 3 + 1);
}

// Setup function
export function setup() {
  console.log('Starting WebSocket stress test');
  console.log(`WebSocket URL: ${WS_URL}`);
  console.log(`Tournament ID: ${TOURNAMENT_ID}`);
  console.log(`Table ID: ${TABLE_ID}`);

  return { startTime: Date.now() };
}

// Teardown function
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Test completed in ${duration.toFixed(2)} seconds`);
}
