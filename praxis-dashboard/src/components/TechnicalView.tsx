/**
 * Technical / audit view (SRS Sec.16, docs/design.md Sec.5.3).
 *
 * Model versions, raw and native scores, calibration identifiers and latencies belong here
 * and nowhere else: always reachable, never in the way. Collapsed by default.
 */

import type { ModuleEvidence, PipelineStatusMessage, SessionSummary } from '../api/types';
import { ANTI_SPOOF_LABELS } from '../api/types';
import { NO_VALUE, formatDateTime, formatMs, formatScore } from '../lib/format';
import { IconChevronDown, IconFileText } from './Icons';
import { StatusPill } from './ui';

function readString(source: Record<string, unknown>, key: string): string | null {
  const value = source[key];
  return typeof value === 'string' && value.length > 0 ? value : null;
}

function readNumber(source: Record<string, unknown>, key: string): number | null {
  const value = source[key];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

interface TechRow {
  key: string;
  module: string;
  detector: string;
  status: ModuleEvidence['status'];
  modelVersion: string;
  calibration: string;
  native: string;
  raw: string;
  calibrated: string;
  latency: string;
  reasons: string;
}

function toRow(item: ModuleEvidence): TechRow {
  const loose = item as unknown as Record<string, unknown>;
  const detector =
    item.module === 'anti_spoof' ? ANTI_SPOOF_LABELS[item.detector] : NO_VALUE;

  const calibrated =
    readNumber(loose, 'calibrated_spoof_score') ??
    readNumber(loose, 'calibrated_prosody_score') ??
    readNumber(loose, 'fused_ai_written_score');

  return {
    key: item.module === 'anti_spoof' ? `anti_spoof:${item.detector}` : item.module,
    module: item.module,
    detector,
    status: item.status,
    modelVersion: item.model_version,
    calibration: readString(loose, 'calibration_version') ?? readString(loose, 'fusion_model_version') ?? NO_VALUE,
    native: formatScore(readNumber(loose, 'native_score')),
    raw: formatScore(readNumber(loose, 'raw_spoof_score')),
    calibrated: formatScore(calibrated),
    latency: formatMs(item.latency_ms),
    reasons: item.reason_codes.length > 0 ? item.reason_codes.join(', ') : NO_VALUE,
  };
}

export function TechnicalView({
  evidence,
  pipeline,
  session,
}: {
  evidence: readonly ModuleEvidence[];
  pipeline: PipelineStatusMessage | null;
  session: SessionSummary | null;
}) {
  const rows = evidence.map(toRow);

  return (
    <details className="card tech">
      <summary>
        <IconFileText />
        Processing details
        <span className="tiny dim" style={{ fontWeight: 600 }}>
          {rows.length} evidence {rows.length === 1 ? 'record' : 'records'}
        </span>
        <IconChevronDown className="chev" />
      </summary>

      <div className="tech-body">
        <div className="row between wrap gap-12" style={{ marginBottom: 14 }}>
          <div className="small muted">
            Raw, native and calibrated values exactly as received. Nothing here is rounded for
            display beyond three decimals.
          </div>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Module</th>
                <th>Detector</th>
                <th>Status</th>
                <th>Model version</th>
                <th>Calibration</th>
                <th>Native</th>
                <th>Raw</th>
                <th>Calibrated</th>
                <th>Latency</th>
                <th>Reason codes</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={10} className="muted">
                    No evidence records have been received for this session.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.key}>
                    <td className="mono">{row.module}</td>
                    <td>{row.detector}</td>
                    <td>
                      <StatusPill status={row.status} />
                    </td>
                    <td className="mono">{row.modelVersion}</td>
                    <td className="mono">{row.calibration}</td>
                    <td className="n">{row.native}</td>
                    <td className="n">{row.raw}</td>
                    <td className="n">{row.calibrated}</td>
                    <td className="n">{row.latency}</td>
                    <td className="mono">{row.reasons}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pipeline ? (
          <>
            <div className="card-title" style={{ margin: '22px 0 10px' }}>
              Pipeline stages reported by the backend
            </div>
            <div className="stage-list">
              {pipeline.stages.map((stage) => (
                <div className="stage-row" key={stage.stage}>
                  <span className="nm">{stage.stage}</span>
                  <span className="ref">{stage.detail}</span>
                  <StatusPill status={stage.status} />
                </div>
              ))}
            </div>
          </>
        ) : null}

        {session ? (
          <>
            <div className="card-title" style={{ margin: '22px 0 10px' }}>
              Session provenance
            </div>
            <table className="kv-table">
              <tbody>
                <tr>
                  <th>Session ID</th>
                  <td className="mono">{session.session_id}</td>
                </tr>
                <tr>
                  <th>Tenant</th>
                  <td className="mono">{session.tenant_id}</td>
                </tr>
                <tr>
                  <th>Call ID</th>
                  <td className="mono">{session.call_id}</td>
                </tr>
                <tr>
                  <th>Host app</th>
                  <td className="mono">{session.host_app_id}</td>
                </tr>
                <tr>
                  <th>State</th>
                  <td>{session.state}</td>
                </tr>
                <tr>
                  <th>Created</th>
                  <td>{formatDateTime(session.created_at)}</td>
                </tr>
                <tr>
                  <th>Windows received</th>
                  <td className="n">{session.windows_received}</td>
                </tr>
                <tr>
                  <th>Windows rejected</th>
                  <td className="n">{session.windows_rejected}</td>
                </tr>
                <tr>
                  <th>Duplicate windows</th>
                  <td className="n">{session.duplicate_windows}</td>
                </tr>
              </tbody>
            </table>
          </>
        ) : null}
      </div>
    </details>
  );
}
