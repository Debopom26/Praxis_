# Supplied contract type index

Generated from the supplied `Contracts.kt`; these are DTOs/enums, not additional client methods. Field names and defaults below are copied from source. The canonical generator/schema sources are absent.

## AIWrittenEvidence — Contracts.kt:9
```kotlin
data class AIWrittenEvidence(
    @SerialName("type") val type: String = "evidence",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String? = null,
    @SerialName("module") val module: String,
    @SerialName("model_version") val modelVersion: String?,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("raw_score") val rawScore: Double? = null,
    @SerialName("features") val features: Map<String, Double?>? = null,
    @SerialName("calibrated_score") val calibratedScore: Double? = null,
    @SerialName("quality") val quality: Map<String, Double?>? = null,
    @SerialName("latency_ms") val latencyMs: Double,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("provenance") val provenance: Provenance? = null,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("normalized_token_count") val normalizedTokenCount: Long,
    @SerialName("supporting_only") val supportingOnly: Boolean = true,
)
```

## AckEvent — Contracts.kt:29
```kotlin
data class AckEvent(
    @SerialName("type") val type: String = "ack",
    @SerialName("sequence_id") val sequenceId: Long,
)
```

## AnalysisGapEvent — Contracts.kt:35
```kotlin
data class AnalysisGapEvent(
    @SerialName("type") val type: String = "analysis_gap",
    @SerialName("reason_codes") val reasonCodes: List<String>,
)
```

## ArtifactState — Contracts.kt:41
```kotlin
enum class ArtifactState {
    @SerialName("NOT_LOADED") NOT_LOADED,
    @SerialName("UNVALIDATED") UNVALIDATED,
    @SerialName("VALIDATED") VALIDATED,
}
```

## AudioFormat — Contracts.kt:48
```kotlin
data class AudioFormat(
    @SerialName("encoding") val encoding: String = "pcm_s16le",
    @SerialName("sample_rate") val sampleRate: Long,
    @SerialName("channels") val channels: Long,
)
```

## AudioFrame — Contracts.kt:55
```kotlin
data class AudioFrame(
    @SerialName("type") val type: String = "audio",
    @SerialName("sequence_id") val sequenceId: Long,
    @SerialName("timestamp_ms") val timestampMs: Long,
    @SerialName("format") val format: AudioFormat,
    @SerialName("audio_base64") val audioBase64: String,
)
```

## AudioQuality — Contracts.kt:64
```kotlin
data class AudioQuality(
    @SerialName("clipping_ratio") val clippingRatio: Double,
    @SerialName("silence_ratio") val silenceRatio: Double,
    @SerialName("snr_proxy_db") val snrProxyDb: Double?,
    @SerialName("duration_ms") val durationMs: Double,
    @SerialName("completeness") val completeness: Double,
    @SerialName("reason_codes") val reasonCodes: List<String>? = null,
)
```

## AudioWindow — Contracts.kt:74
```kotlin
data class AudioWindow(
    @SerialName("type") val type: String = "audio_window",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String,
    @SerialName("sequence_id") val sequenceId: Long,
    @SerialName("start_ms") val startMs: Double,
    @SerialName("end_ms") val endMs: Double,
    @SerialName("audio_reference") val audioReference: String,
    @SerialName("original_sample_rate") val originalSampleRate: Long,
    @SerialName("original_channels") val originalChannels: Long,
    @SerialName("analysis_sample_rate") val analysisSampleRate: Long,
    @SerialName("speech_spans") val speechSpans: List<SpeechSpan>,
    @SerialName("vad_model_version") val vadModelVersion: String,
    @SerialName("quality") val quality: AudioQuality,
    @SerialName("timestamp") val timestamp: String,
)
```

## AuditEvent — Contracts.kt:92
```kotlin
data class AuditEvent(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("event_id") val eventId: String,
    @SerialName("event_type") val eventType: String,
    @SerialName("call_id") val callId: String? = null,
    @SerialName("window_id") val windowId: String? = null,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("model_versions") val modelVersions: Map<String, String>? = null,
    @SerialName("calibration_versions") val calibrationVersions: Map<String, String>? = null,
    @SerialName("risk_model_version") val riskModelVersion: String? = null,
    @SerialName("policy_version") val policyVersion: String? = null,
    @SerialName("profile_version") val profileVersion: String? = null,
    @SerialName("threshold_version") val thresholdVersion: String? = null,
    @SerialName("context_config_version") val contextConfigVersion: String? = null,
    @SerialName("retention_config_version") val retentionConfigVersion: String? = null,
    @SerialName("evidence_summary") val evidenceSummary: List<EvidenceSummary>? = null,
    @SerialName("final_risk") val finalRisk: Double? = null,
    @SerialName("action") val action: PolicyAction? = null,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("quality") val quality: Map<String, Double?>? = null,
    @SerialName("reason_codes") val reasonCodes: List<String>? = null,
)
```

