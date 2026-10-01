import asyncio
from types import SimpleNamespace

import numpy as np
import pytest
from praxis.audio.pipeline import SpeechWindows
from praxis.contracts import SessionStart, TranscriptEvent
from praxis.db.models import AuditRecord, EvidenceRecord
from praxis.db.repository import utcnow
from praxis.orchestration import ModelProcessor, SpeechBuffer
from praxis.runtime import Runtime
from sqlalchemy import select


def windows():
    scheduler = SpeechWindows("c", 16000, 1, "TEST_ONLY")
    results = []
    for n in range(8):
        results += scheduler.add(np.full(16000, n, np.float32), n * 1000)
    return results


def test_asr_buffer_does_not_duplicate_overlap():
    speech = SpeechBuffer()
    results = [speech.add(w) for w in windows()]
    assert results[0] is None and results[1] is None
    samples, rate, spans = results[2]
    assert len(samples) == 8 * rate
    assert sum(end - start for start, end in spans) == 8000
    for i in range(8):
        assert np.all(samples[i * rate : (i + 1) * rate] == i)


@pytest.mark.asyncio
async def test_model_failure_isolated_and_risk_remains_unavailable(repo, settings):
    runtime = Runtime(settings)

    class Broken:
        def analyze(self, window):
            raise RuntimeError("private data must not escape")

    runtime.models["prosody"] = Broken()
    principal = repo.principal("admin-a", "a")
    session = repo.start(
        principal, SessionStart(tenant_id="a", call_id="c", host_app_id="test", created_at=utcnow())
    )
    processor = ModelProcessor(runtime, repo, principal)
    await processor._analyze(session, windows()[0])
    events = []
    while not processor.events.empty():
        events.append(processor.events.get_nowait())
    assert any(getattr(e, "module", None) == "prosody" and e.status == "ERROR" for e in events)
    assert any(getattr(e, "module", None) == "risk" and e.status == "UNAVAILABLE" for e in events)
    assert all("private data" not in e.model_dump_json() for e in events)
    await processor.close()
    await runtime.close()


def test_transcript_persistence_is_metadata_only_and_audited(repo):
    principal = repo.principal("admin-a", "a")
    session = repo.start(
        principal, SessionStart(tenant_id="a", call_id="c", host_app_id="test", created_at=utcnow())
    )
    event = TranscriptEvent(
        call_id="c",
        text="CONFIDENTIAL",
        language="en",
        segments=[],
        quality=None,
        status="AVAILABLE",
        model_version="TEST_ONLY",
        latency_ms=1,
        timestamp=utcnow(),
        analysis_english="CONFIDENTIAL",
    )
    repo.record_event(principal, session.session_id, event)
    with repo.sessions() as db:
        row = db.scalar(select(EvidenceRecord))
        assert "CONFIDENTIAL" not in str(row.payload)
        assert len(list(db.scalars(select(AuditRecord)))) == 2


@pytest.mark.asyncio
async def test_low_priority_capacity_never_waits_for_qwen(repo, settings):
    runtime = Runtime(settings)
    processor = ModelProcessor(runtime, repo, repo.principal("admin-a", "a"))
    async with runtime.ai_lock:
        await asyncio.wait_for(processor._ai(SimpleNamespace(call_id="c"), "text"), 0.5)
    assert (await processor.next_event()).reason_codes == ["LOW_PRIORITY_CAPACITY"]
    await processor.close()
    await runtime.close()


@pytest.mark.asyncio
async def test_audio_failure_is_explicit_and_does_not_retry_every_frame(repo, settings):
    runtime = Runtime(settings)
    processor = ModelProcessor(runtime, repo, repo.principal("admin-a", "a"))
    calls = []

    def broken(frame):
        calls.append(frame)
        raise RuntimeError("test private diagnostic")

    processor.pipeline = SimpleNamespace(push=broken, close=lambda: None)
    session = SimpleNamespace(call_id="c")
    first = await processor.process(session, object())
    assert first[0].status == "ERROR" and first[0].reason_codes == ["AUDIO_PROCESSING_FAILED"]
    assert await processor.process(session, object()) == []
    assert len(calls) == 1
    await processor.close()
    await runtime.close()


@pytest.mark.asyncio
async def test_window_backpressure_is_bounded_and_reports_gap(repo, settings):
    runtime = Runtime(settings)
    processor = ModelProcessor(runtime, repo, repo.principal("admin-a", "a"))
    blocked, entered = asyncio.Event(), asyncio.Event()

    async def slow(session, window):
        entered.set()
        await blocked.wait()

    processor._analyze = slow
    window = windows()[0]
    processor.pipeline = SimpleNamespace(push=lambda frame: [window], close=lambda: None)
    session = SimpleNamespace(call_id="c")
    await processor.process(session, object())
    await asyncio.wait_for(entered.wait(), 1)
    for _ in range(4):
        await processor.process(session, object())
    assert processor.windows.qsize() == 2
    assert (await processor.next_event()).reason_codes == ["ANALYSIS_BACKPRESSURE_GAP"]
    await processor.close()
    await runtime.close()
