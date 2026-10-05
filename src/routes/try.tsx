import { createFileRoute } from "@tanstack/react-router";
import { TryPraxis } from "@/components/praxis/TryPraxis";
import { AttackLab } from "@/components/praxis/AttackLab";
import { FullPraxisCTA } from "@/components/praxis/FullPraxisCTA";

export const Route = createFileRoute("/try")({
  head: () => ({
    meta: [
      { title: "Try Praxis — Live Evidence Walkthrough" },
      {
        name: "description",
        content:
          "Run a guided scenario through the Praxis evidence channels and see how an outcome is formed from acoustic, speaker, linguistic and contextual signals.",
      },
      { property: "og:title", content: "Try Praxis — Live Evidence Walkthrough" },
      {
        property: "og:description",
        content: "Explore Praxis scenarios and the attack lab without deploying infrastructure.",
      },
    ],
  }),
  component: TryPage,
});

function TryPage() {
  return (
    <>
      <TryPraxis />
      <AttackLab />
      <FullPraxisCTA />
    </>
  );
}
