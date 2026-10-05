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
          "An honest status matrix of Praxis capabilities: what has been validated, what is architectural support only, and what remains open research.",
      },
      { property: "og:title", content: "Praxis Validation — What Is Measured and What Is Not" },
      {
        property: "og:description",
        content: "Validation status, research basis and the team behind Praxis.",
      },
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