## ComponentHealth — Contracts.kt:117
```kotlin
data class ComponentHealth(
    @SerialName("status") val status: ModuleStatus,
    @SerialName("version") val version: String? = null,
    @SerialName("reason_codes") val reasonCodes: List<String>? = null,
)
```

## ConnectionEvent — Contracts.kt:124
```kotlin
data class ConnectionEvent(
    @SerialName("type") val type: String = "connection",
    @SerialName("status") val status: String = "AVAILABLE",
    @SerialName("session_id") val sessionId: String,
    @SerialName("contract_version") val contractVersion: String,
    @SerialName("last_sequence_id") val lastSequenceId: Long,
    @SerialName("last_timestamp_ms") val lastTimestampMs: Long,
    @SerialName("reason_codes") val reasonCodes: List<String>,
)
```

## ContextConfig — Contracts.kt:135
```kotlin
data class ContextConfig(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("version") val version: String,
    @SerialName("weights") val weights: Map<String, Double>? = null,
    @SerialName("operating_start") val operatingStart: String? = null,
    @SerialName("operating_end") val operatingEnd: String? = null,
    @SerialName("timezone") val timezone: String? = null,
)
```

## ContextEvidence — Contracts.kt:145
```kotlin
data class ContextEvidence(
    @SerialName("type") val type: String = "context",
    @SerialName("call_id") val callId: String,
    @SerialName("config_version") val configVersion: String,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("flags") val flags: Map<String, RuleFlag>,
    @SerialName("context_score") val contextScore: Double?,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("timestamp") val timestamp: String,
)
```

## ContextInput — Contracts.kt:157
```kotlin
data class ContextInput(
    @SerialName("known_contact") val knownContact: Boolean? = null,
    @SerialName("claimed_role") val claimedRole: String? = null,
    @SerialName("expected_role") val expectedRole: String? = null,
    @SerialName("department") val department: String? = null,
    @SerialName("transaction_type") val transactionType: String? = null,
    @SerialName("amount") val amount: Double? = null,
    @SerialName("allowed_amount") val allowedAmount: Double? = null,
    @SerialName("beneficiary") val beneficiary: String? = null,
    @SerialName("beneficiary_known") val beneficiaryKnown: Boolean? = null,
    @SerialName("workflow_state") val workflowState: String? = null,
    @SerialName("workflow_permitted") val workflowPermitted: Boolean? = null,
    @SerialName("time") val time: String? = null,
    @SerialName("historical_risk") val historicalRisk: Boolean? = null,
)
```

## EnrollmentRequest — Contracts.kt:174
```kotlin
data class EnrollmentRequest(
    @SerialName("session_id") val sessionId: String,
    @SerialName("identity") val identity: String,
    @SerialName("approved") val approved: Boolean,
    @SerialName("clips_base64") val clipsBase64: List<String>,
)
```

## EvidenceSummary — Contracts.kt:182
```kotlin
data class EvidenceSummary(
    @SerialName("module") val module: String,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("model_version") val modelVersion: String? = null,
)
```

## HealthStatus — Contracts.kt:190
```kotlin
data class HealthStatus(
    @SerialName("service_version") val serviceVersion: String,
    @SerialName("contract_version") val contractVersion: String,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("components") val components: Map<String, ComponentHealth>,
    @SerialName("artifacts") val artifacts: List<ModelArtifactStatus>,
    @SerialName("timestamp") val timestamp: String,
)
```

## LinguisticEvidence — Contracts.kt:200
```kotlin
data class LinguisticEvidence(
    @SerialName("type") val type: String = "evidence",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String? = null,
    @SerialName("module") val module: String,
    @SerialName("model_version") val modelVersion: String?,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("raw_score") val rawScore: Double? = null,
    @SerialName("features") val features: Map<String, Double?>? = null,
    @SerialName("calibrated_score") val calibratedScore: Double? = null,
    @SerialName("quality") val quality: Map<String, Double?>? = null,
    @SerialName("latency_ms") val latencyMs: Double,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("provenance") val provenance: Provenance? = null,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("rule_labels") val ruleLabels: List<LinguisticLabel>? = null,
    @SerialName("classifier_scores") val classifierScores: Map<String, Double>? = null,
    @SerialName("classifier_state") val classifierState: ArtifactState = ArtifactState.NOT_LOADED,
)
```

