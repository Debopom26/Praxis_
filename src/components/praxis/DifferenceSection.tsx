import { useState } from "react";
import { motion } from "motion/react";
import { AudioLines, Activity, UserCheck, MessageSquareWarning, Building2 } from "lucide-react";
import { Reveal, Section, SectionHeader, Pill } from "./primitives";
import { cn } from "@/lib/utils";

const CHANNELS = [
  {
    id: "acoustic",
    icon: AudioLines,
    title: "ACOUSTIC",
    body: "Anti-spoofing models detect synthetic or manipulated speech evidence.",
  },
  {
    id: "prosody",
    icon: Activity,
    title: "PROSODY",
    body: "Examines pitch, energy, timing, pauses and speaking patterns.",
  },
  {
    id: "speaker",
    icon: UserCheck,
    title: "SPEAKER",
    body: "Checks consistency with an enrolled speaker when available.",
  },
  {
    id: "linguistic",
    icon: MessageSquareWarning,
    title: "LINGUISTIC",
    body: "Analyses transcript for social-engineering patterns and manipulation.",
  },
  {
    id: "context",
    icon: Building2,
    title: "CONTEXT",
    body: "Considers caller, workflow, beneficiary, urgency and organisational context.",
  },
];

export function DifferenceSection() {
  const [active, setActive] = useState<string | null>(null);

  return (
    <Section id="difference" tone="raised">
      <SectionHeader
        eyebrow="What makes Praxis different"
        title="A detector classifies audio. Praxis evaluates a conversation."
        sub="Synthetic speech does not automatically mean fraud. A known and authorised AI agent may legitimately use synthetic speech — the decision depends on the combined evidence."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Reveal>
          <div className="panel h-full p-5">
            <Pill>Conventional voice detector</Pill>
            <p className="mt-4 text-lg text-muted-foreground">“Is this audio synthetic?”</p>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              A single binary channel. No speaker history, no conversation content, no organisational
              context — and no way to express what it could not observe.
            </p>
          </div>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="panel h-full border-primary/30 bg-primary/[0.04] p-5">
            <Pill tone="accent">Praxis</Pill>
            <p className="mt-4 text-lg text-foreground">“Is this communication trustworthy?”</p>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              Five independent evidence channels are calibrated separately, then fused with explicit
              handling for quality and missingness before a policy decision is produced.
            </p>
          </div>
        </Reveal>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {CHANNELS.map((c, i) => {
            const Icon = c.icon;
            const on = active === c.id;
            return (
              <Reveal key={c.id} delay={i * 0.05}>
                <button
                  onMouseEnter={() => setActive(c.id)}
                  onMouseLeave={() => setActive(null)}
                  onClick={() => setActive(on ? null : c.id)}
                  className={cn(
                    "panel panel-hover h-full w-full p-4 text-left",
                    on && "border-primary/50 bg-primary/[0.06]",
                  )}
                >
                  <Icon className={cn("h-4 w-4", on ? "text-primary" : "text-muted-foreground")} />
                  <div className="mt-3 font-mono text-[11px] tracking-[0.12em]">{c.title}</div>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{c.body}</p>
                  <div className="mt-3 h-px w-full overflow-hidden bg-border">
                    <motion.div
                      className="h-px bg-primary"
                      initial={false}
                      animate={{ width: on ? "100%" : "0%" }}
                      transition={{ duration: 0.4 }}
                    />
                  </div>
                </button>
              </Reveal>
            );
          })}
        </div>
      </div>

      <div className="mt-3 grid place-items-center">
        <div
          className={cn(
            "panel w-full max-w-md p-4 text-center transition-colors",
            active && "border-signal/40 bg-signal/[0.06]",
          )}
        >
          <div className="font-mono text-[11px] tracking-[0.14em] text-signal">RISK ENGINE</div>
          <p className="mt-1.5 text-xs text-muted-foreground">
            {active
              ? `${CHANNELS.find((c) => c.id === active)?.title} evidence is routed into fusion.`
              : "Evidence channels feed the fusion layer, then the policy engine."}
          </p>
        </div>
      </div>
    </Section>
  );
}
