import { createFileRoute } from "@tanstack/react-router";
import { FaqSection } from "@/components/praxis/FaqSection";
import { FullPraxisCTA } from "@/components/praxis/FullPraxisCTA";

export const Route = createFileRoute("/faq")({
  head: () => ({
    meta: [
      { title: "Praxis FAQ — Questions Judges and Engineers Ask" },
      {
        name: "description",
        content:
          "What Praxis detects, how it treats authorised AI agents, what happens when a channel is unavailable, and how organisations integrate it.",
      },
      { property: "og:title", content: "Praxis FAQ — Questions Judges and Engineers Ask" },
      {
        property: "og:description",
        content: "Direct answers about detection scope, failure modes, privacy and integration.",
      },
    ],
  }),
  component: FaqPage,
});

function FaqPage() {
  return (
    <>
      <FaqSection />
      <FullPraxisCTA />
    </>
  );
}
