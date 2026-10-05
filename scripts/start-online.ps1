$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mutex = [System.Threading.Mutex]::new($false, 'Local\PraxisOnlineLauncher')
$locked = $false
try {
    try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) {
        Write-Host 'Praxis launcher is already open. Leave its window running; no second startup is needed.'
        Write-Host 'Dashboard/phone server: https://praxisdashboard.debopomrc2602.workers.dev/'
        Write-Host 'If it is stuck, close the existing launcher with Ctrl+C, then open this launcher again.'
        return
    }
    $dockerBin = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'
    if (Test-Path (Join-Path $dockerBin 'docker.exe')) { $env:Path = "$dockerBin;$env:Path" }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop is not installed.' }
    function Get-PraxisDockerState {
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $reply = (& docker info --format '{{.ServerVersion}}' 2>&1 | Out-String)
            $exitCode = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previousPreference }
        if ($exitCode -eq 0) { return 'READY' }
        if ($reply -match 'manually paused') { return 'PAUSED' }
        return 'UNAVAILABLE'
    }
    $dockerState = Get-PraxisDockerState
    if ($dockerState -eq 'PAUSED') {
        Write-Host 'Docker Desktop is paused. Open Docker Desktop and click Resume/Unpause, then open this launcher again.'
        return
    }
    if ($dockerState -ne 'READY') {
        $desktop = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'
        if (-not (Test-Path $desktop)) { $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe' }
        if (-not (Test-Path $desktop)) { throw 'Open Docker Desktop, unpause it, and retry.' }
        Start-Process -FilePath $desktop -WindowStyle Hidden
        Write-Host 'Waiting for Docker Desktop. Unpause it if needed...'
        $deadline = (Get-Date).AddMinutes(3)
        do {
            Start-Sleep -Seconds 3
            $dockerState = Get-PraxisDockerState
            if ($dockerState -eq 'PAUSED') {
                Write-Host 'Docker Desktop is paused. Click Resume/Unpause, then open this launcher again.'
                return
            }
        } while ($dockerState -ne 'READY' -and (Get-Date) -lt $deadline)
        if ($dockerState -ne 'READY') { throw 'Docker is not ready. Open Docker Desktop and retry.' }
    }
    & (Join-Path $PSScriptRoot 'start.ps1')
    & (Join-Path $PSScriptRoot 'start-tunnel.ps1')
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
