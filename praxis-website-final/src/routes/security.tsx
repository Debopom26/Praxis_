import { createFileRoute } from "@tanstack/react-router";
import { SecuritySection } from "@/components/praxis/SecuritySection";

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
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SecurityPage,
});

function SecurityPage() {
  return (
    <>
      <SecuritySection />
    </>
  );
}
