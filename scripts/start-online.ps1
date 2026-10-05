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
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        $desktop = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'
        if (-not (Test-Path $desktop)) { $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe' }
        if (-not (Test-Path $desktop)) { throw 'Open Docker Desktop, unpause it, and retry.' }
        Start-Process -FilePath $desktop -WindowStyle Hidden
        Write-Host 'Waiting for Docker Desktop. Unpause it if needed...'
        $deadline = (Get-Date).AddMinutes(3)
        do {
            Start-Sleep -Seconds 3
            & docker info *> $null
        } while ($LASTEXITCODE -ne 0 -and (Get-Date) -lt $deadline)
        if ($LASTEXITCODE -ne 0) { throw 'Docker is not ready. Open/unpause Docker Desktop and retry.' }
    }
    & (Join-Path $PSScriptRoot 'start.ps1')
    & (Join-Path $PSScriptRoot 'start-tunnel.ps1')
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
