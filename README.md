# PRAXIS_ — Real-Time Voice Integrity for Live Calls

Public website for Praxis. Built with TanStack Start, React 19, TypeScript, Vite 7 and Tailwind CSS v4.

## Requirements
- Node.js 20+ (or Bun 1.1+)

## Setup
```sh
npm install        # or: bun install
npm run dev        # open http://localhost:8080
```

## Production build
```sh
npm run build
npm run preview
```

## Project structure
- `src/routes/` — pages (/, /try, /how-it-works, /docs, /validation, /security, /faq, /use-praxis)
- `src/components/praxis/` — site sections (Hero, TryPraxis, AttackLab, ArchitectureCanvas, ...)
- `src/styles.css` — design tokens and utilities

## Editing content
- Validation status: `src/components/praxis/ValidationMatrix.tsx` (COMPONENTS array)
- Team: `src/components/praxis/TeamSection.tsx`
- APK/QR placeholders: `src/components/praxis/FullPraxisCTA.tsx`

## Sharing
- **Live link:** publish from Lovable (Publish button) for a permanent public URL.
- **Temporary preview:** Lovable → Share → Share preview (7 days, no login).
- **Code:** push this folder to GitHub, or share this ZIP.
- **Self-host:** run `npm run build` and deploy to any Node/edge host (default target: Cloudflare Workers).

Demo and scenario simulations on the site are clearly marked and do not represent real model inference.

# Praxis_ System Architecture

> **Praxis_** analyzes live call audio, combines acoustic, linguistic, identity and trusted contextual evidence, and produces an operational malicious-impersonation risk score with policy-driven actions.

---

