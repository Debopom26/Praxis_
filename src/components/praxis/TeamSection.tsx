import { Section, SectionHeader } from "./primitives";

const TEAM = [
  { name: "Debarpan Bera", role: "Lead · Systems", contrib: "Risk and policy engine architecture" },
  { name: "Team member", role: "ML · Anti-spoofing", contrib: "Acoustic models and calibration" },
  { name: "Team member", role: "ML · Speech & language", contrib: "ASR and multilingual analysis" },
  { name: "Team member", role: "Backend", contrib: "Streaming server, auth and tenancy" },
  { name: "Team member", role: "Android", contrib: "Caller app and SDK integration" },
  { name: "Team member", role: "Research", contrib: "Interviews and threat modelling" },
];

export function TeamSection() {
  return (
    <Section id="team" tone="raised">
      <SectionHeader eyebrow="Team" title="Who built Praxis." />
      <div className="mt-6 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-3">
        {TEAM.map((m) => (
          <div key={m.name + m.role} className="bg-card p-4 transition-colors hover:bg-surface-2">
            <div className="text-sm font-medium">{m.name}</div>
            <div className="label-xs mt-1.5">{m.role}</div>
            <p className="mt-2 text-xs text-muted-foreground">{m.contrib}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
