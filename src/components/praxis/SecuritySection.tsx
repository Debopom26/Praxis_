import { Lock, KeyRound, Users, Database, ShieldCheck, Filter, Timer, Network } from "lucide-react";
import { Section, SectionHeader, Note, Reveal } from "./primitives";

const CALL_FLOW = ["LIVE CALL AUDIO", "ROLLING TRANSIENT ANALYSIS", "DISCARDED BY DEFAULT"];
const ENROLL_FLOW = [
  "APPROVED ENROLLMENT AUDIO",
  "ECAPA EMBEDDING",
  "AES-256-GCM ENCRYPTED CENTROID",
  "RAW ENROLLMENT AUDIO DELETED BY DEFAULT",
];

const CAPS = [
  { icon: Network, t: "TLS / HTTPS / WSS", d: "Encrypted transport for REST and streaming sessions." },
  { icon: KeyRound, t: "JWT Authentication", d: "Signed, short-lived session tokens for host applications." },
  { icon: Users, t: "RBAC", d: "Role-scoped access to sessions, enrollment and policy." },
  { icon: ShieldCheck, t: "Tenant Isolation", d: "Data and profiles are scoped per organisation." },
  { icon: Database, t: "PostgreSQL Persistence", d: "Structured session records, not raw audio." },
  { icon: Lock, t: "Encrypted Speaker Profiles", d: "Centroids stored under AES-256-GCM." },
  { icon: Filter, t: "Input Validation", d: "Strict schema validation on all host-supplied context." },
  { icon: Timer, t: "Retention Controls", d: "Configurable retention windows per deployment." },
];

function Flow({ title, steps, accent }: { title: string; steps: string[]; accent?: boolean }) {
  return (
    <div className="panel p-5">
      <div className="label-xs">{title}</div>
      <div className="mt-3 grid gap-1.5">
        {steps.map((s, i) => (
          <div key={s}>
            <div
              className={`rounded-md border px-3 py-2.5 font-mono text-[11px] tracking-[0.08em] ${
                accent && i === steps.length - 1
                  ? "border-signal/40 bg-signal/[0.07] text-foreground"
                  : "border-border bg-surface/70 text-foreground/85"
              }`}
            >
              {s}
            </div>
            {i < steps.length - 1 ? <div className="mx-auto h-3 w-px bg-border-strong" /> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SecuritySection() {
  return (
    <Section id="security">
      <SectionHeader
        eyebrow="Security & privacy"
        title="Audio is evidence during the call, not an asset afterwards."
        sub="Live audio is analysed on rolling windows and discarded by default. Only approved enrollment produces a stored artifact, and that artifact is an encrypted embedding."
      />

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <Reveal>
          <Flow title="Live call path" steps={CALL_FLOW} />
        </Reveal>
        <Reveal delay={0.08}>
          <Flow title="Enrollment path" steps={ENROLL_FLOW} accent />
        </Reveal>
      </div>

      <div className="mt-4 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-4">
        {CAPS.map((c) => {
          const Icon = c.icon;
          return (
            <div key={c.t} className="bg-card p-4 transition-colors hover:bg-surface-2">
              <Icon className="h-4 w-4 text-muted-foreground" />
              <div className="mt-3 font-mono text-[11px] tracking-[0.08em]">{c.t}</div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{c.d}</p>
            </div>
          );
        })}
      </div>

      <Note>
        These are implemented controls in the current system. Production readiness, certification and
        third-party audit status are not claimed.
      </Note>
    </Section>
  );
}
