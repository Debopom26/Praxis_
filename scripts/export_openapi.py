import base64
import json
import secrets
from pathlib import Path

from praxis.config import Settings
from praxis.main import create_app

# Disposable configuration only; export does not open the DB or load models.
settings = Settings(database_url="postgresql+psycopg://schema-export@localhost/praxis",
    jwt_secret=secrets.token_urlsafe(48), embedding_key_base64=base64.b64encode(secrets.token_bytes(32)).decode(),
    models_enabled=False, _env_file=None)
app = create_app(settings)
target = Path(__file__).resolve().parents[1] / "contracts/openapi/openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
app.state.repository.engine.dispose()
print("Exported OpenAPI")
