# Oracle Always Free migration checkpoint

Requested 2026-10-05. User will create the Free Tier account later. No Oracle server has been provisioned or tested.

An eligible VM can remain running independently of the laptop. The current documented Always Free ARM allowance is 2 OCPUs / 12 GB RAM, with no GPU. Capacity is not guaranteed and idle instances may be reclaimed. Do not upgrade to paid usage or allocate resources outside the account's displayed Always Free limits.

Official limits: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Next steps after account creation

1. Confirm the actual account quotas and available Always Free ARM capacity in its home region. Verify storage and public-network allowances before provisioning.
2. Provision an eligible Linux VM only. Keep PostgreSQL and the model worker private; restrict administrative SSH and expose only the required HTTPS/calling entry point.
3. Verify ARM64 support for the pinned Docker image digests and Python dependencies before deployment. Existing Windows environments cannot be copied as runnable Linux environments.
4. Recreate the existing main Python runtime and separate Python 3.10/Fairseq runtime. The supplied engine already has a native non-Windows worker launch branch; configure its Python path for Linux rather than WSL.
5. Transfer verified model artifacts with checksums and map local paths. Preserve models, preprocessing and scoring; do not retrain or silently substitute artifacts.
6. Measure full-model peak RAM and actual E2E latency. The 12 GB VM is not yet proven sufficient; do not enable swap or report missing models as successful analysis to hide capacity failures.
7. Migrate the existing PostgreSQL data and required keys through protected transfer/backup, preserving accounts. Do not put secrets or backups in GitHub.
8. Verify migrations, least-privilege credentials, tenant isolation, HTTPS/WSS and bidirectional calling with real analysis before changing the dashboard proxy origin.
9. Configure service restart on boot and retain the existing local deployment as rollback until remote verification passes.

This is a migration plan, not a deployed server. Guest dashboard browsing needs no VM; real authentication and calls still use the existing backend until cutover.
