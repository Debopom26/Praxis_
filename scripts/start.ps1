$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop is required. Install/start it, then rerun this script.' }
$envPath = Join-Path $projectRoot '.env'
if (-not (Test-Path -LiteralPath $envPath)) { & (Join-Path $PSScriptRoot 'init-env.ps1') }
$values = @{}
Get-Content -LiteralPath $envPath | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { $values[$matches[1]] = $matches[2] }
}
if ($values['PRAXIS_SUPPLIED_MODELS_ENABLED'] -eq 'true') {
    if (-not $values['PRAXIS_SUPPLIED_WORKER_TOKEN']) { throw 'Missing PRAXIS_SUPPLIED_WORKER_TOKEN.' }
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $worker = Join-Path $projectRoot 'scripts\supplied_worker_server.py'
    $models = Join-Path $projectRoot 'model_paths.json'
    $connection = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection.Connect('127.0.0.1', 8765)
        $running = $true
    } catch [System.Net.Sockets.SocketException] {
        $running = $false
    } finally {
        $connection.Dispose()
    }
    if (-not $running) {
        Start-Process -FilePath $python -ArgumentList @($worker, '--model-paths', $models,
            '--env-file', $envPath, '--port', '8765') -WindowStyle Hidden
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -Headers @{
                Authorization = "Bearer $($values['PRAXIS_SUPPLIED_WORKER_TOKEN'])"
            } -TimeoutSec 5
        } catch {
            Start-Sleep -Seconds 5
            continue
        }
        if ($health.status -ne 'AVAILABLE') { throw 'Supplied model worker is unhealthy.' }
        $ready = $true
        break
    }
    if (-not $ready) { throw 'Supplied model worker did not become ready.' }
}
& docker compose --env-file $envPath -f (Join-Path $projectRoot 'deployment\compose.yaml') up --no-build -d
if ($LASTEXITCODE -ne 0) { throw 'Deployment did not start successfully.' }
