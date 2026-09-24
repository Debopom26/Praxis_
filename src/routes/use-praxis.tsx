import { createFileRoute } from "@tanstack/react-router";
import { FullPraxisCTA } from "@/components/praxis/FullPraxisCTA";
import { DeploymentSection } from "@/components/praxis/DeploymentSection";
import { DocsHub } from "@/components/praxis/DocsHub";

export const Route = createFileRoute("/use-praxis")({
  head: () => ({
    meta: [
      { title: "Use Full Praxis — Deployment and Access" },
      {
        name: "description",
        content:
          "Run the full Praxis analysis layer hosted or on-premise over LAN/VPN, integrated through the Kotlin SDK, REST and streaming interfaces.",
      },
      { property: "og:title", content: "Use Full Praxis — Deployment and Access" },
      {
        property: "og:description",
        content: "Deployment options and integration surface for the full Praxis system.",
      },
    ],
  }),
  component: UsePraxis,
});

function UsePraxis() {
  return (
    <>
      <FullPraxisCTA />
      <DeploymentSection />
      <DocsHub />
    </>
  );
}
