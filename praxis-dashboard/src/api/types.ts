/**
 * Wire types for the Praxis dashboard.
 *
 * Mirrored field-for-field from the locked backend contracts
 * (`backend/app/contracts/`) so a drift between the two surfaces fails type-checking
 * rather than silently rendering a wrong number.
 *
 * Two vocabularies are carried here and are NOT interchangeable
 * (SRS Sec.16 / docs/design.md Sec.2.1):
 *   - `PolicyAction` describes what the organisation does.
 *   - `ModuleStatus`  describes whether evidence exists and can be trusted.
 */

/* ------------------------------------------------------------------ *
 * Locked enumerations (backend/app/contracts/enums.py)
 * ------------------------------------------------------------------ */

export type ModuleStatus = 'AVAILABLE' | 'LOW_QUALITY' | 'UNAVAILABLE' | 'ERROR';

export type EvidenceFamily =
  | 'ACOUSTIC'
  | 'PROSODY'
  | 'SPEAKER'
  | 'LINGUISTIC'
  | 'AI_WRITTEN'
  | 'CONTEXT';

export type PolicyAction =
  | 'ALLOW'
  | 'WARN'
  | 'SECONDARY_VERIFICATION'
  | 'ESCALATE'
  | 'HOLD';

export type SpeakerVerificationResult = 'MATCH' | 'UNCERTAIN' | 'MISMATCH' | 'UNAVAILABLE';

/** SRS Sec.8. RawNet2 is deliberately absent; it is not part of locked V1. */
export type AntiSpoofModel = 'W2V2_AASIST' | 'WAVLM_ANTISPOOF' | 'AASIST';

/** SRS Sec.11.2 - exactly eight locked multi-label categories. */
export type SocialEngineeringLabel =
  | 'urgency'
  | 'secrecy'
  | 'authority_pressure'
  | 'financial_request'
  | 'credential_request'
  | 'verification_bypass'
  | 'coercion'
  | 'emotional_pressure';

/** The role a stream connection takes (backend/app/streaming/ws.py). */
export type StreamMode = 'analyze' | 'observe';

export type UserRole = 'admin' | 'analyst' | 'host';
export type SessionState = 'CREATED' | 'ACTIVE' | 'ENDED';
export type RiskModelStatus = 'UNVALIDATED' | 'VALIDATED';
export type EnrollmentStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVOKED';

export const ANTI_SPOOF_MODELS: readonly AntiSpoofModel[] = [
  'W2V2_AASIST',
  'WAVLM_ANTISPOOF',
  'AASIST',
];

export const ANTI_SPOOF_LABELS: Record<AntiSpoofModel, string> = {
  W2V2_AASIST: 'W2V2-AASIST',
  WAVLM_ANTISPOOF: 'WavLM anti-spoof',
  AASIST: 'AASIST',
};

export const SOCIAL_ENGINEERING_LABELS: readonly SocialEngineeringLabel[] = [
  'urgency',
  'secrecy',
  'authority_pressure',
  'financial_request',
  'credential_request',
  'verification_bypass',
  'coercion',
  'emotional_pressure',
];

export const SOCIAL_ENGINEERING_TEXT: Record<SocialEngineeringLabel, string> = {
  urgency: 'Urgency',
  secrecy: 'Secrecy',
  authority_pressure: 'Authority pressure',
  financial_request: 'Financial request',
  credential_request: 'Credential request',
  verification_bypass: 'Verification bypass',
  coercion: 'Coercion',
  emotional_pressure: 'Emotional pressure',
};

/** SRS Sec.13 - the nine permitted context inputs. Absent means UNKNOWN. */
export const CONTEXT_FIELDS = [
  'known_contact',
  'claimed_role',
  'department',
  'transaction_type',
  'amount',
  'beneficiary',
  'workflow_state',
  'time',
  'historical_risk',
] as const;

export type ContextField = (typeof CONTEXT_FIELDS)[number];

