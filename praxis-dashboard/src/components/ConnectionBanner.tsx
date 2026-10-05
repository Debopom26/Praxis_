/**
 * Transport-state chrome.
 *
 * Green here describes the *transport*, never call risk. It is never placed directly
 * beside a risk figure without a label separating the two (docs/design.md Sec.3.6).
 */

export type StreamStatus = 'connecting' | 'open' | 'reconnecting' | 'closed' | 'rejected';
import { IconAlertTriangle, IconPlug, IconXCircle } from './Icons';

const PILL: Record<StreamStatus, { cls: string; text: string }> = {
  connecting: { cls: 'conn-pill conn-idle', text: 'Connecting' },
  open: { cls: 'conn-pill conn-live', text: 'Stream live' },
  reconnecting: { cls: 'conn-pill conn-idle', text: 'Reconnecting' },
  closed: { cls: 'conn-pill conn-idle', text: 'Not connected' },
  rejected: { cls: 'conn-pill conn-bad', text: 'Stream refused' },
};

export function ConnectionPill({ status }: { status: StreamStatus }) {
  const config = PILL[status];
  return (
    <span className={config.cls}>
      <span className="dot" />
      {config.text}
    </span>
  );
}

export function ConnectionBanner({
  status,
  detail,
}: {
  status: StreamStatus;
  detail: string | null;
}) {
  if (status === 'reconnecting') {
    return (
      <div className="conn-banner banner-reconnecting" role="status" aria-live="polite">
        <IconPlug />
        <span>{detail ?? 'Connection lost. Retrying with backoff.'}</span>
      </div>
    );
  }

  if (status === 'rejected') {
    return (
      <div className="conn-banner banner-error" role="alert">
        <IconXCircle />
        <span>{detail ?? 'The backend refused this stream.'}</span>
      </div>
    );
  }

  if (status === 'closed' && detail) {
    return (
      <div className="conn-banner banner-restored" role="status">
        <IconAlertTriangle />
        <span>{detail}</span>
      </div>
    );
  }

  return null;
}
