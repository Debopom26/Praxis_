import { createFileRoute } from "@tanstack/react-router";
import { Hero } from "@/components/praxis/Hero";
import { ProblemStory } from "@/components/praxis/ProblemStory";
import { DifferenceSection } from "@/components/praxis/DifferenceSection";
import { TryPraxis } from "@/components/praxis/TryPraxis";
import { ArchitectureCanvas } from "@/components/praxis/ArchitectureCanvas";
import { MultilingualSection } from "@/components/praxis/MultilingualSection";
import { ValidationMatrix } from "@/components/praxis/ValidationMatrix";
import { SecuritySection } from "@/components/praxis/SecuritySection";
import { DeploymentSection } from "@/components/praxis/DeploymentSection";
import { FullPraxisCTA } from "@/components/praxis/FullPraxisCTA";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Praxis_ — Real-Time Voice Integrity for Live Calls" },
      {
        name: "description",
        content:
          "Praxis analyses voice authenticity, speaker consistency, prosody, language and context while a call is still happening.",
      },
      { property: "og:title", content: "Praxis_ — Real-Time Voice Integrity for Live Calls" },
      {
        property: "og:description",
        content:
          "A real-time voice-integrity and communication-risk layer for live calls, built on multi-channel evidence.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <>
      <Hero />
      <ProblemStory />
      <DifferenceSection />
      <TryPraxis />
      <ArchitectureCanvas />
      <MultilingualSection />
      <ValidationMatrix />
      <SecuritySection />
      <DeploymentSection />
      <FullPraxisCTA />
    </>
  );
}
