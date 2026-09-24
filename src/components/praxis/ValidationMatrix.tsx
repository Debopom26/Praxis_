import { Section, SectionHeader, Pill, Note, Reveal } from "./primitives";

type Status = "IMPLEMENTED" | "VALIDATED" | "UNDER VALIDATION" | "PLANNED";

const tone = (s: Status) =>
  s === "VALIDATED" ? "good" : s === "IMPLEMENTED" ? "info" : s === "UNDER VALIDATION" ? "warn" : "neutral";

/** Update these rows as validation progresses. */
export const COMPONENTS: Array<{ name: string; status: Status; note: string }> = [
  { name: "RawNet2", status: "IMPLEMENTED", note: "Anti-spoofing baseline in the acoustic channel." },
  { name: "AASIST", status: "UNDER VALIDATION", note: "Calibration and fusion weighting in progress." },
  { name: "WavLM Anti-Spoof", status: "UNDER VALIDATION", note: "Representation-based spoof evidence." },
  { name: "Prosody", status: "IMPLEMENTED", note: "Pitch, energy, timing and pause features." },
  { name: "Speaker Verification", status: "IMPLEMENTED", note: "ECAPA-TDNN against enrolled centroid." },
  { name: "Linguistic Analysis", status: "IMPLEMENTED", note: "Rule packs plus multilingual MiniLM." },
  { name: "Risk Fusion", status: "UNDER VALIDATION", note: "Fusion across available, calibrated evidence." },
];

const LEGEND: Array<[Status, string]> = [
  ["IMPLEMENTED", "Built and running in the system."],
  ["VALIDATED", "Measured against a held-out protocol."],
  ["UNDER VALIDATION", "Measurement in progress; not yet reportable."],
  ["PLANNED", "Designed but not yet built."],
];

export function ValidationMatrix() {
  return (
    <Section id="validation">
      <SectionHeader
        eyebrow="Validation"
        title="Built with evidence. Honest about what is validated."
        sub="Implementation status and validation status are intentionally separated. No accuracy figures are published until a held-out protocol supports them."
      />

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {LEGEND.map(([s, d], i) => (
          <Reveal key={s} delay={i * 0.05}>
            <div className="panel h-full p-4">
              <Pill tone={tone(s)}>{s}</Pill>
              <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">{d}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <div className="mt-5 overflow-hidden rounded-lg border border-border">
        <div className="grid grid-cols-[1.1fr_auto] gap-3 border-b border-border bg-surface px-4 py-2.5 sm:grid-cols-[1fr_1.4fr_auto]">
          <span className="label-xs">Component</span>
          <span className="label-xs hidden sm:block">Role</span>
          <span className="label-xs text-right">Status</span>
        </div>
        {COMPONENTS.map((c) => (
          <div
            key={c.name}
            className="grid grid-cols-[1.1fr_auto] items-center gap-3 border-b border-border px-4 py-3 last:border-0 hover:bg-surface/60 sm:grid-cols-[1fr_1.4fr_auto]"
          >
            <span className="font-mono text-[12px]">{c.name}</span>
            <span className="hidden text-xs text-muted-foreground sm:block">{c.note}</span>
            <Pill tone={tone(c.status)}>{c.status}</Pill>
          </div>
        ))}
      </div>

      <Note>
        No benchmark numbers, accuracy percentages or confidence values appear on this website. They
        will be published only with the protocol, dataset splits and artifact versions used.
      </Note>
    </Section>
  );
}
