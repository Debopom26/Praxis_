import numpy as np
import pytest
from praxis.contracts import TranscriptEvent
from praxis.db.repository import utcnow
from praxis.linguistic import analyze_rules
from praxis.speaker import cosine


def transcript(text, language="en", status="AVAILABLE"):
    return TranscriptEvent(
        call_id="c",
        text=text,
        language=language,
        segments=[],
        quality=None,
        status=status,
        model_version="TEST_ONLY",
        latency_ms=0,
        timestamp=utcnow(),
    )


@pytest.mark.parametrize(
    "text,label",
    [
        ("Act now", "urgency"),
        ("Do not tell anyone", "secrecy"),
        ("I am the bank manager", "authority_pressure"),
        ("Transfer the money", "financial_request"),
        ("Share your OTP", "credential_request"),
        ("Bypass the verification", "verification_bypass"),
        ("You will be arrested", "coercion"),
        ("Your child is in danger", "emotional_pressure"),
    ],
)
def test_rule_categories(text, label):
    assert label in analyze_rules(transcript(text)).rule_labels


@pytest.mark.parametrize(
    "text", ["Never share your OTP.", "Do not transfer money.", "Have a good day."]
)
def test_benign_rules(text):
    assert analyze_rules(transcript(text)).rule_labels == []


def test_quality_and_language_gate():
    assert analyze_rules(transcript("Share your OTP", status="LOW_QUALITY")).status == "UNAVAILABLE"
    assert analyze_rules(transcript("Share your OTP", language="hi")).status == "UNAVAILABLE"


def test_cosine_no_fabricated_thresholds():
    assert cosine(np.array([1.0, 0]), np.array([1.0, 0])) == 1
    assert cosine(np.array([1.0, 0]), np.array([0.0, 1])) == 0
    for bad in [np.zeros(2), np.array([float("nan"), 1]), np.ones(3)]:
        with pytest.raises(ValueError):
            cosine(np.ones(2), bad)


def test_real_prosody_features():
    from praxis.audio.pipeline import SpeechWindows
    from praxis.prosody import Prosody

    rate = 16000
    one = 0.1 * np.sin(2 * np.pi * 120 * np.arange(rate) / rate).astype(np.float32)
    scheduler = SpeechWindows("c", rate, 1, "TEST_ONLY")
    windows = []
    for n in range(4):
        windows += scheduler.add(one, n * 1000)
    result = Prosody().analyze(windows[0])
    assert len([k for k in result.features if k.startswith("egemaps_")]) == 88
    assert result.calibrated_score is None
    assert result.features["praat_f0_median"] == pytest.approx(120, abs=2)


@pytest.mark.parametrize(
    "spans", [[], [(100, 0)], [(0, 1000), (500, 1500)], [(0, 500)], [(0, float("nan"))]]
)
def test_asr_rejects_invalid_source_spans_before_inference(spans):
    from praxis.asr import WhisperSmall

    model = object.__new__(WhisperSmall)
    with pytest.raises(ValueError):
        model.transcribe("c", np.zeros(16000), 16000, spans)


def test_asr_keeps_original_segments_and_gates_poor_translation():
    from threading import Lock

    from praxis.asr import WhisperSmall

    class Model:
        def transcribe(self, audio, task, **kwargs):
            return {
                "language": "hi",
                "text": "original" if task == "transcribe" else "translation",
                "segments": [
                    {
                        "start": 0,
                        "end": 1,
                        "text": task,
                        "avg_logprob": -2 if task == "translate" else -0.1,
                    }
                ],
            }

    model = object.__new__(WhisperSmall)
    model.model, model.lock, model.version = Model(), Lock(), "TEST_ONLY"
    event = model.transcribe("c", np.zeros(16000), 16000, [(1000, 2000)])
    assert len(event.segments) == 1 and event.segments[0].start_ms == 1000
    assert event.text == "original" and event.analysis_english is None
    assert event.status == "LOW_QUALITY"
