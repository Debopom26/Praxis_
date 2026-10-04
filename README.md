# Praxis

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

Praxis is a voice-analysis prototype with a FastAPI/PostgreSQL backend, an authenticated live dashboard, an Android caller, and a separate public website. The Android **Internet** calling demo relays audio between two signed-in Praxis users and analyzes the incoming voice on each phone. The repository also contains the SDK, tests, and deployment scripts.

**Status:** A two-phone demo has delivered analysis to both phones, but a later call connected without delivering detailed analysis. The current V2 score uses a `BOOTSTRAP_UNTRAINED` risk regressor: it is experimental, not a calibrated probability of a scam. CPU inference can lag behind live speech. This is not a production-ready, always-on calling service.

## Find your way around

| Path | Purpose |
| --- | --- |
| [`backend/`](backend/) | FastAPI, authentication, session and analysis APIs, PostgreSQL persistence, and VoIP relay |
| [`praxis-dashboard/`](praxis-dashboard/) | Authenticated React/Vite dashboard for live sessions and analysis history |
| [`integrations/android/Praxis_Caller/`](integrations/android/Praxis_Caller/) | Android caller source; Internet calls and cellular dialer are separate modes |
| [`android-sdk/`](android-sdk/) | Praxis Android SDK source |
| [`deployment/`](deployment/) | Docker Compose, PostgreSQL, backend, and Caddy configuration |
| [`scripts/`](scripts/) | Startup, account creation, verification, and maintenance commands |
| [`src/`](src/) | Separate public website; its demonstrations are not live model inference |
| [`docs/`](docs/) | Architecture, traceability, deployment, and verification records |

Model weights, the local `model_paths.json`, environment secrets, database volumes, raw audio, and generated APKs are intentionally absent from Git. A source checkout alone cannot run the full model pipeline. Use the pinned asset information and deployment instructions in [`docs/`](docs/) and keep existing verified artifacts unchanged.

## Run the local backend and dashboard

On Windows, install/start Docker Desktop with Linux containers. From the repository root in PowerShell:

```powershell
.\scripts\start.ps1
```

The script starts the persistent local model worker when configured, then PostgreSQL, backend, and HTTPS dashboard. First model load can take several minutes. It prints the current LAN address for phones; the address can change when your network changes. The script creates `.env` only when missing and does not overwrite existing keys. Never commit `.env`.

Open `https://localhost/` after startup. A browser or phone must trust the Praxis local CA for local HTTPS; do not bypass certificate validation. The backend health endpoint is `/api/v1/health`. No default administrator credentials exist. To create an organization administrator interactively:

```powershell
docker compose --env-file .env -f deployment/compose.yaml exec backend python /app/scripts/create_admin.py
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for model assets, TLS, PostgreSQL, security, and verification details. To rebuild the dashboard served by local Caddy, run `.\scripts\deploy-dashboard.ps1` and restart Praxis, or use [`praxis-dashboard/start.cmd`](praxis-dashboard/start.cmd).

## Android Internet-call demo

Download the [current demo APK from GitHub Releases](https://github.com/Debopom26/Praxis_/releases/tag/v0.1.0-voip-demo). It is **debug-signed**, includes the local development CA for test connections, and is not a Play Store or production build. Its SHA-256 is `5A8E543DA0F8CBF3117DABBFE3FDFCFC8E387210E489B15D44559CD4CDE1FCBD`.

Both participants need the app, different active Praxis accounts in the same organization, and a connection to the same reachable backend. Enter the current HTTPS server address shown by `start.ps1` when testing on one LAN. A signed-in user places an Internet call to the other user's Praxis username; the recipient accepts in the app. Each phone analyzes the **other** person's voice. The Internet mode does not call ordinary SIM/PSTN numbers or emergency services. Incoming ringing after the app process is stopped requires push delivery, which is not implemented here. Read [`docs/VOIP_DEMO.md`](docs/VOIP_DEMO.md) for setup and limitations.

The cellular dialer can place normal phone calls, but Android may silence third-party microphone capture during a cellular call. It cannot reliably obtain the remote voice for Praxis analysis. This is why the two-party demo uses Internet calling.

## Deploy the dashboard later with Cloudflare Pages

The dashboard is separate from the public website. Connect this GitHub repository to Cloudflare Pages with root directory `praxis-dashboard`, build command `npm run build`, and output directory `dist`. Set the Pages runtime variable `PRAXIS_BACKEND_ORIGIN` to the **public HTTPS origin** of the Praxis backend. The included Pages Function forwards same-origin `/api/*` requests; a private `10.x.x.x` or `192.168.x.x` address cannot serve a cloud-hosted dashboard. The backend and model worker must themselves be hosted and reachable for sign-in and live analysis to work. Cloudflare hosting is not yet configured. See [`praxis-dashboard/README.md`](praxis-dashboard/README.md).

## Development checks

```powershell
.\scripts\test.ps1
cd praxis-dashboard
npm ci
npm run build
```

For the Android app, run `gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug` from `integrations/android/Praxis_Caller/`. These checks validate code and builds; they do not prove phone audio routing, detection accuracy, or cloud availability. See [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md) for the verified scope and remaining gaps.
