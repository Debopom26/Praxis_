import { useEffect, useRef } from "react";
import { useReducedMotion } from "motion/react";
import { Play } from "lucide-react";
import { Section, SectionHeader } from "./primitives";

export function DemoVideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Autoplay must be muted for browsers (including mobile Safari) to allow it.
    // Keep controls available so the viewer can explicitly enable sound.
    let inView = false;
    const syncPlayback = () => {
      if (inView && document.visibilityState === "visible" && !reducedMotion) {
        void video.play().catch(() => {
          // Browser autoplay may still be blocked; the native Play control remains available.
        });
      } else {
        video.pause();
      }
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        inView = entry.isIntersecting && entry.intersectionRatio >= 0.55;
        syncPlayback();
      },
      { threshold: [0, 0.55, 1] },
    );

    observer.observe(video);
    document.addEventListener("visibilitychange", syncPlayback);

    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", syncPlayback);
      video.pause();
    };
  }, [reducedMotion]);

  return (
    <Section id="demo-video">
      <SectionHeader
        eyebrow="Demo"
        title="See Praxis in action."
        sub="The demonstration plays automatically when it comes into view, and pauses when you scroll away."
      />

      <div className="panel mt-6 overflow-hidden p-0">
        <div className="relative bg-black">
          <video
            ref={videoRef}
            className="aspect-video w-full object-contain"
            controls
            muted
            playsInline
            preload="metadata"
            aria-label="Praxis demonstration video"
          >
            <source src="/praxis-demo.mp4" type="video/mp4" />
            Your browser does not support the video element.
          </video>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border px-4 py-3 font-mono text-[11px] tracking-[0.1em] text-muted-foreground uppercase">
          <span className="inline-flex items-center gap-2">
            <Play className="h-3.5 w-3.5 text-primary" />
            Praxis_ live demonstration
          </span>
          <span>Autoplay is muted · enable sound in player controls</span>
        </div>
      </div>
    </Section>
  );
}
