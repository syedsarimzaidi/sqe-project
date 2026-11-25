import http from 'k6/http';
import { check, sleep } from 'k6';

const base = __ENV.SQE_BASE_URL || 'http://localhost:8000';
const fixtureIds = (__ENV.SQE_STOCK_IDS || __ENV.SQE_STOCK_ID || '').split(',').map(Number);
const item = fixtureIds[Math.max(0, __VU - 1) % fixtureIds.length];

if (!/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(base) || !Number.isInteger(item) || item < 1 || !__ENV.SQE_TOKEN) {
  throw new Error('Use a disposable loopback instance, stock fixture ID and fixture API token.');
}

const headers = {
  Authorization: 'Token ' + __ENV.SQE_TOKEN,
  'Content-Type': 'application/json'
};

export const options = {
  vus: Number(__ENV.SQE_VUS || 1),
  duration: __ENV.SQE_DURATION || '60s',
  thresholds: {
    'http_req_duration{operation:receive}': ['p(95)<500'],
    'http_req_duration{operation:dispatch}': ['p(95)<500'],
    http_req_failed: ['rate==0'],
    checks: ['rate==1']
  }
};

export default function () {
  const body = JSON.stringify({items: [{pk: item, quantity: '1'}]});
  for (const [operation, endpoint] of [['receive', 'add'], ['dispatch', 'remove']]) {
    const response = http.post(base + '/api/stock/' + endpoint + '/', body, {
      headers,
      tags: {operation}
    });
    check(response, {[operation + ' returns 201']: r => r.status === 201});
    if (response.status !== 201) break;
  }
  sleep(0.15);
}
