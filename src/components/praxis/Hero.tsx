import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { EvidenceFlow } from "./EvidenceFlow";
import { Eyebrow } from "./primitives";

const CAPABILITIES = [
  "REAL-TIME",
  "MULTILINGUAL",
  "MULTI-SIGNAL ANALYSIS",
  "PRIVACY-PRESERVING",
  "SDK / API INTEGRATION",
];

export function Hero() {
  const reduced = useReducedMotion();
  return (
    <section className="relative overflow-hidden px-5 pt-12 pb-14 sm:px-8 md:pt-16">
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-70" />
      <div className="relative mx-auto grid w-full max-w-6xl items-start gap-10 lg:grid-cols-[1.08fr_0.92fr]">
        <div>
          <Eyebrow>Real-time voice integrity</Eyebrow>
          <motion.h1
            initial={reduced ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="mt-4 text-[2.1rem] leading-[1.08] font-semibold tracking-tight sm:text-5xl md:text-[3.35rem]"
          >
            <span className="text-gradient-warm">Real-Time Voice Integrity</span>
            <br />
            for Live Calls.
          </motion.h1>
          <motion.p
            initial={reduced ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mt-5 max-w-xl text-[15px] leading-relaxed text-muted-foreground"
          >
            Praxis combines voice authenticity, speaker consistency, prosody, linguistic manipulation
            and contextual evidence to identify suspicious communication while a conversation is
            still happening.
          </motion.p>

          <div className="mt-7 flex flex-wrap items-center gap-2.5">
            <Link
              to="/try"
              className="group inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 font-mono text-[11px] tracking-[0.12em] text-primary-foreground uppercase transition-transform hover:-translate-y-px"
            >
              Try Praxis
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              to="/how-it-works"
              className="inline-flex items-center gap-2 rounded-md border border-border-strong px-4 py-2.5 font-mono text-[11px] tracking-[0.12em] uppercase hover:bg-accent"
            >
              How it works <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <Link
              to="/use-praxis"
              className="inline-flex items-center gap-2 rounded-md border border-signal/40 bg-signal/[0.07] px-4 py-2.5 font-mono text-[11px] tracking-[0.12em] text-signal uppercase hover:bg-signal/12"
            >
              Use full Praxis <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap gap-x-5 gap-y-2 border-t border-border pt-5">
            {CAPABILITIES.map((c) => (
              <span key={c} className="label-xs flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-signal" />
                {c}
              </span>
            ))}
          </div>
        </div>

        <motion.div
          initial={reduced ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
        >
          <EvidenceFlow />
        </motion.div>
      </div>
    </section>
  );
}