export const CONTEXT_FIELD_TEXT: Record<ContextField, string> = {
  known_contact: 'Known contact',
  claimed_role: 'Claimed role',
  department: 'Department',
  transaction_type: 'Transaction type',
  amount: 'Amount',
  beneficiary: 'Beneficiary',
  workflow_state: 'Workflow state',
  time: 'Time',
  historical_risk: 'Historical risk',
};

/** SRS Sec.13.1 - rule flags with the locked demo default weights. */
export const CONTEXT_RULES = [
  'unknown_contact',
  'claimed_role_mismatch',
  'new_beneficiary',
  'unusual_amount',
  'workflow_violation',
  'unusual_time',
  'historical_risk_indicator',
] as const;

export type ContextRule = (typeof CONTEXT_RULES)[number];

export const CONTEXT_RULE_TEXT: Record<ContextRule, string> = {
  unknown_contact: 'Unknown contact',
  claimed_role_mismatch: 'Claimed role mismatch',
  new_beneficiary: 'New beneficiary',
  unusual_amount: 'Unusual amount',
  workflow_violation: 'Workflow violation',
  unusual_time: 'Unusual time',
  historical_risk_indicator: 'Historical risk indicator',
};

/** SRS Sec.15 - the locked default action bands. */
export const POLICY_BANDS: ReadonlyArray<readonly [number, number, PolicyAction]> = [
  [0, 39, 'ALLOW'],
  [40, 59, 'WARN'],
  [60, 79, 'SECONDARY_VERIFICATION'],
  [80, 89, 'ESCALATE'],
  [90, 100, 'HOLD'],
];

export const ACTION_TEXT: Record<PolicyAction, string> = {
  ALLOW: 'ALLOW',
  WARN: 'WARN',
  SECONDARY_VERIFICATION: 'SECONDARY VERIFICATION',
  ESCALATE: 'ESCALATE',
  HOLD: 'HOLD',
};

export const ACTION_DESCRIPTION: Record<PolicyAction, string> = {
  ALLOW: 'No intervention. Risk index 0-39.',
  WARN: 'Advise the operator. Risk index 40-59.',
  SECONDARY_VERIFICATION: 'Require a second verification step. Risk index 60-79.',
  ESCALATE: 'Escalate to a human reviewer. Risk index 80-89.',
  HOLD: 'Pause the protected workflow. Risk index 90-100.',
};

export const STATUS_TEXT: Record<ModuleStatus, string> = {
  AVAILABLE: 'AVAILABLE',
  LOW_QUALITY: 'LOW QUALITY',
  UNAVAILABLE: 'UNAVAILABLE',
  ERROR: 'ERROR',
};

export const FAMILY_TEXT: Record<EvidenceFamily, string> = {
  ACOUSTIC: 'Acoustic',
  PROSODY: 'Prosody',
  SPEAKER: 'Speaker',
  LINGUISTIC: 'Linguistic',
  AI_WRITTEN: 'AI-written language',
  CONTEXT: 'Context',
};

/** Maps a displayed risk value to its locked band. Mirrors `band_for_risk`. */
export function bandForRisk(risk: number): PolicyAction | null {
  for (const band of POLICY_BANDS) {
    if (risk >= band[0] && risk <= band[1]) return band[2];
  }
  return null;
}

/* ------------------------------------------------------------------ *
 * Evidence records (backend/app/contracts/evidence.py)
 * ------------------------------------------------------------------ */

export interface EvidenceBase {
  module: string;
  family: EvidenceFamily;
  model_version: string;
  status: ModuleStatus;
  quality: ModuleStatus | null;
  latency_ms: number | null;
  reason_codes: string[];
  timestamp: string;
}

export interface AntiSpoofEvidence extends EvidenceBase {
  module: 'anti_spoof';
  family: 'ACOUSTIC';
  detector: AntiSpoofModel;
  native_score: number | null;
  raw_spoof_score: number | null;
  calibrated_spoof_score: number | null;
  calibration_version: string | null;
}

export interface AcousticFusionEvidence extends EvidenceBase {
  module: 'acoustic_fusion';
  family: 'ACOUSTIC';
  calibrated_spoof_score: number | null;
  fusion_model_version: string | null;
  detectors_present: AntiSpoofModel[];
  detectors_missing: AntiSpoofModel[];
}

