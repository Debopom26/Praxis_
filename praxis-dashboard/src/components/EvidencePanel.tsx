/**
 * Grouped evidence view (SRS Sec.16, docs/design.md Sec.5.3).
 *
 * Requirements this file exists to satisfy:
 *  - evidence is grouped into Acoustic / Prosody / Speaker / Linguistic / Context, and is
 *    never collapsed into one aggregate "fake score";
 *  - a module that has produced nothing renders as UNAVAILABLE with a reason, never as a
 *    zero;
 *  - speaker never asserts an identity that was not verified;
 *  - social-engineering reasons and AI-written evidence are separate blocks inside the
 *    Linguistic group and never merge into one number;
 *  - context lists UNKNOWN fields as content, because "we were not told" is itself
 *    evidence about the situation.
 */

import type { ReactNode } from 'react';

import type {
  AIWrittenEvidence,
  ASREvidence,
  AcousticFusionEvidence,
  AntiSpoofEvidence,
  AntiSpoofModel,
  ContextEvidence,
  ContextField,
  LinguisticEvidence,
  ModuleEvidence,
  ModuleStatus,
  ProsodyEvidence,
  SessionContext,
  SpeakerEvidence,
  SpeakerVerificationResult,
} from '../api/types';
import {
  ANTI_SPOOF_LABELS,
  ANTI_SPOOF_MODELS,
  CONTEXT_FIELDS,
  CONTEXT_FIELD_TEXT,
  CONTEXT_RULES,
  CONTEXT_RULE_TEXT,
  SOCIAL_ENGINEERING_TEXT,
} from '../api/types';
import { NO_VALUE, formatDateTime, formatMs, formatScore } from '../lib/format';
import {
  IconAlertTriangle,
  IconChevronDown,
  IconHelpCircle,
  IconLayers,
  IconMessage,
  IconMic,
  IconSparkle,
  IconTrending,
  IconUserCheck,
} from './Icons';
import { Note, StatusPill, statusExplanation } from './ui';

/* ------------------------------------------------------------------ *
 * Lookups
 * ------------------------------------------------------------------ */

function findModule<T extends ModuleEvidence['module']>(
  list: readonly ModuleEvidence[],
  module: T,
): Extract<ModuleEvidence, { module: T }> | null {
  const found = list.find((item) => item.module === module);
  return found ? (found as Extract<ModuleEvidence, { module: T }>) : null;
}

function findAntiSpoof(
  list: readonly ModuleEvidence[],
  detector: AntiSpoofModel,
): AntiSpoofEvidence | null {
  const found = list.find(
    (item): item is AntiSpoofEvidence => item.module === 'anti_spoof' && item.detector === detector,
  );
  return found ?? null;
}

function worstStatus(statuses: readonly ModuleStatus[]): ModuleStatus {
  if (statuses.includes('ERROR')) return 'ERROR';
  if (statuses.includes('LOW_QUALITY')) return 'LOW_QUALITY';
  if (statuses.includes('AVAILABLE')) return 'AVAILABLE';
  return 'UNAVAILABLE';
}

/* ------------------------------------------------------------------ *
 * Family shell
 * ------------------------------------------------------------------ */

function FamilyCard({
  icon,
  title,
  subtitle,
  status,
  children,
}: {
  icon: ReactNode;
  title: string;
  subtitle: string;
  status: ModuleStatus;
  children: ReactNode;
}) {
  return (
    <details className="card family">
      <summary className="family-head">
        <span className="icon">{icon}</span>
        <span className="titles">
          <span className="t1">{title}</span>
          <span className="t2">{subtitle}</span>
        </span>
        <StatusPill status={status} />
        <span className="chev">
          <IconChevronDown />
        </span>
      </summary>
      <div className="family-body">{children}</div>
    </details>
  );
}

function AbsentRecord({ module }: { module: string }) {
  return (
    <Note
      tone="info"
      icon={<IconHelpCircle />}
    >
      {`No ${module} results are available for this conversation yet.`}
    </Note>
  );
}

