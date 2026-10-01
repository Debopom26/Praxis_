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
6. During an active call, tap Connect to Praxis. The server address is prefilled as
   https://10.20.51.112/. Enter your organization ID, username and password, then Sign in and connect.
   The token is encrypted with Android Keystore. The password is not saved. Approve the explicit
   microphone consent prompt for the controlled demo. Keep the other phone muted to avoid mixed audio.

The address is editable if this computer's Wi-Fi IP changes; Caddy must also be configured for
that new address. This is a local development endpoint, not a public internet deployment.
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

2026-10-01 update: Latest connected-phone debug APK is Praxis-Caller-Connected.apk (SHA-256 F7EF92A7D2E4FF2AA8586C11E7369CB4EC3A5DE64E771B3346FC30A553BE97CC). The old debug build had a different signing key and was uninstalled before installing this one, so sign in again at the current HTTPS LAN address. Show/Hide password is available. Silent microphone windows now display unavailable and retry; call-time recovery still needs phone testing.
