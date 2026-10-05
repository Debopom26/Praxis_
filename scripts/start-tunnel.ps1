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
Write-Host 'Keep this window open. Copy the HTTPS trycloudflare address into the dashboard backend setting and Android server address.'
Write-Host 'This launcher starts Praxis on sign-in. It cannot wake an off/asleep PC. Temporary address changes after restart.'
& $connector tunnel --no-autoupdate --url http://127.0.0.1:8787
