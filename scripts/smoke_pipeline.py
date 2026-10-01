"""Real model orchestration using synthetic audio and an isolated SQLite audit fixture.

This is not PostgreSQL/TLS, accuracy, enrollment or real-time performance validation.
"""
import asyncio
import base64
import json
from contextlib import suppress
from pathlib import Path
import secrets
from time import perf_counter
from uuid import uuid4

import numpy as np
from scipy.signal import resample_poly
from math import gcd
from sqlalchemy import create_engine

from praxis.audio.decode import decode_clip
from praxis.config import Settings
from praxis.contracts import AudioFrame, SessionStart
from praxis.db.models import Base, Membership, Organization, User
from praxis.db.repository import Repository, utcnow
from praxis.orchestration import ModelProcessor
from praxis.runtime import Runtime
from praxis.security import hash_password


async def main():
    root = Path(__file__).resolve().parents[1]
    fixture = root / ".cache/synthetic-speech.wav"
    samples, rate = decode_clip(fixture.read_bytes())
    factor = gcd(rate, 16000)
    samples = resample_poly(samples, 16000 // factor, rate // factor)
    settings = Settings(database_url="postgresql+psycopg://unused@localhost/synthetic-smoke",
        jwt_secret=secrets.token_urlsafe(48), embedding_key_base64=base64.b64encode(secrets.token_bytes(32)).decode(),
        artifacts_dir=root / "artifacts", _env_file=None)
    database = root / ".cache" / ("synthetic-audit-" + str(uuid4()) + ".sqlite")
    engine = create_engine("sqlite:///" + database.as_posix(), connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)  # Isolated test fixture only; production uses Alembic/PostgreSQL.
    repo = Repository(engine)
    with repo.sessions.begin() as db:
        db.add(Organization(id="TEST_ONLY", name="Synthetic software fixture")); db.flush()
        db.add(User(id="TEST_ONLY", username="TEST_ONLY", password_hash=hash_password(secrets.token_urlsafe(24)), active=True)); db.flush()
        db.add(Membership(tenant_id="TEST_ONLY", user_id="TEST_ONLY", role="admin"))
    principal = repo.principal("TEST_ONLY", "TEST_ONLY")
    session = repo.start(principal, SessionStart(tenant_id="TEST_ONLY", call_id="synthetic-call", host_app_id="software-test", created_at=utcnow()))
    runtime = Runtime(settings)
    started = perf_counter()
    await asyncio.to_thread(runtime.load)
    print("Actual model registry initialized", flush=True)
    if any(v.status == "ERROR" for v in runtime.health.values()):
        raise RuntimeError("Model initialization failed")
    processor = ModelProcessor(runtime, repo, principal)
    events = []
    async def consume():
        while True:
            event = await processor.next_event()
            await asyncio.to_thread(repo.record_event, principal, session.session_id, event)
            row = {"type": event.type, "module": getattr(event, "module", event.type),
                   "status": getattr(event, "status", "AVAILABLE"), "reasons": getattr(event, "reason_codes", [])}
            if event.type == "transcript":
                row.update(text_nonempty=bool(event.text.strip()), language=event.language, segments=len(event.segments), latency_ms=event.latency_ms)
            events.append(row)
            processor.events.task_done()
    consumer = asyncio.create_task(consume())
    try:
        for sequence, start in enumerate(range(0, len(samples), 16000)):
            chunk = np.clip(samples[start:start+16000]*32767, -32768, 32767).astype("<i2")
            frame = AudioFrame(sequence_id=sequence, timestamp_ms=sequence*1000,
                format={"sample_rate":16000,"channels":1}, audio_base64=base64.b64encode(chunk.tobytes()).decode())
            repo.accept_sequence(principal, session.session_id, frame.sequence_id, frame.timestamp_ms)
            for event in await processor.process(session, frame):
                await processor.events.put(event)
            # Pace to completion for execution verification, not an SLA measurement.
            await asyncio.wait_for(processor.windows.join(), timeout=120)
        if processor.ai_task:
            await asyncio.wait_for(processor.ai_task, timeout=120)
        await asyncio.wait_for(processor.events.join(), timeout=15)
        if not any(e["type"] == "transcript" and e.get("text_nonempty") for e in events):
            raise RuntimeError("No actual transcript produced")
        if any(e["type"] == "risk" for e in events):
            raise RuntimeError("Unexpected risk without a validated artifact")
        if any(e["status"] == "ERROR" for e in events):
            raise RuntimeError("Model or orchestration error")
        report = {"fixture":"SYNTHETIC_TEST_ONLY", "persistence":"isolated SQLite fixture, not PostgreSQL",
            "accuracy_validated":False, "realtime_validated":False, "elapsed_seconds":round(perf_counter()-started,3),
            "events":events, "audit_records":len(repo.audit(principal,session.session_id,500))}
        (root / "docs/PIPELINE_SMOKE.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps({"events":len(events),"audit_records":report["audit_records"],"transcript_events":sum(e["type"]=="transcript" for e in events)}),flush=True)
    finally:
        consumer.cancel()
        with suppress(asyncio.CancelledError): await consumer
        await processor.close()
        await runtime.close()
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
