from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .base import Contract, Identifier, NonNegative, UnitScore, Version
from .status import ModuleStatus


class TranscriptSegment(Contract):
    start_ms: NonNegative
    end_ms: NonNegative
    text: str = Field(max_length=8000)

    @model_validator(mode="after")
    def check(self):
        if self.end_ms < self.start_ms:
            raise ValueError("Invalid transcript timestamps")
        return self


class TranscriptEvent(Contract):
    type: Literal["transcript"] = "transcript"
    call_id: Identifier
    text: str = Field(max_length=32000)
    language: str | None
    segments: list[TranscriptSegment]
    quality: UnitScore | None
    status: ModuleStatus
    model_version: Version | None
    latency_ms: NonNegative
    timestamp: AwareDatetime
    analysis_english: str | None = Field(default=None, max_length=32000)
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check(self):
        if self.status in (ModuleStatus.ERROR, ModuleStatus.UNAVAILABLE) and (
            self.text or self.segments or self.analysis_english
        ):
            raise ValueError("Unavailable transcript must not invent text")
        return self
