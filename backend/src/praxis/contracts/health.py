from pydantic import AwareDatetime, Field

from .base import Contract, Identifier, Version
from .status import ArtifactState, ModuleStatus


class ModelArtifactStatus(Contract):
    module: Identifier
    state: ArtifactState
    version: Version | None = None
    reason_codes: list[str] = Field(default_factory=list)


class ComponentHealth(Contract):
    status: ModuleStatus
    version: Version | None = None
    reason_codes: list[str] = Field(default_factory=list)


class HealthStatus(Contract):
    service_version: Version
    contract_version: Version
    status: ModuleStatus
    components: dict[str, ComponentHealth]
    artifacts: list[ModelArtifactStatus]
    timestamp: AwareDatetime
