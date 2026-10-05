/**
 * Overall Risk + policy action (SRS Sec.16, docs/design.md Sec.5.3 and Sec.5.4).
 *
 * Two things this component must never do:
 *  - print a number where no risk model produced one (SRS Sec.2.2);
 *  - let the headline figure and the timeline be confused for each other. The headline
 *    is the EMA-smoothed value; the timeline is raw per-window risk. Both are labelled.
 */

import type { PolicyEvent, RiskEvent } from '../api/types';
import { ACTION_DESCRIPTION, bandForRisk } from '../api/types';
import { NO_VALUE, formatDateTime, formatRisk, riskClass } from '../lib/format';
import { IconHelpCircle } from './Icons';
import { ActionPill, KeyValue } from './ui';

/* ------------------------------------------------------------------ *
 * Timeline
 * ------------------------------------------------------------------ */

const W = 100;
const H = 56;


function sparklinePoints(history: readonly RiskEvent[]): string {
  if (history.length === 0) return '';
  if (history.length === 1) {
    const only = history[0];
    if (!only) return '';
    const y = H - 2 - (only.risk_raw_0_100 / 100) * (H - 4);
    return `${W / 2},${y.toFixed(2)}`;
  }
  return history
    .map((event, index) => {
      const x = (index / (history.length - 1)) * W;
      const y = H - 2 - (event.risk_raw_0_100 / 100) * (H - 4);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');
}

export function RiskTimeline({ history }: { history: readonly RiskEvent[] }) {
  const latest = history.length > 0 ? history[history.length - 1] : undefined;

  return (
    <div className="timeline">
      <div className="timeline-head">
        <span className="tiny muted">Risk over time</span>
        <span className="tiny dim">
          {history.length > 0
            ? `${history.length} window${history.length === 1 ? '' : 's'}`
            : 'no windows analysed'}
        </span>
      </div>

      {history.length === 0 ? (
        <div className="note note-info" style={{ marginTop: 4 }}>
          <IconHelpCircle />
          <div>
            The chart will appear once audio has been analyzed.
          </div>
        </div>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="Raw per-window risk index over time">
          <line x1="0" y1={H - 2 - 0.4 * (H - 4)} x2={W} y2={H - 2 - 0.4 * (H - 4)} stroke="#e4e9f0" strokeWidth="0.4" strokeDasharray="2 2" />
          <line x1="0" y1={H - 2 - 0.7 * (H - 4)} x2={W} y2={H - 2 - 0.7 * (H - 4)} stroke="#e4e9f0" strokeWidth="0.4" strokeDasharray="2 2" />
          <polyline
            points={sparklinePoints(history)}
            fill="none"
            stroke="#0b1420"
            strokeWidth="1.2"
            vectorEffect="non-scaling-stroke"
            strokeLinejoin="round"
          />
        </svg>
      )}

      <div className="timeline-legend">
        <span className="row gap-6">
          <span className="swatch" style={{ background: '#0b1420' }} />
          Raw per-window risk (plotted)
        </span>
        <span className="row gap-6">
          <span className="swatch" style={{ background: '#e4e9f0' }} />
          Band boundaries at 40 and 70
        </span>
        <span className="row gap-6">
          Latest raw: <strong className="tnum">{formatRisk(latest?.risk_raw_0_100 ?? null)}</strong>
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Headline
 * ------------------------------------------------------------------ */

export function RiskPanel({
  risk,
  policy,
  riskHistory,
}: {
  risk: RiskEvent | null;
  policy: PolicyEvent | null;
  riskHistory: readonly RiskEvent[];
}) {
  const display = risk?.risk_display_0_100 ?? null;
  const action = policy?.action ?? (display === null ? null : bandForRisk(display));

  return (
    <div className="card risk-panel fade-in">
      <div className={display === null ? 'risk-figure risk-empty' : 'risk-figure'}>
        <span className="label">Overall risk index</span>
        <div
          className="risk-value"
          aria-live={action === 'HOLD' ? 'assertive' : 'polite'}
          aria-atomic="true"
        >
          <span
            className="number tnum"
            style={display === null ? undefined : { color: riskColor(display) }}
          >
            {formatRisk(display)}
          </span>
          <span className="scale">/ 100</span>
        </div>
        <span className="risk-caption">
          {display === null
            ? 'Waiting for enough evidence to assess this conversation.'
            : 'An evidence-based indicator, not a probability of fraud.'}
        </span>
      </div>

      <div className="risk-actions">
        <div className="action-block">
          <span className="label">Recommended action</span>
          {action ? (
            <div>
              <ActionPill action={action} />
              <div className="risk-caption" style={{ marginTop: 8 }}>
                {ACTION_DESCRIPTION[action]}
              </div>
            </div>
          ) : (
            <div>
              <span className="pill action-pill action-none">
                <IconHelpCircle />
                Awaiting assessment
              </span>
              <div className="risk-caption" style={{ marginTop: 8 }}>
                A recommendation will appear when an assessment is available.
              </div>
            </div>
          )}
        </div>

        <div className="meta-grid">
          {risk && risk.model_status !== 'VALIDATED' ? <p className="small muted">Experimental assessment — review the evidence before acting.</p> : null}
          <KeyValue label="Updated" value={risk ? formatDateTime(risk.timestamp) : NO_VALUE} />
        </div>
      </div>

      {riskHistory.length > 0 ? <div style={{ flexBasis: '100%' }}>
        <RiskTimeline history={riskHistory} />
      </div> : null}
    </div>
  );
}

function riskColor(risk: number): string {
  const cls = riskClass(risk);
  switch (cls) {
    case 'risk-critical':
      return 'var(--risk-crit-text)';
    case 'risk-high':
      return 'var(--risk-high-text)';
    case 'risk-medium':
      return 'var(--risk-med-text)';
    default:
      return 'var(--risk-low-text)';
  }
}
