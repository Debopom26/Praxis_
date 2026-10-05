$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$dockerBin = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'
if (Test-Path -LiteralPath (Join-Path $dockerBin 'docker.exe')) { $env:Path = "$dockerBin;$env:Path" }
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
    $runtime = Join-Path $projectRoot 'runtime'
    $pidFile = Join-Path $runtime 'supplied-worker.json'
    $errorLog = Join-Path $runtime 'supplied-worker-startup.log'
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    function Get-TrackedWorker {
        if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
        try {
            $record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
            $process = Get-Process -Id ([int]$record.pid) -ErrorAction Stop
            if ($process.StartTime.ToUniversalTime().Ticks -eq [long]$record.started_utc_ticks) {
                return $process
            }
        } catch { return $null }
        return $null
    }
    $mutex = [System.Threading.Mutex]::new($false, 'Local\PraxisSuppliedWorkerStartup')
    $locked = $false
    try {
        try { $locked = $mutex.WaitOne(15000) }
        catch [System.Threading.AbandonedMutexException] { $locked = $true }
        if (-not $locked) { throw 'Another Praxis startup is preparing the model worker. Retry shortly.' }
        $tracked = Get-TrackedWorker
        $connection = [System.Net.Sockets.TcpClient]::new()
        try {
            $connection.Connect('127.0.0.1', 8765)
            $portOpen = $true
        } catch [System.Net.Sockets.SocketException] {
            $portOpen = $false
        } finally {
            $connection.Dispose()
        }
        if (-not $portOpen -and -not $tracked) {
            Write-Host 'Starting persistent model worker. First load may take several minutes.'
            $tracked = Start-Process -FilePath $python -ArgumentList @($worker, '--model-paths', $models,
                '--env-file', $envPath, '--port', '8765') -RedirectStandardError $errorLog -WindowStyle Hidden -PassThru
            @{ pid = $tracked.Id; started_utc_ticks = $tracked.StartTime.ToUniversalTime().Ticks } |
                ConvertTo-Json -Compress | Set-Content -LiteralPath $pidFile
        } elseif ($tracked -and -not $portOpen) {
            Write-Host 'Existing model worker is still loading; waiting for it.'
        }
    } finally {
        if ($locked) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
    $ready = $false
    $deadline = (Get-Date).AddMinutes(8)
    $lastProgress = (Get-Date).AddSeconds(-15)
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -Headers @{
                Authorization = "Bearer $($values['PRAXIS_SUPPLIED_WORKER_TOKEN'])"
            } -TimeoutSec 3
        } catch {
            if ($tracked -and -not (Get-TrackedWorker)) {
                throw "Model worker exited during startup. See $errorLog"
            }
            if (((Get-Date) - $lastProgress).TotalSeconds -ge 15) {
                Write-Host 'Loading local models (Whisper, MiniLM, Qwen, W2V2); please wait...'
                $lastProgress = Get-Date
            }
            Start-Sleep -Seconds 5
            continue
        }
        if ($health.status -ne 'AVAILABLE') { throw 'Supplied model worker is unhealthy.' }
        $ready = $true
        break
    }
    if (-not $ready) { throw "Model worker did not become ready within eight minutes. See $errorLog" }
    Write-Host 'Model worker ready.'
}
$lanAddresses = @(& (Join-Path $PSScriptRoot 'network-address.ps1'))
$previousHost = [Environment]::GetEnvironmentVariable('PRAXIS_HOST', 'Process')
$previousSni = [Environment]::GetEnvironmentVariable('PRAXIS_DEFAULT_SNI', 'Process')
try {
    $env:PRAXIS_HOST = (@('localhost') + $lanAddresses) -join ', '
    $env:PRAXIS_DEFAULT_SNI = if ($lanAddresses.Count) { $lanAddresses[0] } else { 'localhost' }
    Write-Host 'Starting PostgreSQL, backend and HTTPS dashboard...'
    & docker compose --env-file $envPath -f (Join-Path $projectRoot 'deployment\compose.yaml') up --no-build -d
    if ($LASTEXITCODE -ne 0) { throw 'Deployment did not start successfully.' }
} finally {
    [Environment]::SetEnvironmentVariable('PRAXIS_HOST', $previousHost, 'Process')
    [Environment]::SetEnvironmentVariable('PRAXIS_DEFAULT_SNI', $previousSni, 'Process')
}
Write-Host 'Praxis dashboard/backend: https://localhost/'
foreach ($address in $lanAddresses) { Write-Host "Phone on the same network: https://$address/" }
if (-not $lanAddresses.Count) { Write-Warning 'No private LAN address found. Phone access is unavailable until a LAN connection is active and Praxis is restarted.' }