export interface ProsodyEvidence extends EvidenceBase {
  module: 'prosody';
  family: 'PROSODY';
  calibrated_prosody_score: number | null;
  calibration_version: string | null;
  features: Record<string, number> | null;
  features_omitted: string[];
}

export interface SpeakerEvidence extends EvidenceBase {
  module: 'speaker';
  family: 'SPEAKER';
  result: SpeakerVerificationResult;
  /** SRS Sec.16: never present when `result` is UNAVAILABLE. */
  claimed_identity: string | null;
  cosine_similarity: number | null;
  embedding_model_version: string | null;
}

export interface LinguisticEvidence extends EvidenceBase {
  module: 'linguistic';
  family: 'LINGUISTIC';
  activated_labels: SocialEngineeringLabel[];
  label_scores: Record<string, number> | null;
  rule_reason_codes: string[];
  aggregate_linguistic_score: number | null;
  transcript_language: string | null;
  analysed_in_english: boolean;
}

export interface TranscriptSegment {
  start_ms: number;
  end_ms: number;
  text: string;
}

export interface ASREvidence extends EvidenceBase {
  module: 'asr';
  family: 'LINGUISTIC';
  language: string | null;
  language_confidence: number | null;
  segments: TranscriptSegment[] | null;
  model_name: string;
}

export interface AIWrittenEvidence extends EvidenceBase {
  module: 'ai_written';
  family: 'AI_WRITTEN';
  fused_ai_written_score: number | null;
  binoculars_style_score: number | null;
  lm_statistics_score: number | null;
  fusion_model_version: string | null;
  calibration_version: string | null;
  normalized_token_count: number;
  /** Locked limitation (SRS Sec.12 / Sec.35). Always false in V1. */
  may_trigger_hold_alone: boolean;
}

export interface ContextEvidence extends EvidenceBase {
  module: 'context';
  family: 'CONTEXT';
  context_score: number | null;
  activated_rules: string[];
  unknown_fields: string[];
  available_fields: string[];
  weights_version: string | null;
}

export type ModuleEvidence =
  | AntiSpoofEvidence
  | AcousticFusionEvidence
  | ProsodyEvidence
  | SpeakerEvidence
  | LinguisticEvidence
  | ASREvidence
  | AIWrittenEvidence
  | ContextEvidence;

/* ------------------------------------------------------------------ *
 * Risk and policy (backend/app/contracts/risk.py, policy.py)
 * ------------------------------------------------------------------ */

export interface EvidenceSummary {
  family: EvidenceFamily;
  module: string;
  status: ModuleStatus;
  reason_codes: string[];
}

export interface RiskEvent {
  call_id: string;
  window_id: string;
  risk_raw_0_100: number;
  risk_display_0_100: number;
  evidence_summary: EvidenceSummary[];
  quality: ModuleStatus | null;
  missing_evidence_families: EvidenceFamily[];
  risk_model_version: string;
  model_status: RiskModelStatus;
  timestamp: string;
}

export interface PolicyEvent {
  policy_version: string;
  action: PolicyAction;
  triggering_rule: string;
  threshold_band: [number, number] | null;
  recommended_workflow: string | null;
  host_supports_hold: boolean;
  timestamp: string;
}

export interface AuditEvent {
  audit_id: string;
  tenant_id: string;
  session_id: string;
  call_id: string;
  window_id: string | null;
  event_type: string;
  recorded_at: string;
  model_versions: Record<string, string>;
  calibration_versions: Record<string, string>;
  risk_model_version: string | null;
  policy_version: string | null;
  evidence_summaries: EvidenceSummary[];
  final_risk_0_100: number | null;
  final_action: PolicyAction | null;
  status: ModuleStatus | null;
}

/* ------------------------------------------------------------------ *
 * Sessions (backend/app/contracts/session.py)
 * ------------------------------------------------------------------ */

