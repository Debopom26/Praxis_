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
$url = 'https://localhost/'
Write-Output "Opening connected Praxis dashboard at $url"
if (-not $NoOpen) { Start-Process $url }
