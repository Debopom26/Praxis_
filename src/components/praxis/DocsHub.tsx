import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Section, SectionHeader, Note } from "./primitives";

const CATEGORIES: Array<{ title: string; items: Array<[string, string]> }> = [
  {
    title: "Overview",
    items: [
      ["What is Praxis?", "A real-time voice-integrity and communication-risk layer for live calls."],
      ["Quick Start", "Attach the SDK to a call session, supply host context, consume policy events."],
      ["Product Boundaries", "Praxis advises a decision; it does not replace the host call application."],
    ],
  },
  {
    title: "Architecture",
    items: [
      ["End-to-End Data Flow", "Call → audio pipeline → evidence channels → risk fusion → policy."],
      ["Audio Pipeline", "Rolling windows, quality estimation, transient buffers only."],
      ["Risk / Policy Flow", "Calibrated evidence with explicit missingness, then configurable policy."],
    ],
  },
  {
    title: "Models",
    items: [
      ["Anti-Spoofing", "RawNet2, AASIST, WavLM anti-spoof with individual calibration and fusion."],
      ["Prosody", "Pitch, energy, timing, pause structure and speaking-rate dynamics."],
      ["Speaker", "ECAPA-TDNN embeddings compared with an enrollment centroid."],
      ["ASR", "Whisper small multilingual, original-language output."],
      ["Linguistic", "Deterministic rule packs plus multilingual MiniLM semantics."],
    ],
  },
  {
    title: "Multilingual",
    items: [
      ["13-language architecture", "Target language set for Indian deployments."],
      ["Transcript pipeline", "Speech → Whisper → original-language transcript → analysis."],
      ["Validation", "Language-level validation is reported separately, not assumed."],
    ],
  },
  {
    title: "Training & Data",
    items: [
      ["Dataset roles", "Which corpora serve training, calibration and evaluation."],
      ["Splits", "Speaker-disjoint and condition-disjoint splits."],
      ["Calibration", "Per-model score calibration before fusion."],
      ["Artifact versions", "Every deployed model artifact is versioned and pinned."],
    ],
  },
  {
    title: "Integration",
    items: [
      ["Kotlin SDK", "Android caller integration for live sessions."],
      ["REST HTTPS", "Session lifecycle, enrollment and policy configuration."],
      ["WSS", "Streaming audio frames and incremental evidence events."],
      ["Host Context", "Structured fields with explicit UNKNOWN handling."],
    ],
  },
  {
    title: "Security",
    items: [
      ["TLS / WSS", "Encrypted transport for all traffic."],
      ["JWT", "Short-lived signed tokens per host session."],
      ["RBAC", "Role-scoped access to sessions and enrollment."],
      ["Tenant Isolation", "Per-organisation scoping of data and profiles."],
    ],
  },
  {
    title: "Deployment",
    items: [
      ["Hosted demo", "Judge-accessible deployment for evaluation."],
      ["Self-hosted", "LAN/VPN deployment inside the organisation."],
      ["Docker", "Container images for the server and model runtime."],
    ],
  },
  {
    title: "Validation",
    items: [
      ["Metrics", "Published only with protocol and artifact versions."],
      ["Latency", "Measured per stage on the streaming path."],
      ["Limitations", "Known failure modes and unsupported conditions."],
    ],
  },
];

export function DocsHub() {
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return CATEGORIES;
    return CATEGORIES.map((c) => ({
      ...c,
      items: c.items.filter(
        ([k, v]) => k.toLowerCase().includes(t) || v.toLowerCase().includes(t) || c.title.toLowerCase().includes(t),
      ),
    })).filter((c) => c.items.length > 0);
  }, [q]);

  return (
    <Section id="docs">
      <SectionHeader
        eyebrow="Documentation"
        title="Documentation hub"
        sub="Short, diagram-oriented pages instead of one long document. Search across every section."
      />

      <div className="mt-6 flex items-center gap-2 rounded-md border border-border bg-surface/70 px-3 py-2.5 focus-within:border-primary/60">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search documentation…"
          className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((c) => (
          <div key={c.title} className="panel panel-hover p-4">
            <div className="label-xs">{c.title}</div>
            <ul className="mt-3 grid gap-2.5">
              {c.items.map(([k, v]) => (
                <li key={k} className="border-b border-border pb-2.5 last:border-0 last:pb-0">
                  <div className="text-[13px] text-foreground">{k}</div>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{v}</p>
                </li>
              ))}
            </ul>
          </div>
        ))}
        {filtered.length === 0 ? (
          <p className="text-sm text-muted-foreground">No documentation entries match “{q}”.</p>
        ) : null}
      </div>

      <Note>
        Documentation summaries describe the implemented system. Pages that depend on validation
        results stay unpublished until those results exist.
      </Note>
    </Section>
  );
}
