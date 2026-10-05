from time import perf_counter

from praxis.contracts import ArtifactState, ModuleEvidence, Provenance
from praxis.db.repository import utcnow


def evidence(
    call_id,
    window_id,
    module,
    version,
    status,
    started,
    features=None,
    reasons=None,
    artifact_state=ArtifactState.NOT_LOADED,
):
    return ModuleEvidence(
        call_id=call_id,
        window_id=window_id,
        module=module,
        model_version=version,
        status=status,
        features=features or {},
        latency_ms=(perf_counter() - started) * 1000,
        reason_codes=reasons or [],
        provenance=Provenance(model_version=version, artifact_state=artifact_state),
        timestamp=utcnow(),
    )
