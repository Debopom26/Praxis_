import { ArrowUpRight, Smartphone, QrCode } from "lucide-react";
import { Section, SectionHeader, Note } from "./primitives";

const STEPS = [
  "Install Android Caller App",
  "Open Praxis Dashboard",
  "Log in",
  "Make a real demo call",
  "Explore actual evidence",
];

const META: Array<[string, string]> = [
  ["APK version", "— to be filled"],
  ["Release date", "— to be filled"],
  ["SHA-256", "— to be filled"],
  ["Minimum Android", "— to be filled"],
];

export function FullPraxisCTA() {
  return (
    <Section id="use-full-praxis">
      <div className="panel overflow-hidden border-primary/25 bg-primary/[0.03] p-6 sm:p-8">
        <SectionHeader
          eyebrow="Use full Praxis"
          title="Go beyond the demo."
          sub="The public website shows the analysis layer. The full product runs on a real call, through the Android caller app and the authenticated Praxis dashboard."
        />

        <div className="mt-7 grid gap-5 lg:grid-cols-[1.3fr_1fr]">
          <ol className="grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2">
            {STEPS.map((s, i) => (
              <li key={s} className="flex items-center gap-3 bg-card px-4 py-3.5">
                <span className="font-mono text-[11px] text-primary">0{i + 1}</span>
                <span className="text-sm">{s}</span>
              </li>
            ))}
            <li className="flex flex-wrap items-center gap-2 bg-card px-4 py-3.5">
              <a
                href="#"
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 font-mono text-[11px] tracking-[0.1em] text-primary-foreground uppercase"
              >
                <Smartphone className="h-3.5 w-3.5" /> Install Android App
              </a>
              <a
                href="#"
                className="inline-flex items-center gap-1.5 rounded-md border border-border-strong px-3 py-2 font-mono text-[11px] tracking-[0.1em] uppercase hover:bg-accent"
              >
                Open Praxis Dashboard <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </li>
          </ol>

          <div className="panel p-4">
            <div className="flex items-start gap-4">
              <div className="grid h-24 w-24 shrink-0 place-items-center rounded-md border border-dashed border-border-strong text-muted-foreground">
                <QrCode className="h-8 w-8" />
              </div>
              <div className="grid flex-1 gap-2">
                {META.map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-3 border-b border-border pb-1.5 last:border-0">
                    <span className="label-xs">{k}</span>
                    <span className="font-mono text-[11px] text-muted-foreground">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <Note>
              Release metadata and the QR code are placeholders until the build is published. The
              authenticated dashboard is a separate product and is not embedded in this website.
            </Note>
          </div>
        </div>
      </div>
    </Section>
  );
}
