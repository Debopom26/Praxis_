import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="label-xs flex items-center gap-2">
      <span className="h-1 w-1 rounded-full bg-primary" />
      {children}
    </div>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  sub,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  sub?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
      <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl md:text-[2.15rem] md:leading-[1.15]">
        {title}
      </h2>
      {sub ? <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">{sub}</p> : null}
    </div>
  );
}

export function Section({
  id,
  children,
  className,
  tone = "base",
}: {
  id?: string;
  children: ReactNode;
  className?: string;
  tone?: "base" | "raised";
}) {
  return (
    <section
      id={id}
      className={cn(
        "hairline-t scroll-mt-20 px-5 py-16 sm:px-8 md:py-20",
        tone === "raised" && "bg-surface/50",
        className,
      )}
    >
      <div className="mx-auto w-full max-w-6xl">{children}</div>
    </section>
  );
}

type Tone = "neutral" | "good" | "warn" | "bad" | "info" | "accent";

const toneClass: Record<Tone, string> = {
  neutral: "border-border text-muted-foreground",
  good: "border-signal/35 text-signal bg-signal/10",
  warn: "border-warn/35 text-warn bg-warn/10",
  bad: "border-destructive/40 text-destructive bg-destructive/10",
  info: "border-info/35 text-info bg-info/10",
  accent: "border-primary/40 text-primary bg-primary/10",
};

export function Pill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[10px] tracking-[0.12em] uppercase",
        toneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return (
    <p className="mt-4 flex gap-2 font-mono text-[11px] leading-relaxed text-muted-foreground/80">
      <span className="text-primary">//</span>
      <span>{children}</span>
    </p>
  );
}
