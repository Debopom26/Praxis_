$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$envPath = Join-Path $projectRoot '.env'
if (Test-Path -LiteralPath $envPath) { throw '.env already exists; refusing to overwrite keys or database credentials.' }
@'
import base64, secrets, sys
from pathlib import Path
p=Path(sys.argv[1])
values={"PRAXIS_HOST":"localhost", "PRAXIS_OWNER_PASSWORD":secrets.token_urlsafe(36),
        "PRAXIS_RUNTIME_PASSWORD":secrets.token_urlsafe(36), "PRAXIS_JWT_SECRET":secrets.token_urlsafe(48),
        "PRAXIS_EMBEDDING_KEY_BASE64":base64.b64encode(secrets.token_bytes(32)).decode(),
        "PRAXIS_SUPPLIED_MODELS_ENABLED":"true",
        "PRAXIS_SUPPLIED_WORKER_URL":"http://host.docker.internal:8765",
        "PRAXIS_SUPPLIED_WORKER_TOKEN":secrets.token_urlsafe(48)}
with p.open('x',encoding='utf-8') as f:
    f.write('\n'.join(k+'='+v for k,v in values.items())+'\n')
print('Created local .env. Values were not printed. Preserve the embedding key for retained data.')
'@ | & $pythonPath - $envPath
if ($LASTEXITCODE -ne 0) { throw 'Environment initialization failed.' }
