import base64
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PRAXIS_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    database_url: SecretStr
    jwt_secret: SecretStr
    embedding_key_base64: SecretStr
    jwt_issuer: str = "praxis"
    jwt_audience: str = "praxis-sdk"
    token_ttl_minutes: int = Field(default=30, ge=1, le=30)
    artifacts_dir: Path = Path("artifacts")
    max_message_bytes: int = Field(default=262144, ge=1024, le=1048576)
    stream_timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_connections: int = Field(default=16, ge=1, le=100)
    max_frames_per_second: int = Field(default=100, ge=1, le=200)
    models_enabled: bool = True
    supplied_models_enabled: bool = False
    model_paths_file: Path = Path("model_paths.json")
    supplied_worker_url: str | None = None
    supplied_worker_token: SecretStr | None = None
    webapp_origins: list[str] = Field(default_factory=list)
    inference_workers: int = Field(default=2, ge=1, le=4)
    torch_threads: int = Field(default=2, ge=1, le=8)
    risk_artifact: Path | None = None
    risk_artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def check(self):
        if "*" in self.webapp_origins:
            raise ValueError("Explicit webapp origins required")
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("PostgreSQL psycopg URL required")
        if len(self.jwt_secret.get_secret_value().encode()) < 32:
            raise ValueError("JWT secret requires at least 32 bytes")
        if len(base64.b64decode(self.embedding_key_base64.get_secret_value(), validate=True)) != 32:
            raise ValueError("AES-256 key requires exactly 32 decoded bytes")
        if bool(self.supplied_worker_url) != bool(self.supplied_worker_token):
            raise ValueError("Supplied worker URL and token must be configured together")
        if self.supplied_worker_url and not self.supplied_worker_url.startswith("http://host.docker.internal:"):
            raise ValueError("Supplied worker must use the Docker host gateway")
        return self
