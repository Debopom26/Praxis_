import { useEffect, useRef, useState } from "react";
import { Mic, Square, ShieldQuestion, Loader2 } from "lucide-react";
import { Section, SectionHeader, Pill } from "./primitives";
import { cn } from "@/lib/utils";

type State = "idle" | "listening" | "analyzing" | "done" | "error";

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  as: "Assamese",
  bn: "Bengali",
  brx: "Bodo",
  gu: "Gujarati",
  hi: "Hindi",
  kn: "Kannada",
  ml: "Malayalam",
  or: "Odia",
  odia: "Odia",
  pa: "Punjabi",
  sa: "Sanskrit",
  ta: "Tamil",
  te: "Telugu",
  ur: "Urdu",
};

function languageLabel(codeOrName: string): string {
  const key = codeOrName.trim().toLowerCase();
  const short = key.split("-")[0] ?? key;
  return LANGUAGE_NAMES[short] ?? codeOrName;
}

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
  { k: "Language detection", v: "LIVE" },
  { k: "Acoustic", v: "UNAVAILABLE" },
  { k: "Prosody", v: "UNAVAILABLE" },
  { k: "Linguistic", v: "UNAVAILABLE" },
  { k: "Speaker", v: "UNAVAILABLE" },
  { k: "Context", v: "UNAVAILABLE" },
] as const;

type DetectionResult = { language: string | null; transcript: string | null };

export function TryPraxis() {
  const [state, setState] = useState<State>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (state !== "listening") return;
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [state]);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function startRecording() {
    setErrorMsg(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        void analyze();
      };
      recorder.start();
      setElapsed(0);
      setState("listening");
    } catch {
      setErrorMsg("Microphone access was denied. Allow mic access to try live detection.");
      setState("error");
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    recorderRef.current = null;
  }

  async function analyze() {
    setState("analyzing");
    try {
      // MediaRecorder output is often labelled video/webm even when audio-only;
      // the transcription model requires an audio/* MIME type.
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      if (blob.size < 1000) {
        setErrorMsg("Recording was too short. Speak for a few seconds and try again.");
        setState("error");
        return;
      }
      const form = new FormData();
      form.append("file", new File([blob], "recording.webm", { type: "audio/webm" }));
      const res = await fetch("/api/public/detect-language", { method: "POST", body: form });
      const data = (await res.json()) as {
        text?: string;
        language?: string;
        error?: string | { message?: string };
      };
      if (!res.ok) {
        const msg =
          typeof data.error === "string"
            ? data.error
            : (data.error?.message ?? `Detection failed (${res.status}).`);
        setErrorMsg(msg);
        setState("error");
        return;
      }
      setResult({
        language: data.language ? languageLabel(data.language) : null,
        transcript: data.text?.trim() || null,
      });
      setState("done");
    } catch {
      setErrorMsg("Could not reach the detection service. Check your connection and retry.");
      setState("error");
    }
  }

  const busy = state === "analyzing";

  return (
    <Section id="try">
      <SectionHeader
        eyebrow="Try Praxis"
        title="Try Praxis"
        sub="Speak into your microphone — the language is detected live from your voice."
      />

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <Pill tone="accent">Live language detection</Pill>
        <Pill tone="warn">Other evidence modules not connected</Pill>
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
              ) : state === "analyzing" ? (
                "ANALYZING…"
              ) : state === "done" ? (
                "COMPLETE"
              ) : state === "error" ? (
                "ERROR"
              ) : (
                "READY"
              )}
            </span>
          </div>

          <div className="px-4 py-5">
            <Waveform active={state === "listening"} />

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <button
                disabled={busy}
                onClick={() => {
                  if (state === "listening") stopRecording();
                  else void startRecording();
                }}
                className={cn(
                  "inline-flex items-center gap-2 rounded-md px-5 py-3 font-mono text-[11px] tracking-[0.12em] uppercase disabled:opacity-60",
                  state === "listening"
                    ? "border border-border-strong bg-surface-2 text-foreground"
                    : "ridge-btn",
                )}
              >
                {busy ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Analyzing
                  </>
                ) : state === "listening" ? (
                  <>
                    <Square className="h-3.5 w-3.5" /> Stop &amp; detect
                  </>
                ) : (
                  <>
                    <Mic className="h-3.5 w-3.5" /> <span>Start analysis</span>
                  </>
                )}
              </button>
              <span className="text-[12px] text-muted-foreground">
                Speak a few seconds in any supported language, then stop.
              </span>
            </div>

            <dl className="mt-6 grid gap-px overflow-hidden rounded-md border border-border bg-border sm:grid-cols-2">
              {[
                ["Detected language", state === "done" ? (result?.language ?? "Auto-detected") : "—"],
                ["Audio quality", state === "idle" ? "—" : state === "listening" ? "Capturing" : "Captured"],
                ["Mode", "Live microphone"],
                ["Inference", "Language detection only"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between bg-card px-3 py-2.5">
                  <dt className="label-xs">{k}</dt>
                  <dd className="font-mono text-[11px] text-foreground">{v}</dd>
                </div>
              ))}
            </dl>

            {state === "done" && result?.transcript ? (
              <div className="mt-4 rounded-md border border-border bg-surface/70 px-3 py-2.5">
                <div className="label-xs">Transcript</div>
                <p className="mt-1.5 text-sm leading-relaxed text-foreground/85">
                  {result.transcript}
                </p>
              </div>
            ) : null}

            {state === "error" && errorMsg ? (
              <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2.5 text-sm text-foreground/85">
                {errorMsg}
              </div>
            ) : null}
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
                <Pill tone={e.v === "LIVE" ? "accent" : "neutral"}>{e.v}</Pill>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Section>
  );
}