```mermaid
flowchart TB

%% =========================================================
%% 0. ENTRY
%% =========================================================

CALL["📞 Live SIM Call"] --> SDK["Praxis_ SDK / Host"]


%% =========================================================
%% 1. AUDIO PREPROCESSING
%% =========================================================

subgraph PRE["1 · Audio Preprocessing"]
direction LR

DEC["Decode"]
MONO["Mono"]
SR["16 kHz"]
VAD["Silero VAD"]

DEC --> MONO --> SR --> VAD

end

SDK -->|"audio"| DEC


%% =========================================================
%% BUFFERING
%% =========================================================

VAD --> WIN["4 s<br/>Acoustic Window"]
VAD --> BUF["Rolling<br/>ASR Buffer"]


%% =========================================================
%% 2. ACOUSTIC / IDENTITY
%% =========================================================

subgraph ACO["2 · Voice Analysis"]
direction LR

W2V2["W2V2 / XLS-R<br/>+ AASIST"]

PROS["Prosody<br/>98 features"]

ECAPA["ECAPA-TDNN<br/>optional"]

end

WIN --> W2V2
WIN --> PROS
WIN --> ECAPA


%% Compact acoustic evidence bus

W2V2 --> AE["🎙️ Acoustic /<br/>Identity Evidence"]
PROS --> AE
ECAPA --> AE


%% =========================================================
%% 3. LANGUAGE
%% =========================================================

subgraph LANG["3 · Language Understanding"]
direction LR

WH["Whisper"]

MINI["MiniLM"]
RULES["Rules"]
QWEN["Qwen"]

WH --> MINI
WH --> RULES
WH --> QWEN

end

BUF --> WH


%% Compact language evidence bus

MINI --> LE["🧠 Language<br/>Evidence"]
RULES --> LE
QWEN --> LE


%% =========================================================
%% 4. CONTEXT
%% =========================================================

subgraph CTXBLOCK["4 · Context Engine V2"]
direction LR

CTX["Context Engine"]

AUTH["Authorized<br/>Synthetic?"]

IDENT["Identity<br/>Risk"]

SENS["Sensitive<br/>Action"]

CTX --> AUTH
CTX --> IDENT
CTX --> SENS

end

SDK -->|"trusted metadata"| CTX
W2V2 -->|"synthetic evidence"| CTX
ECAPA -->|"speaker evidence"| IDENT
MINI --> SENS
RULES --> SENS


%% Compact context evidence bus

AUTH --> CE["🧭 Context<br/>Evidence"]
IDENT --> CE
SENS --> CE


%% =========================================================
%% 5. EVIDENCE STATE + FUSION
%% =========================================================

AVAIL["Evidence State<br/>Available · Low Quality<br/>Unavailable · Error"]

AE --> FUSION
LE --> FUSION
CE --> FUSION
AVAIL --> FUSION

FUSION["5 · Deterministic Hierarchical<br/>Evidence Fusion"]


%% =========================================================
%% 6. RISK
%% =========================================================

FUSION --> RISK["6 · Praxis_ Risk<br/><b>0–100</b><br/>Malicious Impersonation"]


%% =========================================================
%% 7. POLICY
%% =========================================================

RISK --> POLICY["7 · Policy Engine"]


subgraph ACTIONS["Policy Actions"]
direction LR

ALLOW["0–39<br/>ALLOW"]
WARN["40–59<br/>WARN"]
VERIFY["60–79<br/>VERIFY"]
ESC["80–89<br/>ESCALATE"]
HOLD["90–100<br/>HOLD*"]

end

POLICY --> ALLOW
POLICY --> WARN
POLICY --> VERIFY
POLICY --> ESC
POLICY --> HOLD


%% =========================================================
%% HOLD SAFETY GATES
%% =========================================================

GATES["HOLD Safety Gates<br/>Independent evidence required"]

AE --> GATES
LE --> GATES
CE --> GATES

GATES --> HOLD


%% =========================================================
%% 8. PRODUCT OUTPUTS
%% =========================================================

subgraph OUT["8 · Product Outputs"]
direction LR

MOBILE["📱 Call Protection"]
DASH["📊 Dashboard"]
AUDIT["📋 Audit Evidence"]

end

POLICY --> MOBILE
POLICY --> DASH
FUSION --> AUDIT
POLICY --> AUDIT


%% =========================================================
%% 9. INFRASTRUCTURE
%% =========================================================

subgraph INFRA["9 · Infrastructure"]
direction LR

API["FastAPI"]
DB["PostgreSQL"]
SEC["JWT · RBAC<br/>TLS · AES-256-GCM"]
DEPLOY["Docker · Caddy"]

API --> DB
API --> SEC
API --> DEPLOY

end

SDK -.-> API
API -.-> FUSION
AUDIT -.-> DB


%% =========================================================
%% STYLES
%% =========================================================

classDef entry fill:#eaf2ff,stroke:#4285f4,color:#111827,stroke-width:2px;
classDef audio fill:#eef5ff,stroke:#4285f4,color:#111827;
classDef acoustic fill:#fff1e8,stroke:#ff7a21,color:#111827;
classDef support fill:#eaf8ef,stroke:#34a853,color:#111827;
classDef language fill:#f4efff,stroke:#8b5cf6,color:#111827;
classDef context fill:#eaf8ef,stroke:#34a853,color:#111827;
classDef evidence fill:#f8fafc,stroke:#64748b,color:#111827,stroke-width:2px;
classDef fusion fill:#fff1e8,stroke:#ff7a21,color:#111827,stroke-width:2px;
classDef risk fill:#fff0f0,stroke:#e5484d,color:#111827,stroke-width:3px;
classDef policy fill:#fff8df,stroke:#d9a514,color:#111827;
classDef danger fill:#ffe9e9,stroke:#e5484d,color:#111827,stroke-width:2px;
classDef product fill:#eef5ff,stroke:#4285f4,color:#111827;
classDef infra fill:#f3f4f6,stroke:#6b7280,color:#111827;

class CALL,SDK entry;

class DEC,MONO,SR,VAD,WIN,BUF audio;

class W2V2 acoustic;
class PROS,ECAPA support;

class WH,MINI,RULES,QWEN language;

class CTX,AUTH,IDENT,SENS context;

class AE,LE,CE,AVAIL evidence;

class FUSION fusion;

class RISK risk;

class POLICY,ALLOW,WARN,VERIFY,ESC policy;

class HOLD,GATES danger;

class MOBILE,DASH,AUDIT product;

class API,DB,SEC,DEPLOY infra;
```
Praxis_ combines voice authenticity, language, identity and trusted context before deciding whether a call represents malicious impersonation.

© 2026 Praxis_


