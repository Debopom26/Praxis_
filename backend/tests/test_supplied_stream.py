import numpy as np
from praxis.supplied.stream import MicrophoneWindows


class VadDouble:
    def __init__(self):
        self.model = self
        self.resets = 0

    def reset_states(self):
        self.resets += 1

    def speech(self, audio):
        return bool(np.any(audio))


def test_overlap_new_speech_and_gap():
    vad = VadDouble()
    stream = MicrophoneWindows(vad)
    blocks = [np.full(32000, i, dtype=np.float32) for i in (1, 2, 3, 4)]
    assert stream.push(0, blocks[0]) is None
    window, speech = stream.push(1, blocks[1])
    assert len(window) == len(speech) == 64000
    window, speech = stream.push(2, blocks[2])
    np.testing.assert_array_equal(window[:32000], blocks[1])
    np.testing.assert_array_equal(speech, blocks[2])
    assert stream.push(4, blocks[3]) is None
    assert vad.resets == 1


def test_silence_skipped_and_initial_speech_not_lost():
    stream = MicrophoneWindows(VadDouble())
    zero = np.zeros(32000, dtype=np.float32)
    assert stream.push(0, zero) is None
    assert stream.push(1, zero) is None
    result = stream.push(2, np.ones(32000, dtype=np.float32))
    assert result is not None
    stream.push(3, zero)  # One residual VAD frame may straddle the speech boundary.
    assert stream.push(4, zero) is None
    stream = MicrophoneWindows(VadDouble())
    assert stream.push(0, np.ones(32000, dtype=np.float32)) is None
    result = stream.push(1, zero)
    assert result is not None and len(result[1]) == 64000


def test_identical_text_cached_only_for_given_stream():
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace

    from praxis.supplied.engine import SuppliedEngine

    engine = object.__new__(SuppliedEngine)
    engine.request_lock = threading.Lock()
    engine.pool = ThreadPoolExecutor(max_workers=5)
    calls = {"minilm": 0, "qwen": 0}
    def minilm(text):
        calls["minilm"] += 1
        return {"status": "AVAILABLE", "triggered_labels": []}
    def qwen(text):
        calls["qwen"] += 1
        return {"status": "OK", "ai_script_probability": 0.1}
    engine.w2v2 = SimpleNamespace(analyze=lambda x: {"available": True, "predicted_class": "spoof", "spoof_softmax": 0.9})
    engine.whisper = lambda x: {"text": "The weather is sunny today."}
    engine.minilm = SimpleNamespace(analyze=minilm)
    engine.qwen = SimpleNamespace(predict=qwen)
    engine.prosody = SimpleNamespace(analyze=lambda x: {})
    engine.rules = SimpleNamespace(analyze=lambda x: {})
    engine.context = SimpleNamespace(analyze=lambda: {})
    engine.speaker = lambda *args: {"status": "UNAVAILABLE"}
    engine.fusion = SimpleNamespace(build=lambda **kwargs: {})
    engine.risk = SimpleNamespace(score=lambda x: {"risk_score": 1, "regressor_status": "BOOTSTRAP_UNTRAINED"})
    audio = np.zeros(64000, dtype=np.float32)
    try:
        cache = {}
        engine.analyze(audio, text_cache=cache)
        engine.analyze(audio, text_cache=cache)
        assert calls == {"minilm": 1, "qwen": 1}
        engine.analyze(audio, text_cache={})
        assert calls == {"minilm": 2, "qwen": 2}
    finally:
        engine.pool.shutdown()