## LinguisticLabel — Contracts.kt:221
```kotlin
enum class LinguisticLabel {
    @SerialName("urgency") URGENCY,
    @SerialName("secrecy") SECRECY,
    @SerialName("authority_pressure") AUTHORITY_PRESSURE,
    @SerialName("financial_request") FINANCIAL_REQUEST,
    @SerialName("credential_request") CREDENTIAL_REQUEST,
    @SerialName("verification_bypass") VERIFICATION_BYPASS,
    @SerialName("coercion") COERCION,
    @SerialName("emotional_pressure") EMOTIONAL_PRESSURE,
}
```

## ModelArtifactStatus — Contracts.kt:233
```kotlin
data class ModelArtifactStatus(
    @SerialName("module") val module: String,
    @SerialName("state") val state: ArtifactState,
    @SerialName("version") val version: String? = null,
    @SerialName("reason_codes") val reasonCodes: List<String>? = null,
)
```

## ModuleEvidence — Contracts.kt:241
```kotlin
data class ModuleEvidence(
    @SerialName("type") val type: String = "evidence",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String? = null,
    @SerialName("module") val module: String,
    @SerialName("model_version") val modelVersion: String?,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("raw_score") val rawScore: Double? = null,
    @SerialName("features") val features: Map<String, Double?>? = null,
    @SerialName("calibrated_score") val calibratedScore: Double? = null,
    @SerialName("quality") val quality: Map<String, Double?>? = null,
    @SerialName("latency_ms") val latencyMs: Double,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("provenance") val provenance: Provenance? = null,
    @SerialName("timestamp") val timestamp: String,
)
```

## ModuleStatus — Contracts.kt:259
```kotlin
enum class ModuleStatus {
    @SerialName("AVAILABLE") AVAILABLE,
    @SerialName("LOW_QUALITY") LOW_QUALITY,
    @SerialName("UNAVAILABLE") UNAVAILABLE,
    @SerialName("ERROR") ERROR,
}
```

## PolicyAction — Contracts.kt:267
```kotlin
enum class PolicyAction {
    @SerialName("ALLOW") ALLOW,
    @SerialName("WARN") WARN,
    @SerialName("SECONDARY_VERIFICATION") SECONDARY_VERIFICATION,
    @SerialName("ESCALATE") ESCALATE,
    @SerialName("HOLD") HOLD,
}
```

## PolicyConfig — Contracts.kt:276
```kotlin
data class PolicyConfig(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("policy_version") val policyVersion: String,
    @SerialName("warn_at") val warnAt: Double = 40.0,
    @SerialName("verify_at") val verifyAt: Double = 60.0,
    @SerialName("escalate_at") val escalateAt: Double = 80.0,
    @SerialName("hold_at") val holdAt: Double = 90.0,
    @SerialName("verification_workflow") val verificationWorkflow: String = "registered-number callback or MFA",
)
```

## PolicyEvent — Contracts.kt:287
```kotlin
data class PolicyEvent(
    @SerialName("type") val type: String = "policy",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String,
    @SerialName("policy_version") val policyVersion: String,
    @SerialName("action") val action: PolicyAction,
    @SerialName("triggering_threshold_or_rule") val triggeringThresholdOrRule: String,
    @SerialName("verification_workflow") val verificationWorkflow: String?,
    @SerialName("timestamp") val timestamp: String,
)
```

## Provenance — Contracts.kt:299
```kotlin
data class Provenance(
    @SerialName("model_version") val modelVersion: String? = null,
    @SerialName("artifact_version") val artifactVersion: String? = null,
    @SerialName("calibration_version") val calibrationVersion: String? = null,
    @SerialName("artifact_state") val artifactState: ArtifactState = ArtifactState.NOT_LOADED,
    @SerialName("checksum_sha256") val checksumSha256: String? = null,
)
```

## RetentionConfig — Contracts.kt:308
```kotlin
data class RetentionConfig(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("version") val version: String,
    @SerialName("retain_transcript") val retainTranscript: Boolean = false,
    @SerialName("retain_enrollment_audio") val retainEnrollmentAudio: Boolean = false,
    @SerialName("metadata_days") val metadataDays: Long = 30,
)
```

