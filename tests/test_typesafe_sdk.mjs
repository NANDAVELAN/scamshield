/**
 * Unit & Integration Tests for @typesafe-ai/sdk and ScamShield TypeSafe Integration
 */
import { TypeSafeClient, noul, choice, score, AuthenticationError, TypeSafeError } from '@typesafe-ai/sdk';
import { getScamShieldQuestions, triageWithTypeSafe } from '../app/typesafe_triage.mjs';
import assert from 'assert';

console.log('=== [1/5] Testing SDK Exports & Schema Builders ===');
const questions = getScamShieldQuestions();
assert.strictEqual(questions.is_scam.type, 'noul', 'is_scam must be noul question');
assert.strictEqual(questions.scam_type.type, 'choice', 'scam_type must be choice question');
assert.strictEqual(questions.urgency.type, 'score', 'urgency must be score question');
assert(Array.isArray(questions.urgency.criteria), 'urgency criteria must be an array');
assert.strictEqual(questions.urgency.criteria.length, 11, 'urgency rubric must have 11 tiers (0-10)');
console.log('  PASS: All question schemas correctly generated via @typesafe-ai/sdk builders');

console.log('\n=== [2/5] Testing Missing Key Validation ===');
let missingKeyThrew = false;
const savedKey = process.env.TYPESAFE_API_KEY;
delete process.env.TYPESAFE_API_KEY;
try {
  new TypeSafeClient();
} catch (e) {
  missingKeyThrew = true;
  assert(e instanceof TypeSafeError || e.message.includes('No API key'), 'Should throw TypeSafeError');
  console.log('  PASS: Threw expected error:', e.message);
} finally {
  if (savedKey) process.env.TYPESAFE_API_KEY = savedKey;
}
assert(missingKeyThrew, 'Client must reject instantiation without API key');

console.log('\n=== [3/5] Testing Client Configuration with Mock Key ===');
const client = new TypeSafeClient({ apiKey: 'ts_mock_test_key_abc123' });
assert.strictEqual(client.baseURL, 'https://api.typesafe.ai');
assert.strictEqual(client.defaultModel, 'jev-latest');
console.log('  PASS: TypeSafeClient initialized with default baseURL and model');

console.log('\n=== [4/5] Testing API Error Handling (Live HTTP 401 Authentication Failure) ===');
try {
  await client.systemOne({
    state: 'URGENT: Verify OTP 9821 for your HDFC transfer of Rs 50,000.',
    questions: {
      is_scam: noul('Is this message a scam?')
    }
  });
  console.log('  UNEXPECTED: Request succeeded with mock key');
} catch (err) {
  assert(err instanceof AuthenticationError, `Expected AuthenticationError but got ${err.name}`);
  assert.strictEqual(err.status, 401, 'Status code must be 401');
  console.log(`  PASS: Caught ${err.name} (HTTP ${err.status}): ${err.message}`);
}

console.log('\n=== [5/5] Testing ScamShield Graceful Degradation & Fallback ===');
const sampleMessage = {
  channel: 'sms',
  sender: 'AD-TRAFFIC',
  body: 'Notice: E-challan pending Rs 1000 for speeding. Pay within 24h at http://traffic-court-pay.top or DL cancelled.'
};

// Calling triageWithTypeSafe with an invalid key should return a safe fallback object without crashing
const result = await triageWithTypeSafe(sampleMessage, { apiKey: 'invalid_key' });
assert.strictEqual(result.success, false, 'Expected success=false for invalid key');
assert.strictEqual(result.status_code, 401, 'Expected status_code=401');
assert.strictEqual(result.error_name, 'AuthenticationError', 'Expected AuthenticationError');
assert.strictEqual(result.source, 'typesafe_fallback', 'Expected source=typesafe_fallback');
console.log('  PASS: Module degraded cleanly without crashing:', {
  success: result.success,
  status_code: result.status_code,
  error_name: result.error_name,
  latency_ms: result.latency_ms
});

console.log('\n======================================================');
console.log(' ALL 5 TYPESAFE SDK TESTS PASSED SUCCESSFULLY! ');
console.log('======================================================');
