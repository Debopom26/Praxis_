$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$docker = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe"
Push-Location $projectRoot
try {
    & $docker compose --env-file .env -f deployment/compose.yaml exec backend python scripts/create_admin.py
    if ($LASTEXITCODE -ne 0) { throw "Account creation did not complete. Existing accounts were not replaced." }
} finally { Pop-Location }
