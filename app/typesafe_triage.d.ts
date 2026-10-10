import { Questions } from '@typesafe-ai/sdk';

export interface ScamShieldMessage {
  channel?: 'whatsapp' | 'sms' | 'gmail' | 'notification' | string;
  sender?: string;
  body: string;
  subject?: string;
}

export interface TypeSafeTriageResult {
  success: boolean;
  scam_probability?: number;
  scam_type?: string;
  urgency?: number;
  impersonates_brand?: number;
  source: 'typesafe_jev' | 'typesafe_error' | 'typesafe_fallback';
  latency_ms?: number;
  status?: 'escalated' | 'passed';
  reason?: string;
  model?: string;
  error?: string;
  status_code?: number;
  error_name?: string;
}

export interface TypeSafeOptions {
  apiKey?: string;
  baseURL?: string;
  model?: string;
}

export declare function getScamShieldQuestions(): Questions;

export declare function triageWithTypeSafe(
  message: ScamShieldMessage,
  options?: TypeSafeOptions
): Promise<TypeSafeTriageResult>;
