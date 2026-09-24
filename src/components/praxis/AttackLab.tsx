import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { Section, SectionHeader, Pill } from "./primitives";
import { cn } from "@/lib/utils";

const VOICES = ["Genuine Human", "Authorized AI Agent", "Synthetic / Cloned Voice"] as const;
const CONVOS = [
  "Normal",
  "OTP Request",
  "Urgent Transfer",
  "Authority Pressure",
  "Credential Request",
  "Verification Bypass",
] as const;
const CONTEXTS = [
  "Known Contact",
  "Unknown Contact",
  "Enrolled Speaker",
  "New Beneficiary",
  "Expected Workflow",
  "Unexpected Workflow",
  "Authorized AI",
] as const;

type Voice = (typeof VOICES)[number];
type Convo = (typeof CONVOS)[number];
type Ctx = (typeof CONTEXTS)[number];

type Outcome = "ALLOW" | "WARN" | "VERIFY" | "ESCALATE" | "HOLD";

function evaluate(voice: Voice, convo: Convo, ctx: Ctx) {
  const acoustic =
    voice === "Synthetic / Cloned Voice" ? "HIGH" : voice === "Authorized AI Agent" ? "HIGH" : "LOW";
  const speaker =
    ctx === "Enrolled Speaker"
      ? voice === "Genuine Human"
        ? "MATCH"
        : "MISMATCH"
      : ctx === "Known Contact"
        ? "UNCERTAIN"
        : "UNAVAILABLE";
  const linguistic =
    convo === "Normal"
      ? "NORMAL"
      : convo === "Urgent Transfer" || convo === "Authority Pressure"
        ? "URGENCY"
        : "CREDENTIAL REQUEST";
  const context =
    ctx === "Expected Workflow" || ctx === "Known Contact" || ctx === "Authorized AI"
      ? "EXPECTED"
      : "UNEXPECTED";

  let score = 0;
  if (acoustic === "HIGH" && voice === "Synthetic / Cloned Voice") score += 2;
  if (voice === "Authorized AI Agent" && ctx !== "Authorized AI") score += 1;
  if (speaker === "MISMATCH") score += 2;
  if (speaker === "UNAVAILABLE") score += 0.5;
  if (linguistic === "URGENCY") score += 1.5;
  if (linguistic === "CREDENTIAL REQUEST") score += 2;
  if (context === "UNEXPECTED") score += 1.5;
  if (ctx === "New Beneficiary") score += 1;

  const outcome: Outcome =
    score >= 6 ? "HOLD" : score >= 4.5 ? "ESCALATE" : score >= 3 ? "VERIFY" : score >= 1.5 ? "WARN" : "ALLOW";

  const rationale =
    voice === "Authorized AI Agent" && ctx === "Authorized AI"
      ? "Synthetic speech is expected here: the agent is authorised in this workflow, so acoustic evidence alone does not raise the decision."
      : speaker === "UNAVAILABLE"
        ? "Speaker evidence is unavailable, so the decision leans on linguistic and contextual evidence rather than assuming a match."
        : "Independent channels agree closely enough for a single operational decision.";

  return { acoustic, speaker, linguistic, context, outcome, rationale };
}

const outcomeTone: Record<Outcome, "good" | "warn" | "accent" | "bad"> = {
  ALLOW: "good",
  WARN: "warn",
  VERIFY: "accent",
  ESCALATE: "bad",
  HOLD: "bad",
};

function Choice<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div>
      <div className="label-xs">{label}</div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {options.map((o) => (
          <button
            key={o}
            onClick={() => onChange(o)}
            className={cn(
              "rounded-md border px-2.5 py-1.5 text-[12px] transition-colors",
              value === o
                ? "border-primary/60 bg-primary/10 text-foreground"
                : "border-border text-muted-foreground hover:border-border-strong hover:text-foreground",
            )}
          >
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}

export function AttackLab() {
  const [voice, setVoice] = useState<Voice>("Synthetic / Cloned Voice");
  const [convo, setConvo] = useState<Convo>("Urgent Transfer");
  const [ctx, setCtx] = useState<Ctx>("New Beneficiary");

  const r = useMemo(() => evaluate(voice, convo, ctx), [voice, convo, ctx]);

  const rows: Array<[string, string, "good" | "warn" | "bad" | "neutral" | "info"]> = [
    ["Acoustic", r.acoustic, r.acoustic === "HIGH" ? "warn" : "good"],
    [
      "Speaker",
      r.speaker,
      r.speaker === "MATCH" ? "good" : r.speaker === "MISMATCH" ? "bad" : r.speaker === "UNCERTAIN" ? "warn" : "neutral",
    ],
    ["Linguistic", r.linguistic, r.linguistic === "NORMAL" ? "good" : "warn"],
    ["Context", r.context, r.context === "EXPECTED" ? "good" : "warn"],
  ];

  return (
    <Section id="attack-lab" tone="raised">
      <SectionHeader
        eyebrow="Attack lab"
        title="See how the evidence changes the decision."
        sub="Change the voice, the conversation and the organisational context. The evidence panel and the policy outcome update together."
      />
      <div className="mt-5">
        <Pill tone="warn">Scenario simulation · not real inference</Pill>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div className="panel grid gap-5 p-5">
          <Choice label="Voice" options={VOICES} value={voice} onChange={setVoice} />
          <Choice label="Conversation" options={CONVOS} value={convo} onChange={setConvo} />
          <Choice label="Caller / context" options={CONTEXTS} value={ctx} onChange={setCtx} />
        </div>

        <div className="panel p-5">
          <div className="label-xs">Evidence panel</div>
          <ul className="mt-3 grid gap-px overflow-hidden rounded-md border border-border bg-border">
            {rows.map(([k, v, tone]) => (
              <li key={k} className="flex items-center justify-between bg-card px-3 py-3">
                <span className="text-sm">{k}</span>
                <motion.span key={v} initial={{ opacity: 0.3 }} animate={{ opacity: 1 }}>
                  <Pill tone={tone}>{v}</Pill>
                </motion.span>
              </li>
            ))}
          </ul>

          <div className="mt-4 grid gap-1.5 text-center">
            <div className="rounded-md border border-border bg-surface/70 py-2 font-mono text-[11px] tracking-[0.14em] text-muted-foreground">
              RISK ENGINE
            </div>
            <div className="mx-auto h-4 w-px bg-border-strong" />
            <div className="rounded-md border border-border bg-surface/70 py-2 font-mono text-[11px] tracking-[0.14em] text-muted-foreground">
              POLICY ENGINE
            </div>
            <div className="mx-auto h-4 w-px bg-border-strong" />
            <motion.div
              key={r.outcome}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              <Pill tone={outcomeTone[r.outcome]} className="px-4 py-2 text-xs">
                {r.outcome}
              </Pill>
            </motion.div>
          </div>

          <p className="mt-4 text-xs leading-relaxed text-muted-foreground">{r.rationale}</p>
        </div>
      </div>
    </Section>
  );
}
