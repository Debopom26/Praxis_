import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import { cn } from "@/lib/utils";

type Node = { id: string; label: string; detail: string; tone?: "accent" | "signal" | "info" };

const ROWS: Node[][] = [
  [{ id: "call", label: "LIVE CALL", detail: "Audio arrives from the host application while the conversation is active." }],
  [{ id: "audio", label: "AUDIO", detail: "Rolling frames are normalised and quality-checked before analysis." }],
  [
    { id: "acoustic", label: "ACOUSTIC", detail: "Anti-spoofing models look for synthetic or manipulated speech evidence.", tone: "accent" },
    { id: "prosody", label: "PROSODY", detail: "Pitch, energy, timing and pause structure are examined.", tone: "accent" },
    { id: "speaker", label: "SPEAKER", detail: "Consistency with an enrolled speaker profile, when one exists.", tone: "accent" },
  ],
  [{ id: "linguistic", label: "LINGUISTIC", detail: "Transcript is analysed for social-engineering and manipulation patterns.", tone: "info" }],
  [{ id: "context", label: "CONTEXT", detail: "Caller, workflow, beneficiary and organisational context supplied by the host.", tone: "info" }],
  [{ id: "risk", label: "RISK ENGINE", detail: "Available, calibrated evidence is fused — missing evidence stays missing.", tone: "signal" }],
  [{ id: "policy", label: "POLICY ENGINE", detail: "Organisation-configurable outcome: ALLOW / WARN / VERIFY / ESCALATE / HOLD.", tone: "signal" }],
];

export function EvidenceFlow({ className }: { className?: string }) {
  const [active, setActive] = useState<string | null>(null);
  const reduced = useReducedMotion();
  const activeNode = ROWS.flat().find((n) => n.id === active);

  return (
    <div className={cn("panel relative overflow-hidden p-4 sm:p-5", className)}>
      <div className="flex items-center justify-between">
        <span className="label-xs">Evidence flow</span>
        <span className="label-xs flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-signal soft-pulse" /> live
        </span>
      </div>

      <div className="mt-4 grid gap-1.5">
        {ROWS.map((row, i) => (
          <div key={i}>
            <div
              className={cn(
                "grid gap-1.5",
                row.length === 3 ? "grid-cols-3" : "grid-cols-1",
              )}
            >
              {row.map((n) => (
                <button
                  key={n.id}
                  onMouseEnter={() => setActive(n.id)}
                  onFocus={() => setActive(n.id)}
                  onClick={() => setActive(n.id)}
                  className={cn(
                    "rounded-md border px-2 py-2.5 text-center font-mono text-[10px] tracking-[0.12em] transition-all sm:text-[11px]",
                    active === n.id
                      ? "border-primary/60 bg-primary/10 text-foreground"
                      : "border-border bg-surface/60 text-muted-foreground hover:border-border-strong hover:text-foreground",
                  )}
                >
                  {n.label}
                </button>
              ))}
            </div>
            {i < ROWS.length - 1 ? (
              <div className="flex justify-center py-1">
                <svg width="14" height="16" viewBox="0 0 14 16" aria-hidden>
                  <line
                    x1="7"
                    y1="0"
                    x2="7"
                    y2="16"
                    stroke="var(--color-border-strong)"
                    strokeWidth="1.5"
                    className={reduced ? undefined : "flow-line"}
                  />
                </svg>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <motion.div
        key={activeNode?.id ?? "idle"}
        initial={reduced ? false : { opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="mt-4 min-h-14 rounded-md border border-border bg-surface/70 p-3 text-xs leading-relaxed text-muted-foreground"
      >
        {activeNode ? (
          <>
            <span className="font-mono text-[10px] tracking-[0.14em] text-primary">
              {activeNode.label}
            </span>
            <p className="mt-1 text-foreground/80">{activeNode.detail}</p>
          </>
        ) : (
          <span className="font-mono text-[11px]">
            Hover a stage to inspect what it contributes.
          </span>
        )}
      </motion.div>
    </div>
  );
}