export interface SessionContext {
  known_contact?: boolean | null;
  claimed_role?: string | null;
  department?: string | null;
  transaction_type?: string | null;
  /** pydantic serialises `Decimal` as a JSON string; accept either form. */
  amount?: string | number | null;
  beneficiary?: string | null;
  workflow_state?: string | null;
  time?: string | null;
  historical_risk?: boolean | null;
}

export interface SessionStartRequest {
  caller_name?: string | null;
  caller_number?: string | null;
  call_id: string;
  host_app_id: string;
  claimed_identity?: string | null;
  context?: SessionContext;
}

export interface SessionStartResponse {
  session_id: string;
  tenant_id: string;
  call_id: string;
  host_app_id: string;
  claimed_identity: string | null;
  context: SessionContext;
  state: SessionState;
  created_at: string;
}

export interface SessionListItem extends SessionSummary {
  analysis_active: boolean;
}

export interface SessionSummary {
  caller_name: string | null;
  caller_number: string | null;
  session_id: string;
  tenant_id: string;
  call_id: string;
  host_app_id: string;
  state: SessionState;
  created_at: string;
  ended_at: string | null;
  windows_received: number;
  windows_rejected: number;
  duplicate_windows: number;
  latest_risk: RiskEvent | null;
  latest_policy: PolicyEvent | null;
}

export interface AuditResponse {
  session_id: string;
  tenant_id: string;
  events: AuditEvent[];
}

/* ------------------------------------------------------------------ *
 * Auth (backend/app/api/v1/auth.py)
 * ------------------------------------------------------------------ */

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  role: UserRole;
  tenant_id: string;
}

/* ------------------------------------------------------------------ *
 * Health (backend/app/api/v1/health.py)
 * ------------------------------------------------------------------ */

export interface StageHealth {
  stage: string;
  title: string;
  status: ModuleStatus;
  srs_ref: string;
  planned_phase: number;
  /** Why the stage reports what it reports; same text as the WSS pipeline.status event. */
  detail: string;
}

/**
 * One anti-spoof detector's live availability (backend/app/api/v1/health.py).
 *
 * AVAILABLE means the adapter is implemented *and* its checkpoint resolved and verified.
 * UNAVAILABLE carries the blocking reason code, so a partially provisioned deployment is
 * visible here rather than being inferred from scores that never arrive.
 */
export interface DetectorHealth {
  model: AntiSpoofModel;
  display_name: string;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
}

export interface AntiSpoofHealth {
  ready: boolean;
  summary: string;
  detectors: DetectorHealth[];
}

/**
 * Live readiness of one module's versioned artefacts (backend/app/api/v1/health.py).
 *
 * These blocks answer a question `stages[]` cannot: a stage can be implemented and still be
 * unprovisioned. `reason_code` names what is missing, and a version is reported only when the
 * verified bytes behind it resolved, so the block never implies a model that is not on disk.
 */
export interface ProsodyHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  model_version: string;
  calibration_version: string | null;
}

export interface SpeakerHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  model_version: string;
  threshold_version: string | null;
}

export interface AsrHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  model_version: string;
}

export interface LinguisticHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  model_version: string;
  encoder_version: string | null;
}

export interface AIWrittenHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  model_version: string;
  observer_version: string | null;
  performer_version: string | null;
  min_tokens: number;
}

export interface FusionHealth {
  available: boolean;
  status: ModuleStatus;
  detail: string;
  fusion_version: string | null;
  fitted_on_split: string | null;
}

export interface RiskHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  risk_model_version: string | null;
  model_status: string | null;
  dataset_version: string | null;
  fitted_on_split: string | null;
  ema_alpha: number;
  validation_report: string | null;
}

export interface PolicyHealth {
  available: boolean;
  status: ModuleStatus;
  reason_code: string | null;
  detail: string;
  policy_version: string | null;
  document_path: string;
  host_supports_hold: boolean;
  bands: string[];
  overrides: string[];
}

export interface RetentionRuleHealth {
  data_class: string;
  disposition: string;
  configurable: boolean;
  srs_ref: string;
  detail: string;
}

