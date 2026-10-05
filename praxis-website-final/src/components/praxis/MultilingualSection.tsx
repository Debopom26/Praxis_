import { Section, SectionHeader, Pill, Note, Reveal } from "./primitives";

const LANGS = [
  "Assamese",
  "Bengali",
  "Bodo",
  "Gujarati",
  "Hindi",
  "Kannada",
  "Malayalam",
  "Odia",
  "Punjabi",
  "Sanskrit",
  "Tamil",
  "Telugu",
  "Urdu",
];

const PIPELINE = [
  "SPEECH",
  "WHISPER SMALL MULTILINGUAL",
  "ORIGINAL-LANGUAGE TRANSCRIPT",
  "MULTILINGUAL RULE PACKS + MULTILINGUAL MINILM",
  "ANALYSIS",
];

export function MultilingualSection() {
  return (
    <Section id="multilingual" tone="raised">
      <SectionHeader
        eyebrow="Multilingual"
        title="Designed for multilingual India."
        sub="Transcription stays in the original language — translation would discard the exact phrasing that social-engineering detection depends on."
      />

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <div className="panel p-5">
          <div className="label-xs">Target languages</div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {LANGS.map((l, i) => (
              <Reveal key={l} delay={i * 0.02}>
                <span className="rounded-md border border-border bg-surface/70 px-2.5 py-1.5 text-[12px] text-foreground/85 transition-colors hover:border-primary/50 hover:text-foreground">
                  {l}
                </span>
              </Reveal>
            ))}
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <Pill tone="accent">Target language</Pill>
            <Pill tone="info">Implemented pipeline</Pill>
            <Pill tone="warn">Validation per language in progress</Pill>
          </div>
          <Note>
            All 13 languages are architectural targets. Language-level validation is reported
            separately and is not claimed for every language.
          </Note>
        </div>

        <div className="panel p-5">
          <div className="label-xs">Transcript pipeline</div>
          <div className="mt-3 grid gap-1.5">
            {PIPELINE.map((p, i) => (
              <div key={p}>
                <div className="rounded-md border border-border bg-surface/70 px-3 py-2.5 font-mono text-[11px] leading-relaxed tracking-[0.08em] text-foreground/85">
                  {p}
                </div>
                {i < PIPELINE.length - 1 ? (
                  <div className="mx-auto h-3 w-px bg-border-strong" />
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}
