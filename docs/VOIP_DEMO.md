# Praxis internet-call demo

Praxis Caller now has an **Internet** tab for two signed-in users of the same organization. It uses an authenticated, tenant-scoped WSS relay. The caller's microphone frame is sent to the other phone; each phone sends only the **incoming** voice to its own existing Praxis analysis session. No call PCM is retained by the relay. The score remains provisional while the risk regressor is untrained.

## Setup

1. Start Praxis with `scripts/start.ps1`. Use the printed `https://<current-LAN-IP>/` address on both phones. Both must have the trusted Praxis debug CA bundled in the new APK; TLS/hostname validation stays enabled.
2. Sign in to both phones using **different usernames in the same organization**. The existing administrator can create another `host` account with `docker compose --env-file .env -f deployment/compose.yaml exec backend python /app/scripts/create_host.py` from the project root. This interactive command asks for the existing organization ID, a new username, and a password without echoing it. It does not create a default account.
3. Keep Praxis Caller open on both phones. On the Internet tab of phone A, enter phone B's Praxis username and tap **Internet call**. Phone B accepts in the Internet tab. Grant microphone permission on each phone when requested.
4. Speak normally using the handset or headset. Each phone should hear the other and show its own analysis of the *remote* voice after enough speech has arrived. A score is shown only after the backend returns a real result.

The cellular Phone/Call tabs remain separate. The Internet tab does not dial SIM numbers, PSTN numbers, or emergency services. Both parties need this app and a working connection to the same Praxis backend. A second device cannot sign in with the same account at the same time. Incoming calls while the app process is stopped are not supported; this demo has no push wake-up service. Simultaneous cellular calls are rejected by the VoIP path. A Wi-Fi/network drop ends the active call; reconnect to start another. Backend uses one worker because the relay is memory-only. Current CPU model inference can lag behind speech, even when the call audio itself is live.

## Verification boundary

Backend tests cover authenticated two-party audio exchange, hangup, tenant separation, RBAC, and malformed media. Android unit tests, lint, and APK build cover the source but cannot prove handset audio routing or quality. A **two-phone acoustic test** is required before claiming the app-to-app call or score is reliable on hardware. Verify both voices, each side's incoming score, hangup, and a network interruption. Do not interpret a connected socket or silence-only frame as successful voice analysis.

Deployment verified 2026-10-02: the disposable scripts/verify_voip_live.py test passed trusted HTTPS, PostgreSQL account/login, both WSS audio directions and V2 analysis for both users. The included APK is integrations/android/Praxis-Caller-VoIP.apk (SHA-256 86A8F1267A4878E942BE4EEEED4FEE10FB6BBB2503522A676C906B07AB5E4605). This is a server-side test; it does not replace the two-phone audio/score test. The startup script prints the current LAN address, which changes with the network.

If an existing user's password is forgotten, run the local operator command from the project root: docker compose --env-file .env -f deployment/compose.yaml exec backend python /app/scripts/reset_account_password.py. It prompts for organization ID, username, and the new password twice. The current debug APK includes the Praxis local CA; install the current APK on both phones and keep TLS validation enabled.