/**
 * The SRS Sec.18 controls and the SRS Sec.17 retention policy, as the live process reports them.
 *
 * These are configuration and enforcement facts rather than model artefacts. The one that
 * matters most for the demo is `raw_audio_retention_enabled`, which is reported even though it
 * can only ever be false: a reader asking the Appendix D question should not have to infer the
 * answer from a missing field.
 */
export interface SecurityHealth {
  available: boolean;
  status: ModuleStatus;
  detail: string;
  retention_policy_version: string;
  transcript_retention: string;
  enrollment_audio_retention: string;
  raw_audio_retention_enabled: boolean;
  retention_rules: RetentionRuleHealth[];
  response_headers: string[];
  http_rate_limit_enabled: boolean;
  rate_limit_exempt_paths: string[];
  max_http_body_bytes: number;
  max_message_bytes: number;
  max_audio_payload_bytes: number;
  max_total_analyze_streams: number;
  max_analyze_streams_per_tenant: number;
  active_analyze_streams: number;
  log_redaction_installed: boolean;
}

export interface HealthResponse {
  service: string;
  service_version: string;
  status: string;
  analysis_implemented: boolean;
  policy_version: string;
  context_weights_version: string;
  persistence: string;
  stages: StageHealth[];
  anti_spoof: AntiSpoofHealth;
  prosody: ProsodyHealth;
  speaker: SpeakerHealth;
  asr: AsrHealth;
  linguistic: LinguisticHealth;
  ai_written: AIWrittenHealth;
  fusion: FusionHealth;
  risk: RiskHealth;
  policy: PolicyHealth;
  security: SecurityHealth;
  checked_at: string;
}

/* ------------------------------------------------------------------ *
 * Streaming envelope (backend/app/contracts/events.py)
 * ------------------------------------------------------------------ */

export interface AudioWindowAck {
  call_id: string;
  window_id: string;
  sequence_number: number;
  accepted: boolean;
  duplicate: boolean;
}

export interface PipelineStage {
  stage: string;
  status: ModuleStatus;
  detail: string;
}

export interface PipelineStatusMessage {
  type: 'pipeline.status';
  session_id: string;
  analysis_implemented: boolean;
  stages: PipelineStage[];
  sent_at: string;
}

/**
 * The role this connection was given, and whether the session has a live audio source.
 *
 * The socket carries a `stream_mode` query parameter: `analyze` connections own the audio
 * input, `observe` connections are read-only. The backend re-sends this event whenever an
 * audio source attaches or detaches, so `analysis_active` is live rather than a snapshot
 * taken at connect time.
 */
export interface StreamStateMessage {
  type: 'stream.state';
  session_id: string;
  stream_mode: StreamMode;
  can_submit_audio: boolean;
  analysis_active: boolean;
  observer_count: number;
  detail: string;
  sent_at: string;
}

export interface WindowAckMessage {
  type: 'window.ack';
  ack: AudioWindowAck;
  sent_at: string;
}

export interface ModuleEvidenceMessage {
  type: 'evidence.module';
  evidence: ModuleEvidence;
  sent_at: string;
}

export interface RiskUpdateMessage {
  type: 'risk.update';
  risk: RiskEvent;
  sent_at: string;
}

export interface PolicyActionMessage {
  type: 'policy.action';
  policy: PolicyEvent;
  sent_at: string;
}

export interface ErrorMessage {
  type: 'error';
  code: string;
  message: string;
  sent_at: string;
}

export interface HeartbeatAckMessage {
  type: 'heartbeat.ack';
  sent_at: string;
}

export interface SessionClosedMessage {
  type: 'session.closed';
  reason: string;
  sent_at: string;
}

export interface AuditEventMessage {
  type: 'audit.event';
  audit: AuditEvent;
  sent_at: string;
}

export type ServerMessage =
  | PipelineStatusMessage
  | StreamStateMessage
  | WindowAckMessage
  | ModuleEvidenceMessage
  | RiskUpdateMessage
  | PolicyActionMessage
  | ErrorMessage
  | HeartbeatAckMessage
  | SessionClosedMessage
  | AuditEventMessage;
