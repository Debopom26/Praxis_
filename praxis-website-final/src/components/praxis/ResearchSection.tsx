import { ArrowRight } from "lucide-react";
import { Section, SectionHeader, Note, Reveal } from "./primitives";

const ROWS = [
  {
    insight: "Familiar voice created trust",
    failure: "Identity was never checked after recognition",
    response: "Speaker consistency + anti-spoof evidence",
  },
  {
    insight: "Urgency reduced verification",
    failure: "Time pressure replaced procedure",
    response: "Linguistic urgency / social-engineering detection",
  },
  {
    insight: "Loss occurred before verification",
    failure: "Review happened after the transfer",
    response: "Real-time intervention during the call",
  },
  {
    insight: "Risk depended on organizational workflow",
    failure: "Generic detection ignored the process",
    response: "Context Engine + Policy Engine",
  },
];

export function ResearchSection() {
  return (
    <Section id="research">
      <SectionHeader
        eyebrow="Research"
        title="Built from real scam experiences."
        sub="Design decisions trace back to anonymised interviews about how the loss actually happened — not to a benchmark leaderboard."
      />
      <div className="mt-6 overflow-hidden rounded-lg border border-border">
        <div className="hidden grid-cols-3 gap-4 border-b border-border bg-surface px-4 py-2.5 md:grid">
          <span className="label-xs">Interview insight</span>
          <span className="label-xs">Observed failure</span>
          <span className="label-xs">Praxis design response</span>
        </div>
        {ROWS.map((r, i) => (
          <Reveal key={r.insight} delay={i * 0.05}>
            <div className="grid gap-2 border-b border-border px-4 py-4 last:border-0 hover:bg-surface/60 md:grid-cols-3 md:items-center md:gap-4">
              <span className="text-sm">{r.insight}</span>
              <span className="flex items-center gap-2 text-xs text-muted-foreground">
                <ArrowRight className="h-3.5 w-3.5 shrink-0 text-border-strong md:hidden" />
                {r.failure}
              </span>
              <span className="flex items-center gap-2 font-mono text-[11px] text-primary">
                <ArrowRight className="h-3.5 w-3.5 shrink-0" />
                {r.response}
              </span>
            </div>
          </Reveal>
        ))}
      </div>
      <Note>All interview material is anonymised. No case details, names or institutions are published.</Note>
    </Section>
  );
}
