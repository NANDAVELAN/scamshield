/**
 * TypeSafe AI (Jev System One) Reflex Client for ScamShield
 * Uses the official @typesafe-ai/sdk Node.js package
 */
import { TypeSafeClient, noul, choice, score, AuthenticationError, APIError } from '@typesafe-ai/sdk';
import path from 'path';
import fs from 'fs';

// Lightweight .env reader without extra third-party dependencies
function loadEnv() {
  const possiblePaths = ['.env', '../.env', path.join(process.cwd(), '.env'), path.join(process.cwd(), '..', '.env')];
  for (const envPath of possiblePaths) {
    if (fs.existsSync(envPath)) {
      try {
        const content = fs.readFileSync(envPath, 'utf8');
        for (const line of content.split(/\r?\n/)) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          const idx = trimmed.indexOf('=');
          if (idx > 0) {
            const key = trimmed.slice(0, idx).trim();
            const val = trimmed.slice(idx + 1).trim();
            if (!process.env[key]) {
              process.env[key] = val;
            }
          }
        }
      } catch (_) {}
      break;
    }
  }
}

loadEnv();

/**
 * Builds the TypeSafe System One Question Rubric for ScamShield
 */
export function getScamShieldQuestions() {
  return {
    is_scam: noul('Is this message a scam, phishing attempt, or fraudulent lure?'),
    scam_type: choice('Which scam category best matches this message?', {
      fake_kyc: 'Bank or KYC block warning with phishing link',
      upi_refund: 'Fake refund, cashback, or QR code payment request',
      courier: 'Held parcel or failed delivery fee extortion',
      bill_disconnect: 'Electricity or water power cut threat',
      job_offer: 'Unsolicited high-paying part-time job or YouTube task scam',
      digital_arrest: 'Police, CBI, or customs arrest threat',
      lottery: 'Prize, lottery, or gift claim notification',
      otp_request: 'Direct request for OTP, PIN, or verification credentials',
      illegal_narcotics: 'Threat regarding parcel containing illegal narcotics or contraband',
      other: 'Other fraudulent pattern',
      none: 'Legitimate personal or transactional communication'
    }),
    urgency: score('Rate the level of urgency, panic, or coercive pressure from 0 to 10', [
      null, null, null, null, null, null, null, null, null, null, null
    ]),
    impersonates_brand: noul('Does the message impersonate a known bank, government body, or recognized brand?')
  };
}

/**
 * Execute TypeSafe System One triage on an incoming notification
 * @param {Object} message - { sender: string, body: string, subject?: string }
 * @param {Object} [options] - Optional client configuration override
 * @returns {Promise<Object>} Formatted triage result
 */
export async function triageWithTypeSafe(message, options = {}) {
  const apiKey = (options.apiKey || process.env.TYPESAFE_API_KEY || process.env.JEV_API_KEY || '').trim();
  if (!apiKey || apiKey === 'your_typesafe_api_key_here') {
    return {
      success: false,
      error: 'Missing or placeholder TYPESAFE_API_KEY',
      source: 'typesafe_error'
    };
  }

  const client = new TypeSafeClient({
    apiKey: apiKey,
    baseURL: options.baseURL || process.env.TYPESAFE_BASE_URL || 'https://api.typesafe.ai'
  });

  const stateText = `Channel: ${message.channel || 'notification'} | Sender: ${message.sender || 'Unknown'} | Body: ${message.body || ''}`;
  const questions = getScamShieldQuestions();

  const startTime = Date.now();
  try {
    const res = await client.systemOne({
      state: stateText,
      questions: questions,
      model: options.model || 'jev-latest'
    });

    const elapsed = Date.now() - startTime;
    const answers = res.answers || {};

    const prob = typeof answers.is_scam?.noul === 'number' ? answers.is_scam.noul : 0.5;
    const scamType = answers.scam_type?.choice || 'other';
    const urgency = typeof answers.urgency?.score === 'number' ? answers.urgency.score : 5;
    const brandImp = typeof answers.impersonates_brand?.noul === 'number' ? answers.impersonates_brand.noul : 0.0;

    return {
      success: true,
      scam_probability: prob,
      scam_type: scamType,
      urgency: urgency,
      impersonates_brand: brandImp,
      source: 'typesafe_jev',
      latency_ms: elapsed,
      status: prob >= 0.2 ? 'escalated' : 'passed',
      reason: `TypeSafe Jev classified as ${scamType} (p=${prob.toFixed(2)})`,
      model: res.model || 'jev-latest'
    };
  } catch (err) {
    const elapsed = Date.now() - startTime;
    return {
      success: false,
      error: err.message,
      status_code: err.status || 500,
      error_name: err.name,
      latency_ms: elapsed,
      source: 'typesafe_fallback'
    };
  }
}

// CLI runner if executed directly
if (process.argv[1] && process.argv[1].replace(/\\/g, '/').endsWith('app/typesafe_triage.mjs')) {
  console.log('Testing TypeSafe AI SDK reflex client...');
  const sample = {
    sender: '+91 9876543210',
    body: 'URGENT: Electricity will be disconnected tonight at 9:30 PM due to unpaid bill. Call 9876543210 immediately.'
  };

  triageWithTypeSafe(sample).then(res => {
    console.log('Result:', JSON.stringify(res, null, 2));
  });
}
