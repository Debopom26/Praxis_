$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$connector = Join-Path $projectRoot 'runtime\cloudflared.exe'
if (-not (Test-Path -LiteralPath $connector)) { throw 'Missing runtime/cloudflared.exe. Install the official Cloudflare connector first.' }
$connection = [System.Net.Sockets.TcpClient]::new()
try { $connection.Connect('127.0.0.1', 8787); $running = $true }
catch [System.Net.Sockets.SocketException] { $running = $false }
finally { $connection.Dispose() }
if (-not $running) {
    Start-Process -FilePath $python -ArgumentList @((Join-Path $PSScriptRoot 'tunnel_gateway.py')) -WindowStyle Hidden
    Start-Sleep -Seconds 2
}
Write-Host 'Keep this window open. The tunnel address will update automatically; no dashboard redeployment.'
Write-Host 'Phone server: https://praxisdashboard.debopomrc2602.workers.dev/'
& $python (Join-Path $PSScriptRoot 'tunnel_launcher.py')
if ($LASTEXITCODE -ne 0) { throw 'Tunnel startup failed. See the message above; no server readiness is claimed.' }
