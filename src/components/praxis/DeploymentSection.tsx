import { Section, SectionHeader, Pill } from "./primitives";

const COLS = [
  {
    tag: "SIH Demo",
    tone: "accent" as const,
    steps: ["Website", "Android Demo App", "Hosted Praxis Server"],
    purpose: "Easy judge access — no infrastructure setup required.",
  },
  {
    tag: "Enterprise / Privacy Deployment",
    tone: "good" as const,
    steps: ["Organization Apps", "LAN / VPN", "Organization-hosted Praxis"],
    purpose: "Privacy and control — audio and profiles never leave the organisation.",
  },
];

export function DeploymentSection() {
  return (
    <Section id="deployment" tone="raised">
      <SectionHeader
        eyebrow="Deployment"
        title="Hosted for the demo. Self-hosted where privacy requires it."
        sub="The same analysis layer runs in both modes; only the trust boundary changes."
      />
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {COLS.map((c) => (
          <div key={c.tag} className="panel p-5">
            <Pill tone={c.tone}>{c.tag}</Pill>
            <div className="mt-4 grid gap-1.5">
              {c.steps.map((s, i) => (
                <div key={s}>
                  <div className="rounded-md border border-border bg-surface/70 px-3 py-2.5 font-mono text-[11px] tracking-[0.08em] text-foreground/85">
                    {s}
                  </div>
                  {i < c.steps.length - 1 ? <div className="mx-auto h-3 w-px bg-border-strong" /> : null}
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
              <span className="label-xs">Purpose </span>
              {c.purpose}
            </p>
          </div>
        ))}
      </div>
    </Section>
  );
}
