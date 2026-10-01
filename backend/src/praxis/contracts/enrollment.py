import base64

from pydantic import Field, StrictBool, field_validator

from .base import Contract, Identifier


class EnrollmentRequest(Contract):
    session_id: Identifier
    identity: Identifier
    approved: StrictBool
    clips_base64: list[str] = Field(min_length=3, max_length=10)

    @field_validator("clips_base64")
    @classmethod
    def clips(cls, values):
        for value in values:
            if not 4 <= len(value) <= 8 * 1024 * 1024:
                raise ValueError("Enrollment clip size invalid")
            base64.b64decode(value, validate=True)
        return values
