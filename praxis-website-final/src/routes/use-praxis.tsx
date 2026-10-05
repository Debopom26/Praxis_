import { createFileRoute } from "@tanstack/react-router";
import { DocsHub } from "@/components/praxis/DocsHub";

export const Route = createFileRoute("/use-praxis")({
  head: () => ({
    meta: [
      { title: "Praxis Integration Documentation" },
      {
        name: "description",
        content:
          "Integration documentation for connecting Praxis through the Kotlin SDK, REST and streaming interfaces.",
      },
      { property: "og:title", content: "Praxis Integration Documentation" },
      {
        property: "og:description",
        content: "Integration guidance for the Praxis system.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: UsePraxis,
});

function UsePraxis() {
  return (
    <>
      <DocsHub />
    </>
  );
}
