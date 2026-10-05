/**
 * Shared primitives.
 *
 * The most important rule in this file: module status and risk/action are rendered by
 * different components with different treatments. They are never swapped, and status
 * never borrows the risk ramp (docs/design.md Sec.2.1, NFR-09).
 */

import type { ReactNode } from 'react';

import type { ModuleStatus, PolicyAction } from '../api/types';
import { ACTION_DESCRIPTION, ACTION_TEXT, STATUS_TEXT, bandForRisk } from '../api/types';
import { actionClass, actionDotClass, riskClass } from '../lib/format';
import {
  IconAlertTriangle,
  IconChevronDown,
  IconHelpCircle,
  IconLock,
  IconXCircle,
} from './Icons';

/* ------------------------------------------------------------------ *
 * Module status - structural/neutral, never the risk ramp
 * ------------------------------------------------------------------ */

const STATUS_CLASS: Record<ModuleStatus, string> = {
  AVAILABLE: 'status-badge status-available',
  LOW_QUALITY: 'status-badge status-low-quality',
  UNAVAILABLE: 'status-badge status-unavailable',
  ERROR: 'status-badge status-error',
};

export function StatusPill({ status }: { status: ModuleStatus }) {
  return (
    <span className={STATUS_CLASS[status]}>
      {status === 'LOW_QUALITY' ? <IconAlertTriangle className="inline-ic" /> : null}
      {status === 'ERROR' ? <IconXCircle className="inline-ic" /> : null}
      {status === 'UNAVAILABLE' ? <IconHelpCircle className="inline-ic" /> : null}
      {STATUS_TEXT[status]}
    </span>
  );
}

/** Short explanatory line for a status, used next to the pill. */
export function statusExplanation(status: ModuleStatus): string {
  switch (status) {
    case 'AVAILABLE':
      return 'Evidence exists and is within the validated operating range.';
    case 'LOW_QUALITY':
      return 'Signal is below the validated operating range; treat this evidence as weaker than usual.';
    case 'UNAVAILABLE':
      return 'No evidence exists for this module. Absence of evidence is not evidence of safety.';
    case 'ERROR':
      return 'The module failed for this window. The failure is isolated and no score was substituted.';
  }
}

/* ------------------------------------------------------------------ *
 * Risk and policy action
 * ------------------------------------------------------------------ */

export function ActionPill({ action }: { action: PolicyAction }) {
  return (
    <span
      className={`pill action-pill ${actionClass(action)}`}
      title={ACTION_DESCRIPTION[action]}
    >
      {action === 'HOLD' ? <IconLock /> : <span className={actionDotClass(action)} />}
      {ACTION_TEXT[action]}
    </span>
  );
}

/** A risk index rendered with its band's action. History tables and lists use this. */
export function RiskPill({ risk }: { risk: number }) {
  const action = bandForRisk(risk);
  if (!action) return <span className="pill status-unavailable">{'\u2014'}</span>;
  return (
    <span className={`pill risk-badge ${riskClass(risk)}`}>
      <span className={actionDotClass(action)} />
      {Math.round(risk)} {'\u00b7'} {ACTION_TEXT[action]}
    </span>
  );
}

/* ------------------------------------------------------------------ *
 * Layout helpers
 * ------------------------------------------------------------------ */

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={className ? `card ${className}` : 'card'}>{children}</div>;
}

export function Panel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <Card className="panel">
      <div className="panel-head">
        <div className="t">{title}</div>
        {action}
      </div>
      {children}
    </Card>
  );
}

export function EmptyState({
  icon,
  title,
  body,
  children,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="ic">{icon}</div>
      <div className="h">{title}</div>
      <p className="p">{body}</p>
      {children}
    </div>
  );
}

type NoteTone = 'info' | 'warn' | 'bad' | 'ok';

export function Note({
  tone = 'info',
  icon,
  children,
}: {
  tone?: NoteTone;
  icon?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className={`note note-${tone}`}>
      {icon}
      <div>{children}</div>
    </div>
  );
}

export function KeyValue({ label, value, mono }: { label: string; value: ReactNode; mono?: boolean }) {
  return (
    <div className="meta-item">
      <span className="k">{label}</span>
      <span className={mono ? 'v mono' : 'v'}>{value}</span>
    </div>
  );
}

/** Native disclosure, so the technical view is keyboard-operable without extra JS. */
export function Disclosure({
  summary,
  children,
  defaultOpen = false,
}: {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="card tech" open={defaultOpen}>
      <summary>
        {summary}
        <IconChevronDown className="chev" />
      </summary>
      <div className="tech-body">{children}</div>
    </details>
  );
}

export function Toast({ tone, message }: { tone: 'ok' | 'bad'; message: string }) {
  return (
    <div className={`toast toast-${tone}`} role="status">
      {message}
    </div>
  );
}
