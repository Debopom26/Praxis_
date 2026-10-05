import { createFileRoute } from "@tanstack/react-router";

// Live language-detection demo endpoint for Try Praxis.
// 1. Transcribes a short mic recording with the gateway transcription model
//    (auto-detects among 85+ languages but returns only text).
// 2. Identifies the language of the transcript with the default chat model.

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // Gemini transcribe caps files at 14 MB
const TRANSCRIBE_MODEL = "google/gemini-3.5-transcribe";
const CHAT_MODEL = "openai/gpt-6-astra";
const GATEWAY = "https://ai.gateway.lovable.dev";

async function identifyLanguage(apiKey: string, transcript: string): Promise<string | null> {
  const response = await fetch(`${GATEWAY}/v1/responses`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "X-Lovable-AIG-SDK": "fetch",
    },
    body: JSON.stringify({
      model: CHAT_MODEL,
      stream: true,
      store: false,
      reasoning: { effort: "low" },
      input:
        "Identify the language of the following transcript. " +
        "Reply with only the language name in English (e.g. Hindi, Tamil, English). " +
        "If unsure, reply with your best guess. Transcript: " +
        transcript.slice(0, 2000),
    }),
  });
  if (!response.ok || !response.body) {
    console.error(`Language identification failed [${response.status}]: ${await response.text()}`);
    return null;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let text = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      for (const line of event.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        try {
          const parsed = JSON.parse(payload) as { type?: string; delta?: string };
          if (parsed.type === "response.output_text.delta" && typeof parsed.delta === "string") {
            text += parsed.delta;
          }
        } catch {
          // ignore keep-alive or partial lines
        }
      }
    }
  }
  const cleaned = text.trim().replace(/[."]+$/, "");
  return cleaned || null;
}

export const Route = createFileRoute("/api/public/detect-language")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const apiKey = process.env["LOVABLE_API_KEY"];
        if (!apiKey) {
          return Response.json({ error: "Language detection is not configured." }, { status: 500 });
        }

        const declared = Number(request.headers.get("content-length") ?? 0);
        if (declared > MAX_UPLOAD_BYTES) {
          return Response.json({ error: "Recording is too large." }, { status: 413 });
        }

        let file: File | null = null;
        try {
          const form = await request.formData();
          const value = form.get("file");
          if (value instanceof File) file = value;
        } catch {
          return Response.json({ error: "Invalid upload." }, { status: 400 });
        }

        if (!file || !file.size || file.size > MAX_UPLOAD_BYTES) {
          return Response.json({ error: "Missing or invalid audio file." }, { status: 400 });
        }
        if (!file.type.startsWith("audio/")) {
          return Response.json({ error: "Unsupported audio format." }, { status: 400 });
        }

        const upstream = new FormData();
        upstream.append("model", TRANSCRIBE_MODEL);
        upstream.append("file", file, file.name || "recording.webm");
        upstream.append("response_format", "json");
        // No `language` field: the model auto-detects among 85+ languages.
        // Buffered (non-streaming) because this is a one-shot detection.

        const transcribeRes = await fetch(`${GATEWAY}/v1/audio/transcriptions`, {
          method: "POST",
          headers: { Authorization: `Bearer ${apiKey}` },
          body: upstream,
        });

        const transcribeBody = await transcribeRes.text();
        if (!transcribeRes.ok) {
          console.error(`Transcription failed [${transcribeRes.status}]: ${transcribeBody}`);
          return new Response(transcribeBody, {
            status: transcribeRes.status,
            headers: {
              "content-type": transcribeRes.headers.get("content-type") ?? "application/json",
            },
          });
        }

        let transcript: string | null = null;
        try {
          const parsed = JSON.parse(transcribeBody) as { text?: string };
          transcript = parsed.text?.trim() || null;
        } catch {
          transcript = null;
        }

        if (!transcript) {
          return Response.json(
            { error: "No speech was detected in the recording. Speak clearly and try again." },
            { status: 422 },
          );
        }

        const language = await identifyLanguage(apiKey, transcript);
        return Response.json({ text: transcript, language });
      },
    },
  },
});
