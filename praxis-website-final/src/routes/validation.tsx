import { createFileRoute } from "@tanstack/react-router";
import { ValidationMatrix } from "@/components/praxis/ValidationMatrix";
import { ResearchSection } from "@/components/praxis/ResearchSection";
import { TeamSection } from "@/components/praxis/TeamSection";

export const Route = createFileRoute("/validation")({
  head: () => ({
    meta: [
      { title: "Praxis Validation — What Is Measured and What Is Not" },
      {
        name: "description",
        content:
          "Implementation and runtime verification status of the current Praxis modules, with the scope of existing checks.",
      },
      { property: "og:title", content: "Praxis Validation — What Is Measured and What Is Not" },
      {
        property: "og:description",
        content: "Validation status, research basis and the team behind Praxis.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ValidationPage,
});

function ValidationPage() {
  return (
    <>
      <ValidationMatrix />
      <ResearchSection />
      <TeamSection />
    </>
  );
}
