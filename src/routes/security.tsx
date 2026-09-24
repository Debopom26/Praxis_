import { createFileRoute } from "@tanstack/react-router";
import { SecuritySection } from "@/components/praxis/SecuritySection";
import { DeploymentSection } from "@/components/praxis/DeploymentSection";
import { FullPraxisCTA } from "@/components/praxis/FullPraxisCTA";

export const Route = createFileRoute("/security")({
  head: () => ({
    meta: [
      { title: "Praxis Security — Privacy, Tenancy and Data Handling" },
      {
        name: "description",
        content:
          "Live audio is analysed on rolling windows and discarded by default. Enrollment is stored as encrypted embeddings, scoped per tenant with RBAC.",
      },
      { property: "og:title", content: "Praxis Security — Privacy, Tenancy and Data Handling" },
      {
        property: "og:description",
        content: "How Praxis handles call audio, speaker profiles and tenant isolation.",
      },
    ],
  }),
  component: SecurityPage,
});

function SecurityPage() {
  return (
    <>
      <SecuritySection />
      <DeploymentSection />
      <FullPraxisCTA />
    </>
  );
}
