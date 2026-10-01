import base64

import numpy as np
import pytest
from praxis.audio.decode import decode_clip
from praxis.audio.pipeline import AudioPipeline, SileroVad, SpeechWindows, quality
from praxis.contracts import AudioFrame


class TestVad:
    __test__ = False
    version = "TEST_ONLY"

    def speech(self, samples):
        return bool(np.any(samples))


def frame(sequence, rate=16000, silent=False):
    data = np.zeros(rate, dtype="<i2") if silent else np.full(rate, 1000, dtype="<i2")
    return AudioFrame(
        sequence_id=sequence,
        timestamp_ms=sequence * 1000,
        format={"sample_rate": rate, "channels": 1},
        audio_base64=base64.b64encode(data.tobytes()).decode(),
    )


@pytest.mark.parametrize("rate", [8000, 16000, 44100, 48000])
def test_windows_overlap_exact_and_bounded(rate):
    pipeline = AudioPipeline("call", TestVad())
    windows = []
    for n in range(30):
        windows += pipeline.push(frame(n, rate))
        assert len(pipeline.input) < rate and len(pipeline.native) < rate
        assert pipeline.windows.count < 4 * rate
    assert len(windows) == 13  # final VAD block remainder remains transient, not padded
    for a, b in zip(windows, windows[1:]):
        assert len(a.samples) == 4 * rate
        assert b.contract.start_ms == pytest.approx(a.contract.start_ms + 2000)
        np.testing.assert_array_equal(a.samples[2 * rate :], b.samples[: 2 * rate])
    pipeline.close()
    assert pipeline.windows.count == 0


def test_silence_and_short_speech_do_not_force_window():
    pipeline = AudioPipeline("c", TestVad())
    assert pipeline.push(frame(0)) == []
    for n in range(1, 10):
        assert pipeline.push(frame(n, silent=True)) == []


def test_gaps_keep_source_timestamps():
    scheduler = SpeechWindows("c", 16000, 1, "TEST_ONLY")
    results = []
    for start in [0, 1000, 7000, 8000]:
        results += scheduler.add(np.ones(16000, np.float32), start)
    assert len(results) == 1
    assert results[0].contract.end_ms == 9000
    assert results[0].contract.quality.duration_ms == 4000


def test_malformed_and_quality():
    for bad in [b"", b"not audio"]:
        with pytest.raises(ValueError):
            decode_clip(bad)
    assert quality(np.zeros(16000), 16000).silence_ratio == 1
    assert quality(np.ones(16000), 16000).clipping_ratio == 1


def test_real_silero_rejects_silence():
    vad = SileroVad()
    assert not vad.speech(np.zeros(512, np.float32))


def test_window_ids_survive_reconnect_with_long_call_id():
    def window(start):
        scheduler = SpeechWindows("c" * 128, 16000, 1, "TEST_ONLY")
        result = []
        for n in range(4):
            result += scheduler.add(np.ones(16000, np.float32), start + n * 1000)
        return result[0].contract.window_id

    assert window(0) != window(10000)
    assert window(0) == window(0)
    assert len(window(0)) <= 128
