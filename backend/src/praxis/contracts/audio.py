import base64
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .base import Contract, Identifier, NonNegative, UnitScore


class AudioFormat(Contract):
    encoding: Literal["pcm_s16le"] = "pcm_s16le"
    sample_rate: Literal[8000, 16000, 24000, 32000, 44100, 48000]
    channels: int = Field(ge=1, le=2)


class AudioFrame(Contract):
    type: Literal["audio"] = "audio"
    sequence_id: int = Field(ge=0, le=9007199254740991)
    timestamp_ms: int = Field(ge=0, le=9007199254740991)
    format: AudioFormat
    audio_base64: str = Field(min_length=4, max_length=256000)

    @model_validator(mode="after")
    def check(self):
        data = base64.b64decode(self.audio_base64, validate=True)
        stride = 2 * self.format.channels
        if not data or len(data) % stride or len(data) > self.format.sample_rate * stride:
            raise ValueError("PCM must be aligned, nonempty and at most one second")
        return self


class AudioQuality(Contract):
    clipping_ratio: UnitScore
    silence_ratio: UnitScore
    snr_proxy_db: float | None
    duration_ms: NonNegative
    completeness: UnitScore
    reason_codes: list[str] = Field(default_factory=list)


class SpeechSpan(Contract):
    start_ms: NonNegative
    end_ms: NonNegative

    @model_validator(mode="after")
    def check(self):
        if self.end_ms <= self.start_ms:
            raise ValueError("Positive speech span required")
        return self


class AudioWindow(Contract):
    type: Literal["audio_window"] = "audio_window"
    call_id: Identifier
    window_id: Identifier
    sequence_id: int = Field(ge=0)
    start_ms: NonNegative
    end_ms: NonNegative
    audio_reference: Identifier
    original_sample_rate: int = Field(ge=8000, le=48000)
    original_channels: int = Field(ge=1, le=2)
    analysis_sample_rate: int = Field(ge=8000, le=48000)
    speech_spans: list[SpeechSpan] = Field(min_length=1)
    vad_model_version: str
    quality: AudioQuality
    timestamp: AwareDatetime

    @model_validator(mode="after")
    def check(self):
        if self.end_ms <= self.start_ms:
            raise ValueError("Invalid window time range")
        if (
            self.speech_spans[0].start_ms != self.start_ms
            or self.speech_spans[-1].end_ms != self.end_ms
        ):
            raise ValueError("Spans must cover window source time range")
        if any(b.start_ms < a.end_ms for a, b in zip(self.speech_spans, self.speech_spans[1:])):
            raise ValueError("Speech spans must be ordered and nonoverlapping")
        return self
