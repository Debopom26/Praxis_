import { createFileRoute } from "@tanstack/react-router";
import { ProblemStory } from "@/components/praxis/ProblemStory";
import { ArchitectureCanvas } from "@/components/praxis/ArchitectureCanvas";
import { DifferenceSection } from "@/components/praxis/DifferenceSection";
import { MultilingualSection } from "@/components/praxis/MultilingualSection";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "How Praxis Works — Evidence Channels and Risk Fusion" },
      {
        name: "description",
        content:
          "Anti-spoofing, speaker verification, prosody, linguistic analysis and context are calibrated separately, then fused with explicit handling of missing evidence.",
      },
      { property: "og:title", content: "How Praxis Works — Evidence Channels and Risk Fusion" },
      {
        property: "og:description",
        content: "The architecture behind real-time voice integrity decisions.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HowItWorks,
});

function HowItWorks() {
  return (
    <>
      <ProblemStory />
      <ArchitectureCanvas />
      <DifferenceSection />
      <MultilingualSection />
    </>
  );
}
