$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$testScratch = Join-Path $projectRoot ('.cache\pytest-' + [guid]::NewGuid().ToString())
Push-Location $projectRoot
try {
    & $pythonPath -m pytest -q -p no:cacheprovider --basetemp $testScratch -c backend/pyproject.toml backend/tests
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    & $pythonPath -m mypy --config-file backend/pyproject.toml backend/src
    if ($LASTEXITCODE -ne 0) { throw 'Type checks failed.' }
    & $pythonPath -m ruff check --config backend/pyproject.toml backend/src backend/tests
    if ($LASTEXITCODE -ne 0) { throw 'Lint checks failed.' }
    & $pythonPath -m bandit -q -r backend/src
    if ($LASTEXITCODE -ne 0) { throw 'Security checks failed.' }
    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency failed.' }
} finally { Pop-Location }
