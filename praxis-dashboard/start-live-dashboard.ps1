param([switch]$NoOpen)
$ErrorActionPreference = 'Stop'
$praxisRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path -LiteralPath (Join-Path $praxisRoot 'scripts\start.ps1'))) {
    throw "Praxis backend not found at $praxisRoot"
}
$dockerBin = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'
if (Test-Path -LiteralPath (Join-Path $dockerBin 'docker.exe')) {
    $env:Path = "$dockerBin;$env:Path"
}
& (Join-Path $praxisRoot 'scripts\deploy-dashboard.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Dashboard build failed.' }
& (Join-Path $praxisRoot 'scripts\start.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Praxis backend did not start.' }
$sniLine = Get-Content -LiteralPath (Join-Path $praxisRoot '.env') |
    Where-Object { $_ -match '^PRAXIS_DEFAULT_SNI=' } | Select-Object -First 1
$server = if ($sniLine) { ($sniLine -split '=', 2)[1].Trim() } else { 'localhost' }
if (-not $server -or $server -notmatch '^[A-Za-z0-9.-]+$') { throw 'Invalid Praxis server address in .env.' }
$url = "https://$server/"
Write-Output "Opening connected Praxis dashboard at $url"
if (-not $NoOpen) { Start-Process $url }
