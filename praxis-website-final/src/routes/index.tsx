import { createFileRoute } from "@tanstack/react-router";
import { Hero } from "@/components/praxis/Hero";
import { ProblemStory } from "@/components/praxis/ProblemStory";
import { DemoVideo } from "@/components/praxis/DemoVideo";
import { DifferenceSection } from "@/components/praxis/DifferenceSection";
import { ArchitectureCanvas } from "@/components/praxis/ArchitectureCanvas";
import { MultilingualSection } from "@/components/praxis/MultilingualSection";
import { ValidationMatrix } from "@/components/praxis/ValidationMatrix";
import { SecuritySection } from "@/components/praxis/SecuritySection";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Praxis_ â€” Real-Time Voice Integrity for Live Calls" },
      {
        name: "description",
        content:
          "Praxis analyses voice authenticity, speaker consistency, prosody, language and context while a call is still happening.",
      },
      { property: "og:title", content: "Praxis_ â€” Real-Time Voice Integrity for Live Calls" },
      {
        property: "og:description",
        content:
          "A real-time voice-integrity and communication-risk layer for live calls, built on multi-channel evidence.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <>
      <Hero />
      <ProblemStory />
      <DemoVideo />
      <DifferenceSection />
      <ArchitectureCanvas />
      <MultilingualSection />
      <ValidationMatrix />
      <SecuritySection />
    </>
  );
}
