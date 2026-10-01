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

## Backend and authenticated dashboard

The live Praxis implementation is kept alongside this public website. `backend/` contains the FastAPI and PostgreSQL service, `deployment/` its Docker configuration, and `praxis-dashboard/` the separate authenticated dashboard. The dashboard's **Current Sessions** panel reads connected calls and recorded analysis from the backend. The public website above remains a separate application.

To run the backend locally, start Docker Desktop, configure a new `.env` from `.env.example` without overwriting existing credentials, and run `scripts/start.ps1`. Model artifacts must be provisioned separately; see `docs/model-assets.json` and `docs/DEPLOYMENT.md`. Run `praxis-dashboard/start.cmd` to build and open the local dashboard. For Cloudflare Pages, configure `praxis-dashboard/` as the dashboard project's root and provide a publicly reachable, certificate-valid Praxis backend. See `praxis-dashboard/README.md` for its deployment settings.

The Android caller source is under `integrations/android/Praxis_Caller/`. On the tested phone, Android may silence third-party microphone capture during a cellular call, leaving a connected session without usable audio or a score. The V2 score is experimental (`BOOTSTRAP_UNTRAINED`), not a calibrated scam probability. This repository excludes local secrets, database data, raw audio, model weights, cached dependencies, generated APKs, and private run logs.

© 2026 Praxis_


