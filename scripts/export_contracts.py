"""Export canonical schemas and explicit TEST fixtures, never runtime defaults."""
import base64
import json
from pathlib import Path
from praxis import contracts as c
from praxis.contracts.context import CONTEXT_RULES

root=Path(__file__).resolve().parents[1]/"contracts"
for name in c.__all__:
    cls=getattr(c,name)
    if isinstance(cls,type) and issubclass(cls,c.Contract) and cls is not c.Contract:
        (root/"schemas"/(name+".json")).write_text(json.dumps(cls.model_json_schema(),indent=2)+"\n")
now="2026-09-20T00:00:00Z"
quality=dict(clipping_ratio=0,silence_ratio=0,snr_proxy_db=None,duration_ms=4000,completeness=1)
summary=[dict(module="context",status="AVAILABLE",reason_codes=["TEST_FIXTURE"])]
examples={
"SessionStart":dict(tenant_id="test-tenant",call_id="test-call",host_app_id="test-host",created_at=now),
"AudioFrame":dict(sequence_id=0,timestamp_ms=0,format=dict(sample_rate=16000,channels=1),audio_base64=base64.b64encode(bytes(320)).decode()),
"AudioWindow":dict(call_id="test-call",window_id="test-0",sequence_id=0,start_ms=0,end_ms=4000,audio_reference="test-transient",original_sample_rate=16000,original_channels=1,analysis_sample_rate=16000,speech_spans=[dict(start_ms=0,end_ms=4000)],vad_model_version="test-only",quality=quality,timestamp=now),
"SpeakerEvidence":dict(call_id="test-call",module="speaker",model_version=None,status="UNAVAILABLE",latency_ms=0,reason_codes=["NOT_ENROLLED"],timestamp=now),
"TranscriptEvent":dict(call_id="test-call",text="Explicit test fixture",language="en",segments=[dict(start_ms=0,end_ms=1000,text="Explicit test fixture")],quality=1,status="AVAILABLE",model_version="test-only",latency_ms=1,timestamp=now),
"ContextEvidence":dict(call_id="test-call",config_version="test-only",status="UNAVAILABLE",flags=dict.fromkeys(CONTEXT_RULES,"UNKNOWN"),context_score=None,reason_codes=["NO_CONTEXT"],timestamp=now),
"RiskEvent":dict(call_id="test-call",window_id="test-0",risk_raw_0_100=60,risk_display_0_100=60,evidence_summary=summary,quality={},missingness={},risk_model_version="TEST_FIXTURE_NOT_DEPLOYABLE",timestamp=now),
"PolicyEvent":dict(call_id="test-call",window_id="test-0",policy_version="test-only",action="SECONDARY_VERIFICATION",triggering_threshold_or_rule=">=60",verification_workflow="MFA",timestamp=now),
"UnavailableEvent":dict(call_id="test-call",module="risk",status="UNAVAILABLE",artifact_state="UNVALIDATED",reason_codes=["NO_VALIDATED_ARTIFACT"],timestamp=now),
"AuditEvent":dict(tenant_id="test-tenant",session_id="test-session",event_id="test-event",event_type="test",timestamp=now,status="AVAILABLE"),
}
for name,value in examples.items():
    model=getattr(c,name).model_validate(value)
    (root/"examples"/(name+".json")).write_text(model.model_dump_json(indent=2)+"\n")
print(f"Exported contracts and {len(examples)} explicit test fixtures")
