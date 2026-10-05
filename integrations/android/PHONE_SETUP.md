# Connect the phone to Praxis

1. Restart Windows once. Docker Desktop currently has a locked stale socket at
   `C:\Users\KIIT\AppData\Local\Docker\run\sailor-ingest.sock`; only a Windows restart can clear it.
   After restart, start Docker Desktop and keep the phone/computer on the same Wi-Fi.
2. From `C:\Users\KIIT\Downloads\Praxis_`, run `./scripts/start.ps1`. This starts the persistent
   supplied-model worker and the Docker/PostgreSQL/Caddy backend without replacing existing secrets.
3. Install Praxis-Local-CA.crt on the phone as a CA certificate through Android security settings.
   This is the public certificate only. The debug APK trusts user-installed CAs; certificate and
   hostname checks remain enabled. Never install or transfer the private CA key.
4. Install Praxis-Caller-Connected.apk. Its debug signing key differs from the supplied APK
   (the source ZIP did not contain the original key), so Android cannot install it as an update.
   To use this build, uninstall the old app first, or supply the original signing key for a compatible
   update. Uninstalling clears this app's local settings; reselect it as the default Phone app afterward.
5. Use an existing Praxis organization administrator/host account. If none exists, run
   `./integrations/android/Create-Praxis-Account.ps1` from PowerShell on this computer.
   It prompts for organization ID, name, username and a hidden password; no default login exists.
6. During an active call, tap Connect to Praxis. Enter the **Phone on the same network**
   HTTPS address printed by `scripts/start.ps1`, then your organization ID, username and
   password. Sign in and connect.
   The token is encrypted with Android Keystore. The password is not saved. Approve the explicit
   microphone consent prompt for the controlled demo. Keep the other phone muted to avoid mixed audio.

If the computer changes Wi-Fi/network, rerun `scripts/start.ps1`; it discovers the new private
LAN address, updates Caddy's configured HTTPS names, and prints the current phone URL. Enter
that new URL on the phone. A previously saved phone address cannot update itself. The installed
Praxis local CA remains the trust anchor; TLS certificate and hostname validation stay enabled.
This is a local development endpoint, not a public internet deployment.
The phone's actual connection still requires manual verification. The workstation test passed
real PostgreSQL-backed login, session creation, authenticated WSS hello, and session end with
normal TLS checks. Its temporary account was removed. No microphone recording was started.

The app sends consented microphone audio as 16 kHz mono, analyzes 4-second windows with 2-second
overlap, and displays the experimental V2 score and guidance. The supplied model runtime remains
bootstrap/untrained, so the displayed value is not a calibrated scam probability. CPU inference is
slower than the 2-second hop; capture continues while stale analysis windows are dropped.

The same HTTPS /api/v1/auth/login and session APIs can serve Android and browser clients.
The webapp interface is in integrations/webapp; its actual origin/CORS/deployment must be verified
when connected. No OAuth service, default credentials, TLS bypass, or app-specific backend fork added.

2026-10-01 update: The Android source no longer prepopulates a fixed server IP. Existing installations may retain their previously saved address until edited. Show/Hide password is available. Silent microphone windows display unavailable and retry; call-time recovery still needs phone testing.
