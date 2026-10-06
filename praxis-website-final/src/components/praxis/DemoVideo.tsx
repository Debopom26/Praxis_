import { Play } from "lucide-react";
import { Section, SectionHeader } from "./primitives";

export function DemoVideo() {
  return (
    <Section id="demo-video">
      <SectionHeader
        eyebrow="Demo"
        title="See Praxis in action."
      />

      <div className="panel mt-6 overflow-hidden p-0">
        <div className="relative bg-black">
          <video
            className="aspect-video w-full object-contain"
            controls
            playsInline
            preload="metadata"
            aria-label="Praxis demonstration video"
          >
            <source src="/praxis-demo.mp4" type="video/mp4" />
            Your browser does not support the video element.
          </video>
        </div>
        <div className="flex items-center gap-2 border-t border-border px-4 py-3 font-mono text-[11px] tracking-[0.1em] text-muted-foreground uppercase">
          <Play className="h-3.5 w-3.5 text-primary" />
          Praxis_ live demonstration
        </div>
      </div>
    </Section>
  );
}
