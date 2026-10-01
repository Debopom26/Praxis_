$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$dashboardRoot = Join-Path $projectRoot 'praxis-dashboard'
$target = Join-Path $projectRoot 'integrations\dashboard-dist'
if (-not (Test-Path -LiteralPath (Join-Path $dashboardRoot 'package.json'))) {
    throw "Dashboard source not found at $dashboardRoot"
}
Push-Location $dashboardRoot
try {
    if (-not (Test-Path -LiteralPath (Join-Path $dashboardRoot 'node_modules\.bin\vite.cmd'))) {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Dashboard dependency install failed.' }
    }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Dashboard build failed.' }
} finally { Pop-Location }
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -Path (Join-Path $dashboardRoot 'dist\*') -Destination $target -Recurse -Force
Write-Output "Dashboard files copied to $target. Restart the Praxis Caddy service to serve them."