function DetectorRow({
  name,
  score,
  status,
  latency,
}: {
  name: string;
  score: string;
  status: ModuleStatus | null;
  latency: string;
}) {
  return (
    <div className="detector-row">
      <span className="name">{name}</span>
      <span className={score === NO_VALUE ? 'value empty tnum' : 'value tnum'}>{score}</span>
      <span className="grow" />
      {status ? <StatusPill status={status} /> : <span className="status-badge status-unavailable">NO RECORD</span>}
      <span className="tiny dim tnum" style={{ minWidth: 62, textAlign: 'right' }}>{latency}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Acoustic
 * ------------------------------------------------------------------ */

function AcousticFamily({ evidence }: { evidence: readonly ModuleEvidence[] }) {
  const fusion: AcousticFusionEvidence | null = findModule(evidence, 'acoustic_fusion');
  const detectors = ANTI_SPOOF_MODELS.map((model) => findAntiSpoof(evidence, model));
  const present = detectors.filter((item) => item !== null).length;

  const statuses: ModuleStatus[] = detectors.flatMap((item) => (item ? [item.status] : []));
  if (fusion) statuses.push(fusion.status);
  const headline = worstStatus(statuses);

  return (
    <FamilyCard
      icon={<IconMic />}
      title="Voice authenticity"
      subtitle={`${present} of ${ANTI_SPOOF_MODELS.length} voice checks have results`}
      status={statuses.length === 0 ? 'UNAVAILABLE' : headline}
    >
      {statuses.length === 0 ? <AbsentRecord module="acoustic" /> : null}

      <div className="detector-row">
        <span className="name">Calibrated fusion</span>
        <span className={fusion?.calibrated_spoof_score == null ? 'value empty tnum' : 'value tnum'}>
          {formatScore(fusion?.calibrated_spoof_score ?? null)}
        </span>
        <span className="grow" />
        {fusion ? <StatusPill status={fusion.status} /> : <span className="status-badge status-unavailable">NO RECORD</span>}
        <span className="tiny dim tnum" style={{ minWidth: 62, textAlign: 'right' }}>
          {formatMs(fusion?.latency_ms ?? null)}
        </span>
      </div>

      {ANTI_SPOOF_MODELS.map((model) => {
        const record = findAntiSpoof(evidence, model);
        return (
          <DetectorRow
            key={model}
            name={ANTI_SPOOF_LABELS[model]}
            score={formatScore(record?.calibrated_spoof_score ?? null)}
            status={record?.status ?? null}
            latency={formatMs(record?.latency_ms ?? null)}
          />
        );
      })}

      {fusion && fusion.detectors_missing.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <Note tone="info" icon={<IconHelpCircle />}>
            {`Not present in this window: ${fusion.detectors_missing
              .map((model) => ANTI_SPOOF_LABELS[model])
              .join(', ')}. Missing detectors contribute missingness to the fusion, never a neutral score.`}
          </Note>
        </div>
      ) : null}

      <div className="small muted" style={{ marginTop: 12 }}>
        Calibrated values are shown here; raw and native model scores live in the technical
        view. Higher means more spoof-like.
      </div>
    </FamilyCard>
  );
}

/* ------------------------------------------------------------------ *
 * Prosody
 * ------------------------------------------------------------------ */

function ProsodyFamily({ evidence }: { evidence: readonly ModuleEvidence[] }) {
  const record: ProsodyEvidence | null = findModule(evidence, 'prosody');
  const features = record?.features ?? null;
  const featureCount = features ? Object.keys(features).length : 0;

  return (
    <FamilyCard
      icon={<IconTrending />}
      title="Speaking patterns"
      subtitle="Pitch, energy, rhythm and pause behaviour"
      status={record?.status ?? 'UNAVAILABLE'}
    >
      {record === null ? <AbsentRecord module="prosody" /> : null}

      <div className="detector-row">
        <span className="name">Calibrated prosody score</span>
        <span className={record?.calibrated_prosody_score == null ? 'value empty tnum' : 'value tnum'}>
          {formatScore(record?.calibrated_prosody_score ?? null)}
        </span>
        <span className="grow" />
        <span className="tiny dim tnum">{formatMs(record?.latency_ms ?? null)}</span>
      </div>

      <div className="detector-row">
        <span className="name">Extracted features</span>
        <span className={featureCount === 0 ? 'value empty tnum' : 'value tnum'}>
          {record ? String(featureCount) : NO_VALUE}
        </span>
        <span className="grow" />
        <span className="tiny dim">
          {record && record.features_omitted.length > 0
            ? `${record.features_omitted.length} omitted (signal quality)`
            : ''}
        </span>
      </div>

      <div className="small muted" style={{ marginTop: 12 }}>
        Prosodic anomaly and spoof-support evidence. This is not a probability of fraud and
        is not labelled as one.
      </div>
    </FamilyCard>
  );
}

/* ------------------------------------------------------------------ *
 * Speaker
 * ------------------------------------------------------------------ */

const VERDICT_CLASS: Record<SpeakerVerificationResult, string> = {
  MATCH: 'verdict verdict-match',
  UNCERTAIN: 'verdict verdict-uncertain',
  MISMATCH: 'verdict verdict-mismatch',
  UNAVAILABLE: 'verdict verdict-unavailable',
};

function SpeakerFamily({ evidence }: { evidence: readonly ModuleEvidence[] }) {
  const record: SpeakerEvidence | null = findModule(evidence, 'speaker');
  const result: SpeakerVerificationResult = record?.result ?? 'UNAVAILABLE';

  return (
    <FamilyCard
      icon={<IconUserCheck />}
      title="Speaker comparison"
      subtitle="Compares the voice with an approved profile"
      status={record?.status ?? 'UNAVAILABLE'}
    >
      <div className="speaker-verdict">
        <span className={VERDICT_CLASS[result]}>
          {result === 'UNAVAILABLE' ? <IconHelpCircle /> : null}
          {result}
        </span>
        {result !== 'UNAVAILABLE' && record?.claimed_identity ? (
          <span className="small muted">
            Against enrolled profile: <strong>{record.claimed_identity}</strong>
          </span>
        ) : null}
      </div>

      <div style={{ marginTop: 14 }}>
        <div className="detector-row">
          <span className="name">Cosine similarity</span>
          <span className={record?.cosine_similarity == null ? 'value empty tnum' : 'value tnum'}>
            {result === 'UNAVAILABLE' ? NO_VALUE : formatScore(record?.cosine_similarity ?? null)}
          </span>
          <span className="grow" />
          <span className="tiny dim tnum">{formatMs(record?.latency_ms ?? null)}</span>
        </div>
        <div className="detector-row">
          <span className="name">Embedding model</span>
          <span className="value mono">{record?.embedding_model_version ?? NO_VALUE}</span>
          <span className="grow" />
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        {result === 'UNAVAILABLE' ? (
          <Note tone="info" icon={<IconHelpCircle />}>
            No approved enrollment profile exists for this identity, so no comparison was made.
            No similarity is reported and no risk is added for the absence.
          </Note>
        ) : (
          <Note tone="info" icon={<IconHelpCircle />}>
            {`Status: ${record ? statusExplanation(record.status) : 'No speaker evidence record has been emitted.'}`}
          </Note>
        )}
      </div>
    </FamilyCard>
  );
}

/* ------------------------------------------------------------------ *
 * Linguistic (social engineering + AI-written, kept separate)
 * ------------------------------------------------------------------ */

function SocialEngineeringBlock({
  linguistic,
  asr,
}: {
  linguistic: LinguisticEvidence | null;
  asr: ASREvidence | null;
}) {
  const labels = linguistic?.activated_labels ?? [];
  const segments = asr?.segments ?? null;

  return (
    <div>
      <div className="sub-block-head">
        <span className="h">Social-engineering reasons</span>
        <span className="badge">deterministic rules + MiniLM</span>
      </div>
      <p className="desc">
        Multi-label indicators activated in the transcript. A transcript may activate several
        at once; they are never summed into a single number here.
      </p>

      <div className="label-chips" style={{ marginTop: 10 }}>
        {labels.length === 0 ? (
          <span className="label-chip none">No indicators activated</span>
        ) : (
          labels.map((label) => (
            <span key={label} className="label-chip">
              {SOCIAL_ENGINEERING_TEXT[label]}
            </span>
          ))
        )}
      </div>

      <div style={{ marginTop: 14 }}>
        <div className="detector-row">
          <span className="name">Aggregate linguistic score</span>
          <span className={linguistic?.aggregate_linguistic_score == null ? 'value empty tnum' : 'value tnum'}>
            {formatScore(linguistic?.aggregate_linguistic_score ?? null)}
          </span>
          <span className="grow" />
        </div>
        <div className="detector-row">
          <span className="name">Transcript language</span>
          <span className="value">{asr?.language ?? linguistic?.transcript_language ?? NO_VALUE}</span>
          <span className="grow" />
          <span className="tiny dim">
            {linguistic?.analysed_in_english === true ? 'analysed in English' : ''}
          </span>
        </div>
        <div className="detector-row">
          <span className="name">Transcript segments</span>
          <span className={segments === null ? 'value empty tnum' : 'value tnum'}>
            {segments === null ? NO_VALUE : String(segments.length)}
          </span>
          <span className="grow" />
        </div>
      </div>

      {segments && segments.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          {segments.map((segment) => (
            <div key={`${segment.start_ms}-${segment.end_ms}`} className="event-row">
              <span className="when tnum">
                {(segment.start_ms / 1000).toFixed(1)}s {'\u2013'} {(segment.end_ms / 1000).toFixed(1)}s
              </span>
              <span className="what" style={{ fontWeight: 400 }}>
                {segment.text}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {linguistic && linguistic.rule_reason_codes.length > 0 ? (
        <div className="small muted" style={{ marginTop: 10 }}>
          Rule codes: <span className="mono">{linguistic.rule_reason_codes.join(', ')}</span>
        </div>
      ) : null}
    </div>
  );
}

function AIWrittenBlock({ record }: { record: AIWrittenEvidence | null }) {
  return (
    <div className="sub-block">
      <div className="sub-block-head">
        <IconSparkle className="inline-ic" />
        <span className="h">AI-written wording evidence</span>
        <span className="badge">experimental {'\u00b7'} supporting only</span>
      </div>
      <p className="desc">
        Language-model statistics over the transcript. This does not determine whether the audio
        is synthetic, and it cannot by itself raise the action to HOLD.
      </p>

      <div style={{ marginTop: 12 }}>
        <div className="detector-row">
          <span className="name">Fused AI-written score</span>
          <span className={record?.fused_ai_written_score == null ? 'value empty tnum' : 'value tnum'}>
            {formatScore(record?.fused_ai_written_score ?? null)}
          </span>
          <span className="grow" />
        </div>
        <div className="detector-row">
          <span className="name">Normalized tokens</span>
          <span className="value tnum">
            {record ? String(record.normalized_token_count) : NO_VALUE}
          </span>
          <span className="grow" />
          <span className="tiny dim">minimum 64 required to score</span>
        </div>
        <div className="detector-row">
          <span className="name">Can trigger HOLD alone</span>
          <span className="value">{record ? (record.may_trigger_hold_alone ? 'YES' : 'NO') : NO_VALUE}</span>
          <span className="grow" />
          <span className="tiny dim">locked to NO in V1</span>
        </div>
      </div>
    </div>
  );
}

function LinguisticFamily({ evidence }: { evidence: readonly ModuleEvidence[] }) {
  const linguistic: LinguisticEvidence | null = findModule(evidence, 'linguistic');
  const asr: ASREvidence | null = findModule(evidence, 'asr');
  const aiWritten: AIWrittenEvidence | null = findModule(evidence, 'ai_written');

  const statuses: ModuleStatus[] = [];
  if (linguistic) statuses.push(linguistic.status);
  if (asr) statuses.push(asr.status);

  return (
    <FamilyCard
      icon={<IconMessage />}
      title="Conversation checks"
      subtitle="Pressure, suspicious requests, and generated wording"
      status={statuses.length === 0 ? 'UNAVAILABLE' : worstStatus(statuses)}
    >
      {linguistic === null && asr === null ? <AbsentRecord module="linguistic" /> : null}
      <SocialEngineeringBlock linguistic={linguistic} asr={asr} />
      <AIWrittenBlock record={aiWritten} />
    </FamilyCard>
  );
}

/* ------------------------------------------------------------------ *
 * Context
 * ------------------------------------------------------------------ */

function contextValue(context: SessionContext, field: ContextField): string | null {
  const value = context[field];
  if (value === undefined || value === null || value === '') return null;
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (field === 'time') return formatDateTime(String(value));
  return String(value);
}

function ContextFamily({
  evidence,
  context,
}: {
  evidence: readonly ModuleEvidence[];
  context: SessionContext;
}) {
  const record: ContextEvidence | null = findModule(evidence, 'context');
  const suppliedFromRecord = record ? new Set(record.available_fields) : null;
  const activated = new Set(record?.activated_rules ?? []);

  // The record's own available_fields is the authority once it exists: a field the backend
  // was told about is supplied even when this console cannot render its value.
  const supplied = CONTEXT_FIELDS.filter((field) => {
    if (suppliedFromRecord) return suppliedFromRecord.has(field);
    return contextValue(context, field) !== null;
  });
  const unknownCount = CONTEXT_FIELDS.length - supplied.length;

  return (
    <FamilyCard
      icon={<IconLayers />}
      title="Conversation context"
      subtitle={`${supplied.length} details supplied; ${unknownCount} not provided`}
      status={record?.status ?? 'UNAVAILABLE'}
    >
      {record === null ? (
        <Note tone="info" icon={<IconHelpCircle />}>
          Context results appear after audio is analyzed. Details shown here were supplied
          in this browser; updates from your connected application may not be shown yet.
        </Note>
      ) : null}

      <div className="context-grid" style={{ marginTop: record === null ? 12 : 0 }}>
        {CONTEXT_FIELDS.map((field) => {
          const value = contextValue(context, field);
          const isSupplied = suppliedFromRecord
            ? suppliedFromRecord.has(field)
            : value !== null;
          const known = isSupplied && value !== null;
          return (
            <div key={field} className={known ? 'context-field' : 'context-field unknown'}>
              <div className="k">{CONTEXT_FIELD_TEXT[field]}</div>
              <div className="v">
                {known ? value : isSupplied ? 'not shown here' : 'UNKNOWN'}
              </div>
            </div>
          );
        })}
      </div>

      <div className="sub-block">
        <div className="sub-block-head">
          <span className="h">Context rules</span>
        </div>
        <div className="rule-list" style={{ marginTop: 8 }}>
          {CONTEXT_RULES.map((rule) => {
            const on = activated.has(rule);
            return (
              <div key={rule} className="rule-item">
                {on ? (
                  <IconAlertTriangle className="rule-on" />
                ) : (
                  <IconChevronDown className="rule-off" style={{ opacity: 0.35 }} />
                )}
                <span className={on ? 'rule-on' : 'rule-off'}>{CONTEXT_RULE_TEXT[rule]}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="detector-row" style={{ marginTop: 14 }}>
        <span className="name">Context score</span>
        <span className={record?.context_score == null ? 'value empty tnum' : 'value tnum'}>
          {formatScore(record?.context_score ?? null, 1)}
        </span>
        <span className="grow" />
        <span className="tiny dim tnum">{formatMs(record?.latency_ms ?? null)}</span>
      </div>

      {record && record.reason_codes.length > 0 ? (
        <div className="small muted" style={{ marginTop: 10 }}>
          Reasons: <span className="mono">{record.reason_codes.join(', ')}</span>
        </div>
      ) : null}
    </FamilyCard>
  );
}

/* ------------------------------------------------------------------ *
 * Panel
 * ------------------------------------------------------------------ */

export function EvidencePanel({
  evidence,
  context,
}: {
  evidence: readonly ModuleEvidence[];
  context: SessionContext;
}) {
  return (
    <div className="evidence-list stagger">
      <AcousticFamily evidence={evidence} />
      <ProsodyFamily evidence={evidence} />
      <SpeakerFamily evidence={evidence} />
      <LinguisticFamily evidence={evidence} />
      <ContextFamily evidence={evidence} context={context} />
    </div>
  );
}
