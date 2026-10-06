import { Section, SectionHeader, Pill, Note, Reveal } from "./primitives";

type Status = "IMPLEMENTED / VERIFIED";
const tone = (_s: Status) => "good" as const;
export const COMPONENTS: Array<{ name: string; status: Status; note: string }> = [
  { name: "AASIST", status: "IMPLEMENTED / VERIFIED", note: "Standalone anti-spoof module; implementation and verification reported by the project owner." },
  { name: "WavLM Anti-Spoof", status: "IMPLEMENTED / VERIFIED", note: "Representation-based spoof module; implementation and verification reported by the project owner." },
  { name: "Wav2Vec2 / XLS-R + AASIST", status: "IMPLEMENTED / VERIFIED", note: "Local acoustic artifact and baseline inference checks." },
  { name: "Whisper", status: "IMPLEMENTED / VERIFIED", note: "Transcript inference in the existing E2E pipeline." },
  { name: "Prosody", status: "IMPLEMENTED / VERIFIED", note: "Finite pitch, energy, timing and pause features." },
  { name: "Speaker Verification", status: "IMPLEMENTED / VERIFIED", note: "ECAPA-TDNN runtime; trusted enrollment required for comparison." },
  { name: "MiniLM + Rules", status: "IMPLEMENTED / VERIFIED", note: "Existing linguistic runtime and locked eight-label contract." },
  { name: "Qwen", status: "IMPLEMENTED / VERIFIED", note: "Existing local transcript analysis artifact." },
  { name: "Context V2", status: "IMPLEMENTED / VERIFIED", note: "Context persistence and evidence integration." },
  { name: "Fusion V2 / Risk / Policy", status: "IMPLEMENTED / VERIFIED", note: "E2E scoring and policy flow; risk regressor remains bootstrap/untrained." },
];
const LEGEND: Array<[Status, string]> = [["IMPLEMENTED / VERIFIED", "Implemented and checked in the existing runtime and integration workflow."]];

export function ValidationMatrix() {
  return (
    <Section id="validation">
      <SectionHeader
        eyebrow="Validation"
        title="Implemented. Verified in the Praxis pipeline."
      />

      <div className="panel mt-6 p-5">
        <p className="label-xs">Overall validation accuracy</p>
        <p className="mt-2 text-3xl font-semibold">82.49%</p>
      </div>

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

      <Note>Runtime verification and overall accuracy describe different checks. The reported overall result does not certify production performance or a trained risk regressor.</Note>
    </Section>
  );
}