## RiskEvent — Contracts.kt:317
```kotlin
data class RiskEvent(
    @SerialName("type") val type: String = "risk",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String,
    @SerialName("risk_raw_0_100") val riskRaw0100: Double,
    @SerialName("risk_display_0_100") val riskDisplay0100: Double,
    @SerialName("evidence_summary") val evidenceSummary: List<EvidenceSummary>,
    @SerialName("quality") val quality: Map<String, Double?>,
    @SerialName("missingness") val missingness: Map<String, Boolean>,
    @SerialName("risk_model_version") val riskModelVersion: String,
    @SerialName("artifact_state") val artifactState: String = "VALIDATED",
    @SerialName("timestamp") val timestamp: String,
)
```

## RuleFlag — Contracts.kt:332
```kotlin
enum class RuleFlag {
    @SerialName("TRUE") TRUE,
    @SerialName("FALSE") FALSE,
    @SerialName("UNKNOWN") UNKNOWN,
}
```

## SessionStart — Contracts.kt:339
```kotlin
data class SessionStart(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("call_id") val callId: String,
    @SerialName("host_app_id") val hostAppId: String,
    @SerialName("claimed_identity") val claimedIdentity: String? = null,
    @SerialName("permitted_context") val permittedContext: ContextInput? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("supports_hold") val supportsHold: Boolean = false,
)
```

## SessionView — Contracts.kt:350
```kotlin
data class SessionView(
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("call_id") val callId: String,
    @SerialName("host_app_id") val hostAppId: String,
    @SerialName("claimed_identity") val claimedIdentity: String? = null,
    @SerialName("permitted_context") val permittedContext: ContextInput? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("supports_hold") val supportsHold: Boolean = false,
    @SerialName("session_id") val sessionId: String,
    @SerialName("ended_at") val endedAt: String? = null,
)
```

## SpeakerEvidence — Contracts.kt:363
```kotlin
data class SpeakerEvidence(
    @SerialName("type") val type: String = "evidence",
    @SerialName("call_id") val callId: String,
    @SerialName("window_id") val windowId: String? = null,
    @SerialName("module") val module: String,
    @SerialName("model_version") val modelVersion: String?,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("raw_score") val rawScore: Double? = null,
    @SerialName("features") val features: Map<String, Double?>? = null,
    @SerialName("calibrated_score") val calibratedScore: Double? = null,
    @SerialName("quality") val quality: Map<String, Double?>? = null,
    @SerialName("latency_ms") val latencyMs: Double,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("provenance") val provenance: Provenance? = null,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("speaker_state") val speakerState: SpeakerState = SpeakerState.UNAVAILABLE,
    @SerialName("cosine_similarity") val cosineSimilarity: Double? = null,
    @SerialName("profile_version") val profileVersion: String? = null,
    @SerialName("threshold_version") val thresholdVersion: String? = null,
    @SerialName("threshold_state") val thresholdState: ArtifactState = ArtifactState.NOT_LOADED,
)
```

## SpeakerState — Contracts.kt:386
```kotlin
enum class SpeakerState {
    @SerialName("MATCH") MATCH,
    @SerialName("UNCERTAIN") UNCERTAIN,
    @SerialName("MISMATCH") MISMATCH,
    @SerialName("UNAVAILABLE") UNAVAILABLE,
}
```

## SpeechSpan — Contracts.kt:394
```kotlin
data class SpeechSpan(
    @SerialName("start_ms") val startMs: Double,
    @SerialName("end_ms") val endMs: Double,
)
```

## TranscriptEvent — Contracts.kt:400
```kotlin
data class TranscriptEvent(
    @SerialName("type") val type: String = "transcript",
    @SerialName("call_id") val callId: String,
    @SerialName("text") val text: String,
    @SerialName("language") val language: String?,
    @SerialName("segments") val segments: List<TranscriptSegment>,
    @SerialName("quality") val quality: Double?,
    @SerialName("status") val status: ModuleStatus,
    @SerialName("model_version") val modelVersion: String?,
    @SerialName("latency_ms") val latencyMs: Double,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("analysis_english") val analysisEnglish: String? = null,
    @SerialName("reason_codes") val reasonCodes: List<String>? = null,
)
```

## TranscriptSegment — Contracts.kt:416
```kotlin
data class TranscriptSegment(
    @SerialName("start_ms") val startMs: Double,
    @SerialName("end_ms") val endMs: Double,
    @SerialName("text") val text: String,
)
```

## UnavailableEvent — Contracts.kt:423
```kotlin
data class UnavailableEvent(
    @SerialName("type") val type: String = "unavailable",
    @SerialName("call_id") val callId: String,
    @SerialName("module") val module: String,
    @SerialName("status") val status: String,
    @SerialName("artifact_state") val artifactState: ArtifactState,
    @SerialName("reason_codes") val reasonCodes: List<String>,
    @SerialName("timestamp") val timestamp: String,
)
```
