import { createFileRoute } from "@tanstack/react-router";
import { DocsHub } from "@/components/praxis/DocsHub";
import { DeploymentSection } from "@/components/praxis/DeploymentSection";

export const Route = createFileRoute("/docs")({
  head: () => ({
    meta: [
      { title: "Praxis Documentation — SDK, API and Integration" },
      {
        name: "description",
        content:
          "Integration reference for Praxis: Kotlin SDK, REST over HTTPS, streaming over WSS and structured host context for the Context Engine.",
      },
      { property: "og:title", content: "Praxis Documentation — SDK, API and Integration" },
      {
        property: "og:description",
        content: "How to integrate Praxis alongside an existing call application.",
      },
    ],
  }),
  component: DocsPage,
});

function DocsPage() {
  return (
    <>
      <DocsHub />
      <DeploymentSection />
    </>
  );
}
