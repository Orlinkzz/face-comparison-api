
import http from 'k6/http';
import { check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// =====================================================
// CONFIGURATION
// =====================================================

const BASE_URL = (__ENV.BASE_URL || 'http://10.xxx.xx.xx')
  .replace(/\/+$/, '');

const PROFILE_PHOTO = __ENV.PROFILE_PHOTO || './profile.jpg';
const SELFIE_PHOTO = __ENV.SELFIE_PHOTO || './selfie.jpg';

const REQUEST_TIMEOUT = __ENV.REQUEST_TIMEOUT || '60s';
const VERBOSE = __ENV.VERBOSE === '1';

// Tahapan concurrency.
// Jarak 80 detik memberi waktu bagi tahap sebelumnya
// untuk selesai sebelum tahap berikutnya dimulai.
const STAGE_INTERVAL_SECONDS = 80;
const STAGE_MAX_DURATION = '65s';

const stages = [
  { name: 'stage_5_vus', vus: 5, startTime: '0s' },
  { name: 'stage_10_vus', vus: 10, startTime: '80s' },
  { name: 'stage_20_vus', vus: 20, startTime: '160s' },
  { name: 'stage_40_vus', vus: 40, startTime: '240s' },
  { name: 'stage_120_vus', vus: 120, startTime: '320s' },
];

// =====================================================
// METRICS
// =====================================================

const matchDuration = new Trend('face_match_duration', true);

const profileEncodingDuration =
  new Trend('profile_encoding_duration', true);

const selfieEncodingDuration =
  new Trend('selfie_encoding_duration', true);

const faceCompareDuration =
  new Trend('face_compare_duration', true);

const serverDuration = new Trend('face_server_duration', true);

const matchSuccess = new Counter('face_match_success');
const matchPending = new Counter('face_match_pending');
const matchBusinessError = new Counter('face_match_business_error');
const matchFailed = new Counter('face_match_failed');

// =====================================================
// SCENARIOS
// =====================================================

const scenarios = {};

for (const stage of stages) {
  scenarios[stage.name] = {
    executor: 'per-vu-iterations',
    vus: stage.vus,
    iterations: 1,
    startTime: stage.startTime,
    maxDuration: STAGE_MAX_DURATION,
    gracefulStop: '10s',
    tags: {
      test_stage: stage.name,
    },
  };
}

// =====================================================
// OPTIONS
// =====================================================

export const options = {
  scenarios,

  discardResponseBodies: false,

  thresholds: {
    http_req_failed: ['rate<0.05'],

    // Target latency P95 < 10 detik per tahap.
    'face_match_duration{test_stage:stage_5_vus}': [
      'p(95)<10000',
    ],
    'face_match_duration{test_stage:stage_10_vus}': [
      'p(95)<10000',
    ],
    'face_match_duration{test_stage:stage_20_vus}': [
      'p(95)<10000',
    ],
    'face_match_duration{test_stage:stage_40_vus}': [
      'p(95)<10000',
    ],
    'face_match_duration{test_stage:stage_120_vus}': [
      'p(95)<10000',
    ],
  },
};

// =====================================================
// TEST DATA
// =====================================================

const profile = open(PROFILE_PHOTO, 'b');
const selfie = open(SELFIE_PHOTO, 'b');

export function setup() {
  console.log(`Target: ${BASE_URL}`);
  console.log(`Profile image: ${PROFILE_PHOTO}`);
  console.log(`Selfie image: ${SELFIE_PHOTO}`);
  console.log(`Profile size: ${profile.byteLength} bytes`);
  console.log(`Selfie size: ${selfie.byteLength} bytes`);
  console.log(
    `Stages: ${stages.map(s => `${s.vus} VUs`).join(' -> ')}`
  );

  return {};
}

// =====================================================
// SERVER-TIMING PARSER
// Requires optional instrumentation in Flask.
// =====================================================

function recordServerTimings(response) {
  const header = response.headers['Server-Timing'];

  if (!header) {
    return;
  }

  const regex = /([\w-]+);dur=([\d.]+)/g;
  let match;

  while ((match = regex.exec(header)) !== null) {
    const name = match[1];
    const duration = Number(match[2]);

    if (!Number.isFinite(duration)) {
      continue;
    }

    switch (name) {
      case 'profile_encoding':
        profileEncodingDuration.add(duration);
        break;

      case 'selfie_encoding':
        selfieEncodingDuration.add(duration);
        break;

      case 'face_compare':
        faceCompareDuration.add(duration);
        break;

      case 'total':
        serverDuration.add(duration);
        break;
    }
  }
}

// =====================================================
// MAIN TEST
// =====================================================

export default function () {
  const stage = __ENV.TEST_STAGE || 'default';

  const payload = {
    image1: http.file(
      profile,
      'profile.jpg',
      'image/jpeg'
    ),

    image2: http.file(
      selfie,
      'selfie.jpg',
      'image/jpeg'
    ),
  };

  const response = http.post(
    `${BASE_URL}/face-recognition/compare_faces`,
    payload,
    {
      timeout: REQUEST_TIMEOUT,

      tags: {
        endpoint: 'compare_faces',
      },
    }
  );

  matchDuration.add(response.timings.duration);

  recordServerTimings(response);

  let result = null;

  try {
    result = response.json();
  } catch (_) {
    // Respons bukan JSON.
  }

  const httpOk = response.status === 200;

  const validPayload =
    result !== null &&
    typeof result.status === 'string' &&
    ['success', 'pending', 'error'].includes(result.status);

  const checksPassed = check(response, {
    'HTTP status is 200': () => httpOk,

    'response has valid API status': () => validPayload,
  });

  if (!checksPassed) {
    matchFailed.add(1);

    console.error(
      `Request failed | HTTP ${response.status} | ` +
      `duration=${response.timings.duration}ms | ` +
      `body=${String(response.body).slice(0, 500)}`
    );

    return;
  }

  switch (result.status) {
    case 'success':
      matchSuccess.add(1);
      break;

    case 'pending':
      matchPending.add(1);
      break;

    case 'error':
      // API berhasil merespons, tetapi proses bisnis
      // tidak menghasilkan kecocokan wajah.
      matchBusinessError.add(1);
      break;
  }

  if (VERBOSE) {
    console.log(
      `HTTP ${response.status} | ` +
      `duration=${response.timings.duration}ms | ` +
      `status=${result.status} | ` +
      `distance=${result.distance ?? 'N/A'}`
    );
  }
}
