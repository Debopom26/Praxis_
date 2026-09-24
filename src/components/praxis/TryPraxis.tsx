import { useEffect, useRef, useState } from "react";
import { Mic, Square, ShieldQuestion } from "lucide-react";
import { Section, SectionHeader, Pill, Note } from "./primitives";
import { cn } from "@/lib/utils";

type State = "idle" | "listening" | "stopped";

const DEMO_TRANSCRIPT = [
  "…",
  "Transcript preview is disabled in this browser demo.",
  "Connect a Praxis server to see original-language transcription.",
];

function Waveform({ active }: { active: boolean }) {
  const [bars, setBars] = useState<number[]>(() => Array.from({ length: 48 }, () => 0.1));
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (!active) {
      setBars(Array.from({ length: 48 }, () => 0.08));
      return;
    }
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;
    let t = 0;
    const tick = () => {
      t += 0.12;
      setBars((prev) =>
        prev.map((_, i) => {
          const v = Math.abs(Math.sin(t + i * 0.35)) * (0.35 + 0.65 * Math.abs(Math.sin(t * 0.4 + i)));
          return 0.1 + v * 0.9;
        }),
      );
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [active]);

  return (
    <div className="flex h-20 items-center gap-[3px]">
      {bars.map((b, i) => (
        <div
          key={i}
          className={cn(
            "w-full rounded-full transition-[height] duration-100",
            active ? "bg-primary/80" : "bg-border-strong",
          )}
          style={{ height: `${Math.max(4, b * 72)}px` }}
        />
      ))}
    </div>
  );
}

const EVIDENCE = [
  { k: "Acoustic", v: "AVAILABLE" },
  { k: "Prosody", v: "AVAILABLE" },
  { k: "Linguistic", v: "AVAILABLE" },
  { k: "Speaker", v: "UNAVAILABLE" },
  { k: "Context", v: "UNAVAILABLE" },
] as const;

export function TryPraxis() {
  const [state, setState] = useState<State>("idle");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (state !== "listening") return;
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  return (
    <Section id="try">
      <SectionHeader
        eyebrow="Try Praxis"
        title="Try Praxis"
        sub="Experience the analysis layer without creating an account."
      />

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <Pill tone="warn">Demo interface · no live inference</Pill>
        <Pill>Mock states clearly labelled</Pill>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1.25fr_1fr]">
        <div className="panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="label-xs">Session</span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {state === "listening" ? (
                <span className="flex items-center gap-1.5 text-primary">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary soft-pulse" /> RECORDING ·{" "}
                  {String(Math.floor(elapsed / 60)).padStart(2, "0")}:
                  {String(elapsed % 60).padStart(2, "0")}
                </span>
              ) : state === "stopped" ? (
                "SESSION ENDED"
              ) : (
                "READY"
              )}
            </span>
          </div>

          <div className="px-4 py-5">
            <Waveform active={state === "listening"} />

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <button
                onClick={() => {
                  if (state === "listening") setState("stopped");
                  else {
                    setElapsed(0);
                    setState("listening");
                  }
                }}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-4 py-2.5 font-mono text-[11px] tracking-[0.12em] uppercase transition-transform hover:-translate-y-px",
                  state === "listening"
                    ? "border border-border-strong bg-surface-2 text-foreground"
                    : "bg-primary text-primary-foreground",
                )}
              >
                {state === "listening" ? (
                  <>
                    <Square className="h-3.5 w-3.5" /> Stop analysis
                  </>
                ) : (
                  <>
                    <Mic className="h-3.5 w-3.5" /> Start analysis
                  </>
                )}
              </button>
              <span className="font-mono text-[11px] text-muted-foreground">
                Microphone capture is not started in this demo build.
              </span>
            </div>

            <dl className="mt-6 grid gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
              {[
                ["Language", state === "idle" ? "—" : "Bengali (demo)"],
                ["Audio quality", state === "idle" ? "—" : "Good (demo)"],
                ["Mode", "Browser demo"],
                ["Inference", "Not connected"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between bg-card px-3 py-2.5">
                  <dt className="label-xs">{k}</dt>
                  <dd className="font-mono text-[11px] text-foreground">{v}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-4 rounded-md border border-border bg-surface/70 p-3">
              <div className="label-xs">Transcript</div>
              <div className="mt-2 space-y-1 font-mono text-[11px] leading-relaxed text-muted-foreground">
                {DEMO_TRANSCRIPT.map((l) => (
                  <p key={l}>{l}</p>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="panel p-4">
          <div className="flex items-center justify-between">
            <span className="label-xs">Evidence · module availability</span>
            <ShieldQuestion className="h-4 w-4 text-muted-foreground" />
          </div>
          <ul className="mt-3 grid gap-px overflow-hidden rounded-md border border-border bg-border">
            {EVIDENCE.map((e) => (
              <li key={e.k} className="flex items-center justify-between bg-card px-3 py-3">
                <span className="text-sm">{e.k}</span>
                <Pill tone={e.v === "AVAILABLE" ? "good" : "neutral"}>{e.v}</Pill>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
            Speaker verification requires an enrolled profile and context requires host-supplied
            structured fields. Neither exists in an anonymous browser session, so both remain
            explicitly <span className="font-mono text-[11px]">UNAVAILABLE</span> rather than being
            guessed.
          </p>
          <Note>
            Browser demo processes audio transiently and does not retain microphone audio by
            default. No risk score, confidence value or model output is produced here.
          </Note>
        </div>
      </div>
    </Section>
  );
}
