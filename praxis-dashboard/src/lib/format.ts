/**
 * Display formatting.
 *
 * Every helper returns an explicit placeholder rather than a number when a value is
 * absent. "0" next to a missing measurement is the single most misleading thing this
 * console could print (docs/design.md Sec.9.1).
 */

import type { ModuleStatus, PolicyAction, SessionState } from '../api/types';
import { STATUS_TEXT } from '../api/types';

/** The placeholder used everywhere a value does not exist. */
export const NO_VALUE = '\u2014';

export function formatScore(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NO_VALUE;
  return value.toFixed(digits);
}

export function formatRisk(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NO_VALUE;
  return Math.round(value).toString();
}

export function formatMs(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return NO_VALUE;
  return `${value.toFixed(0)} ms`;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return NO_VALUE;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return NO_VALUE;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return NO_VALUE;
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return iso;
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export function statusLabel(status: ModuleStatus): string {
  return STATUS_TEXT[status];
}

export function sessionStateLabel(state: SessionState): string {
  return state;
}

/** The risk ramp class for a policy action. Five actions, five distinct treatments. */
export function actionClass(action: PolicyAction): string {
  switch (action) {
    case 'ALLOW':
      return 'risk-low';
    case 'WARN':
      return 'risk-medium';
    case 'SECONDARY_VERIFICATION':
      return 'risk-high';
    case 'ESCALATE':
      return 'risk-critical';
    case 'HOLD':
      return 'action-hold';
  }
}

export function actionDotClass(action: PolicyAction): string {
  switch (action) {
    case 'ALLOW':
      return 'dot-low';
    case 'WARN':
      return 'dot-medium';
    case 'SECONDARY_VERIFICATION':
      return 'dot-high';
    case 'ESCALATE':
      return 'dot-critical';
    case 'HOLD':
      return 'dot-critical';
  }
}

/** The risk ramp class for a raw 0-100 index, used in history tables. */
export function riskClass(risk: number): string {
  if (risk >= 80) return 'risk-critical';
  if (risk >= 60) return 'risk-high';
  if (risk >= 40) return 'risk-medium';
  return 'risk-low';
}
