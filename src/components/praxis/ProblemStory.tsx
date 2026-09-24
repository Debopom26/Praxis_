import { Reveal, SectionHeader, Section } from "./primitives";

const STEPS = [
  { k: "01", t: "VOICE CLONING", d: "A few seconds of public audio is enough." },
  { k: "02", t: "FAMILIAR VOICE", d: "The receiver recognises someone they trust." },
  { k: "03", t: "URGENT REQUEST", d: "Time pressure removes the instinct to verify." },
  { k: "04", t: "TRUST", d: "Identity is assumed, never checked." },
  { k: "05", t: "FINANCIAL / CREDENTIAL LOSS", d: "The transfer or credential leaves before anyone verifies." },
];

export function ProblemStory() {
  return (
    <Section id="problem">
      <SectionHeader
        eyebrow="The problem"
        title="Voice alone can no longer be treated as proof of identity."
        sub="The attack does not start with technology — it ends with it. Cloning only has to be convincing for the few seconds before a decision is made."
      />
      <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 lg:grid-cols-5">
        {STEPS.map((s, i) => (
          <Reveal key={s.k} delay={i * 0.06}>
            <div className="group relative h-full bg-card p-4 transition-colors hover:bg-surface-2">
              <div className="font-mono text-[10px] tracking-[0.14em] text-primary">{s.k}</div>
              <div className="mt-3 font-mono text-[11px] tracking-[0.1em] text-foreground">{s.t}</div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{s.d}</p>
              <div className="mt-4 h-px w-0 bg-primary transition-all duration-500 group-hover:w-full" />
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
