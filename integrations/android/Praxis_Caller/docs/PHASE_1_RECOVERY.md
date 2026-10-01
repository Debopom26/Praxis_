# Phase 1 recovery — 2026-09-28

Phase 1 remains BLOCKED. Found Studio-generated daemon JVM criteria selecting Java25; removed that file. verify_app.py now rejects regenerated criteria and asserts actual daemon/test JVM17. These repairs are NOT TESTED. Historical successful runs remain evidence, but printing JAVA_HOME's java.exe version alone did not establish the daemon version. The verifier performs build/test/lint and report copying; APK/signature/input-integrity inspection requires separate checks. Earlier prose overstated its scope.

After Studio AppData write access was granted, exec_command rejects even git status with `UnsupportedOperation("windows unelevated restricted-token sandbox cannot enforce split writable root sets directly; refusing to run unsandboxed")`. Do not route commands through another tool to bypass this refusal. File patches remain available. This continuation's changes are uncommitted.

Once shell execution works, inspect git status, then run from the task workspace containing work/ and outputs/:

```powershell
python outputs\Praxis_Caller\scripts\verify_app.py --java-home work\tools\jdk17\jdk-17.0.20.1+1 --android-sdk work\android-sdk --gradle-home work\tools\phase1-gradle\gradle-9.3.1 --work-dir work --run-name phase1-jdk17-repair
```

Inspect exitCode, PRAXIS_DAEMON_JAVA, test XML and lint. Fix failures and repeat the required loop. Verify Studio open/sync through native UI or fresh actual IDE logs. Native sky currently returned no Studio window after launch; that does not prove sync success. The user handled the privacy choice earlier. Do not redownload Studio or repeatedly kill unrelated Java processes/copy global caches. Preserve the portable wrapper URL/checksum.

User authorized all phases sequentially; no new permission to begin Phase 2 is needed once the current audit permits it under MASTER_PROMPT. All physical-device/SIM/auth/inference tests remain unperformed. Update controls/checkpoint from real new evidence.
