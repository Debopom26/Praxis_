import { useMemo, useState } from "react";
import { Search, Plus, Minus } from "lucide-react";
import { Section, SectionHeader } from "./primitives";

const FAQS: Array<[string, string]> = [
  ["What exactly does Praxis detect?", "Praxis evaluates evidence about a live conversation: acoustic authenticity, prosody, speaker consistency, linguistic manipulation patterns and organisational context. It produces an operational decision, not a verdict about a person."],
  ["Is Praxis just a deepfake detector?", "No. A detector answers whether audio is synthetic. Praxis asks whether the communication is trustworthy given voice, speaker, conversation and context."],
  ["Why multiple anti-spoof models?", "Different architectures fail on different attack types and recording conditions. Each model is calibrated individually before acoustic fusion, so no single model dominates the decision."],
  ["Why use deterministic rules and MiniLM?", "Rule packs give transparent, auditable coverage of known social-engineering phrasing. MiniLM generalises to paraphrases. Together they are more explainable than either alone."],
  ["How does Praxis handle legitimate AI agents?", "An authorised AI agent is a valid caller. When context marks the agent as authorised for that workflow, synthetic speech is expected and does not by itself raise the outcome."],
  ["Does synthetic speech automatically mean fraud?", "No. That assumption is explicitly rejected in the product design."],
  ["What happens if Whisper fails?", "The linguistic channel reports UNAVAILABLE. The risk engine accounts for the missing evidence instead of substituting a neutral value."],
  ["What happens if the caller is not enrolled?", "Speaker verification reports UNAVAILABLE. Other channels still contribute, and policy can require stronger verification when speaker evidence is missing."],
  ["How does speaker verification work?", "ECAPA-TDNN embeddings from the live call are compared with an encrypted enrollment centroid, producing MATCH, UNCERTAIN, MISMATCH or UNAVAILABLE."],
  ["Does Praxis store call audio?", "Live audio is analysed on rolling windows and discarded by default. Only approved enrollment audio produces a stored artifact, and it is stored as an encrypted embedding."],
  ["Can Praxis work offline/on-premise?", "Yes. The same analysis layer can run inside an organisation over LAN/VPN for privacy and control."],
  ["Why is the SIH demo hosted?", "So judges can evaluate the system immediately without deploying infrastructure."],
  ["How can banks/companies integrate Praxis?", "Through the Kotlin SDK, REST over HTTPS and streaming over WSS, supplying structured host context for the Context Engine."],
  ["Does Praxis replace the organization's call application?", "No. Praxis is a layer beside the call application; the host application keeps ownership of the call and of the user experience."],
  ["What happens when a model is unavailable?", "Its channel is marked UNAVAILABLE and the missingness is carried into fusion. Nothing is imputed silently."],
  ["How are false positives controlled?", "Per-model calibration, multi-channel corroboration, explicit missingness handling and organisation-configurable policy thresholds."],
  ["How is tenant data isolated?", "Data, speaker profiles and policy are scoped per tenant, with RBAC on top."],
  ["Can live calls retrain models automatically?", "No. Live call audio is not used for automatic retraining."],
  ["Which languages are supported?", "Thirteen target languages for Indian deployments. Architectural support is not the same as per-language validation, which is reported separately."],
];

export function FaqSection() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<string | null>(FAQS[0]?.[0] ?? null);

  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return FAQS;
    return FAQS.filter(([k, v]) => k.toLowerCase().includes(t) || v.toLowerCase().includes(t));
  }, [q]);

  return (
    <Section id="faq">
      <SectionHeader eyebrow="FAQ" title="Questions judges and engineers ask." />

      <div className="mt-6 flex items-center gap-2 rounded-md border border-border bg-surface/70 px-3 py-2.5 focus-within:border-primary/60">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search questions…"
          className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-border">
        {list.map(([k, v]) => {
          const on = open === k;
          return (
            <div key={k} className="border-b border-border last:border-0">
              <button
                onClick={() => setOpen(on ? null : k)}
                className="flex w-full items-center justify-between gap-4 px-4 py-3.5 text-left hover:bg-surface/60"
              >
                <span className="text-sm">{k}</span>
                {on ? (
                  <Minus className="h-4 w-4 shrink-0 text-primary" />
                ) : (
                  <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </button>
              {on ? (
                <p className="px-4 pb-4 text-xs leading-relaxed text-muted-foreground">{v}</p>
              ) : null}
            </div>
          );
        })}
        {list.length === 0 ? (
          <p className="px-4 py-6 text-sm text-muted-foreground">No questions match “{q}”.</p>
        ) : null}
      </div>
    </Section>
  );
}
