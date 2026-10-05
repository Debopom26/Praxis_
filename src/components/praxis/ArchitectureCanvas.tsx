import { useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Maximize2 } from "lucide-react";
import { Section, SectionHeader, Pill } from "./primitives";
import { cn } from "@/lib/utils";

type NodeDef = {
  id: string;
  label: string;
  x: number;
  y: number;
  w?: number;
  kind?: "input" | "module" | "engine" | "outcome";
  details: string[];
};

const NODES: NodeDef[] = [
  { id: "call", label: "LIVE CALL", x: 40, y: 20, kind: "input", details: ["Host application streams live audio", "Session + host context attached"] },
  { id: "audio", label: "AUDIO PIPELINE", x: 40, y: 100, kind: "module", details: ["Rolling windows", "Quality estimation", "Transient buffers only"] },
  { id: "spoof", label: "ANTI-SPOOF", x: 300, y: 20, kind: "module", details: ["W2V2-AASIST", "WavLM Anti-Spoof", "AASIST", "Individual calibration", "Acoustic fusion"] },
  { id: "prosody", label: "PROSODY", x: 300, y: 130, kind: "module", details: ["Pitch / energy contours", "Timing and pause structure", "Speaking-rate dynamics"] },
  { id: "speaker", label: "SPEAKER", x: 300, y: 240, kind: "module", details: ["ECAPA-TDNN", "Enrollment centroid", "MATCH / UNCERTAIN / MISMATCH / UNAVAILABLE"] },
  { id: "whisper", label: "WHISPER", x: 300, y: 350, kind: "module", details: ["Whisper small multilingual", "Original-language transcript", "Graceful degradation on failure"] },
  { id: "ling", label: "LINGUISTIC ANALYSIS", x: 560, y: 350, w: 190, kind: "module", details: ["Whisper transcript", "Multilingual rule packs", "Multilingual MiniLM"] },
  { id: "context", label: "CONTEXT ENGINE", x: 560, y: 240, w: 190, kind: "module", details: ["Host-supplied structured fields", "Explicit UNKNOWN handling", "Workflow / beneficiary / urgency"] },
  { id: "risk", label: "RISK ENGINE", x: 560, y: 110, w: 190, kind: "engine", details: ["Available calibrated evidence", "Quality", "Missingness", "Validated fusion model"] },
  { id: "policy", label: "POLICY ENGINE", x: 560, y: 20, w: 190, kind: "engine", details: ["Organization-configurable", "ALLOW / WARN / VERIFY / ESCALATE / HOLD"] },
];

const EDGES: Array<[string, string]> = [
  ["call", "audio"],
  ["audio", "spoof"],
  ["audio", "prosody"],
  ["audio", "speaker"],
  ["audio", "whisper"],
  ["whisper", "ling"],
  ["ling", "risk"],
  ["context", "risk"],
  ["spoof", "risk"],
  ["prosody", "risk"],
  ["speaker", "risk"],
  ["risk", "policy"],
];

const OUTCOMES = ["ALLOW", "WARN", "VERIFY", "ESCALATE", "HOLD"] as const;

const NODE_W = 150;
const NODE_H = 46;

function center(n: NodeDef) {
  return { cx: n.x + (n.w ?? NODE_W) / 2, cy: n.y + NODE_H / 2 };
}

