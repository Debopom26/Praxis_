import base64
import importlib.metadata
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from math import gcd
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from scipy.signal import resample_poly

from praxis.contracts import AudioFrame, AudioQuality, AudioWindow, SpeechSpan


class Vad(Protocol):
    version: str

    def speech(self, samples: np.ndarray) -> bool: ...


class SileroVad:
    def __init__(self):
        import torch
        from silero_vad import load_silero_vad

        self.torch = torch
        self.model = load_silero_vad()
        self.model.reset_states()
        self.version = "silero-vad-" + importlib.metadata.version("silero-vad")

    def speech(self, samples: np.ndarray) -> bool:
        with self.torch.inference_mode():
            return float(self.model(self.torch.from_numpy(samples.copy()), 16000).item()) >= 0.5


def mono(frame: AudioFrame) -> np.ndarray:
    raw = base64.b64decode(frame.audio_base64, validate=True)
    return (
        np.frombuffer(raw, dtype="<i2")
        .reshape(-1, frame.format.channels)
        .astype(np.float32)
        .mean(axis=1)
        / 32768.0
    )


def quality(samples: np.ndarray, sample_rate: int) -> AudioQuality:
    if samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
        raise ValueError("Finite nonempty mono audio required")
    clipping = float(np.mean(np.abs(samples) >= 0.999))
    silence = float(np.mean(np.abs(samples) < 1e-4))
    size = max(1, int(sample_rate * 0.02))
    powers = np.array(
        [
            np.mean(v.astype(np.float64) ** 2)
            for v in np.array_split(samples, max(1, len(samples) // size))
        ]
    )
    low, high = np.percentile(powers, [10, 90])
    proxy = float(10 * np.log10(high / low)) if low > 1e-12 and high > low else None
    reasons = []
    if clipping > 0.01:
        reasons.append("CLIPPING")
    if silence > 0.8:
        reasons.append("MOSTLY_SILENT")
    return AudioQuality(
        clipping_ratio=clipping,
        silence_ratio=silence,
        snr_proxy_db=proxy,
        duration_ms=len(samples) * 1000 / sample_rate,
        completeness=1,
        reason_codes=reasons,
    )


@dataclass
class Window:
    contract: AudioWindow
    samples: np.ndarray


class SpeechWindows:
    """Bounded speech queue; source-time spans preserve removed silence."""

    def __init__(self, call_id: str, sample_rate: int, channels: int, vad_version: str):
        self.call_id = call_id
        self.rate = sample_rate
        self.channels = channels
        self.version = vad_version
        self.parts: deque[tuple[np.ndarray, float]] = deque()
        self.count = 0
        self.sequence = 0

    def add(self, samples: np.ndarray, start_ms: float) -> list[Window]:
        if len(samples) > self.rate:
            raise ValueError("Speech chunk exceeds one second")
        self.parts.append((samples.copy(), start_ms))
        self.count += len(samples)
        outputs = []
        while self.count >= self.rate * 4:
            needed = self.rate * 4
            arrays = []
            spans = []
            for values, start in self.parts:
                take = min(needed, len(values))
                arrays.append(values[:take])
                spans.append(SpeechSpan(start_ms=start, end_ms=start + take * 1000 / self.rate))
                needed -= take
                if needed == 0:
                    break
            wave = np.concatenate(arrays)
            # Source bounds survive reconnects; IDs stay bounded for long call identifiers.
            wid = str(
                uuid5(
                    NAMESPACE_URL,
                    f"praxis:{self.call_id}:{self.rate}:{[(s.start_ms, s.end_ms) for s in spans]}",
                )
            )
            contract = AudioWindow(
                call_id=self.call_id,
                window_id=wid,
                sequence_id=self.sequence,
                start_ms=spans[0].start_ms,
                end_ms=spans[-1].end_ms,
                audio_reference=wid,
                original_sample_rate=self.rate,
                original_channels=self.channels,
                analysis_sample_rate=self.rate,
                speech_spans=spans,
                vad_model_version=self.version,
                quality=quality(wave, self.rate),
                timestamp=datetime.now(timezone.utc),
            )
            outputs.append(Window(contract, wave))
            self.sequence += 1
            remove = self.rate * 2
            while remove:
                values, start = self.parts.popleft()
                take = min(remove, len(values))
                remove -= take
                self.count -= take
                if take < len(values):
                    self.parts.appendleft((values[take:], start + take * 1000 / self.rate))
        return outputs

    def clear(self):
        self.parts.clear()
        self.count = 0


class AudioPipeline:
    def __init__(self, call_id: str, vad: Vad | None = None):
        self.call_id = call_id
        self.vad = vad or SileroVad()
        self.rate = 0
        self.channels = 0
        self.input = np.empty(0, np.float32)
        self.native = np.empty(0, np.float32)
        self.side = np.empty(0, np.float32)
        self.vad_samples = 0
        self.native_samples = 0
        self.received = 0
        self.start_ms = 0.0
        self.windows: SpeechWindows | None = None

    def push(self, frame: AudioFrame) -> list[Window]:
        if not self.rate:
            self.rate = frame.format.sample_rate
            self.channels = frame.format.channels
            self.start_ms = frame.timestamp_ms
            self.windows = SpeechWindows(self.call_id, self.rate, self.channels, self.vad.version)
        if (self.rate, self.channels) != (frame.format.sample_rate, frame.format.channels):
            raise ValueError("FORMAT_CHANGED_RECONNECT_REQUIRED")
        expected = self.start_ms + self.received * 1000 / self.rate
        if abs(frame.timestamp_ms - expected) > 2:
            raise ValueError("AUDIO_TIMESTAMP_GAP")
        wave = mono(frame)
        self.received += len(wave)
        self.input = np.concatenate((self.input, wave))
        outputs = []
        while len(self.input) >= self.rate:
            block = self.input[: self.rate]
            self.input = self.input[self.rate :]
            divisor = gcd(self.rate, 16000)
            side = resample_poly(block, 16000 // divisor, self.rate // divisor).astype(np.float32)
            self.native = np.concatenate((self.native, block))
            self.side = np.concatenate((self.side, side))
            while len(self.side) >= 512:
                step = self.side[:512]
                self.side = self.side[512:]
                new_native = round((self.vad_samples + 512) * self.rate / 16000)
                count = new_native - self.native_samples
                chunk = self.native[:count]
                self.native = self.native[count:]
                if self.vad.speech(step):
                    if self.windows is None:
                        raise RuntimeError("Audio window scheduler is not initialized")
                    outputs.extend(
                        self.windows.add(
                            chunk, self.start_ms + self.native_samples * 1000 / self.rate
                        )
                    )
                self.native_samples = new_native
                self.vad_samples += 512
        return outputs

    def close(self):
        self.input = np.empty(0, np.float32)
        self.native = np.empty(0, np.float32)
        self.side = np.empty(0, np.float32)
        if self.windows is not None:
            self.windows.clear()