export function ArchitectureCanvas() {
  const [selected, setSelected] = useState<string>("risk");
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const reduced = useReducedMotion();
  const node = NODES.find((n) => n.id === selected)!;

  return (
    <Section id="how-praxis-thinks">
      <SectionHeader
        eyebrow="Architecture"
        title="How Praxis Thinks"
        sub="Independent evidence is evaluated before an operational decision is made."
      />

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_300px]">
        {/* Desktop canvas */}
        <div className="panel relative hidden overflow-hidden md:block">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="label-xs">Node canvas · drag to pan, scroll to zoom</span>
            <button
              onClick={() => {
                setPan({ x: 0, y: 0 });
                setZoom(1);
              }}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 font-mono text-[10px] tracking-[0.1em] text-muted-foreground uppercase hover:border-border-strong hover:text-foreground"
            >
              <Maximize2 className="h-3 w-3" /> Reset view
            </button>
          </div>
          <div
            className="relative h-[460px] cursor-grab overflow-hidden active:cursor-grabbing"
            onPointerDown={(e) => {
              drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
              (e.target as Element).setPointerCapture?.(e.pointerId);
            }}
            onPointerMove={(e) => {
              if (!drag.current) return;
              setPan({
                x: drag.current.px + (e.clientX - drag.current.x),
                y: drag.current.py + (e.clientY - drag.current.y),
              });
            }}
            onPointerUp={() => (drag.current = null)}
            onPointerLeave={() => (drag.current = null)}
            onWheel={(e) => {
              setZoom((z) => Math.min(1.6, Math.max(0.6, z - e.deltaY * 0.0012)));
            }}
          >
            <div className="absolute inset-0 grid-bg opacity-60" />
            <div
              className="absolute top-0 left-0 origin-top-left"
              style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
            >
              <svg width="820" height="440" className="absolute top-0 left-0 overflow-visible">
                {EDGES.map(([a, b]) => {
                  const na = NODES.find((n) => n.id === a)!;
                  const nb = NODES.find((n) => n.id === b)!;
                  const A = center(na);
                  const B = center(nb);
                  const on = selected === a || selected === b;
                  const mx = (A.cx + B.cx) / 2;
                  return (
                    <path
                      key={`${a}-${b}`}
                      d={`M ${A.cx} ${A.cy} C ${mx} ${A.cy}, ${mx} ${B.cy}, ${B.cx} ${B.cy}`}
                      fill="none"
                      stroke={on ? "var(--color-primary)" : "var(--color-border-strong)"}
                      strokeWidth={on ? 1.6 : 1}
                      className={reduced ? undefined : "flow-line"}
                      opacity={on ? 1 : 0.7}
                    />
                  );
                })}
              </svg>

              {NODES.map((n) => (
                <button
                  key={n.id}
                  onClick={() => setSelected(n.id)}
                  style={{ left: n.x, top: n.y, width: n.w ?? NODE_W, height: NODE_H }}
                  className={cn(
                    "absolute rounded-md border px-3 text-left font-mono text-[11px] tracking-[0.1em] transition-colors",
                    selected === n.id
                      ? "border-primary/70 bg-primary/12 text-foreground"
                      : n.kind === "engine"
                        ? "border-signal/35 bg-signal/[0.06] text-foreground/90 hover:border-signal/60"
                        : "border-border bg-card text-muted-foreground hover:border-border-strong hover:text-foreground",
                  )}
                >
                  <span className="flex h-full items-center">{n.label}</span>
                </button>
              ))}

              <div className="absolute" style={{ left: 560, top: 420 }}>
                <div className="flex gap-1.5">
                  {OUTCOMES.map((o) => (
                    <span
                      key={o}
                      className="rounded border border-border bg-surface px-2 py-1 font-mono text-[10px] tracking-[0.08em] text-muted-foreground"
                    >
                      {o}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile stacked flow */}
        <div className="panel divide-y divide-border md:hidden">
          {NODES.map((n) => (
            <button
              key={n.id}
              onClick={() => setSelected(selected === n.id ? "" : n.id)}
              className="w-full px-4 py-3 text-left"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] tracking-[0.1em]">{n.label}</span>
                <span className="text-muted-foreground">{selected === n.id ? "−" : "+"}</span>
              </div>
              {selected === n.id ? (
                <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
                  {n.details.map((d) => (
                    <li key={d}>· {d}</li>
                  ))}
                </ul>
              ) : null}
            </button>
          ))}
          <div className="flex flex-wrap gap-1.5 px-4 py-3">
            {OUTCOMES.map((o) => (
              <Pill key={o}>{o}</Pill>
            ))}
          </div>
        </div>

        <motion.div
          key={node.id}
          initial={reduced ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="panel hidden h-fit p-4 md:block"
        >
          <div className="label-xs">Node</div>
          <div className="mt-2 font-mono text-sm tracking-[0.08em] text-primary">{node.label}</div>
          <ul className="mt-3 grid gap-2 text-xs leading-relaxed text-muted-foreground">
            {node.details.map((d) => (
              <li key={d} className="flex gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-border-strong" />
                {d}
              </li>
            ))}
          </ul>
          <div className="mt-4 border-t border-border pt-3">
            <div className="label-xs">Policy outcomes</div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {OUTCOMES.map((o) => (
                <Pill key={o}>{o}</Pill>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </Section>
  );
}
