from typing import Literal

from pydantic import Field

from .base import Contract, Identifier


class ConnectionEvent(Contract):
    type: Literal["connection"] = "connection"
    status: Literal["AVAILABLE"] = "AVAILABLE"
    session_id: Identifier
    contract_version: str
    last_sequence_id: int = Field(ge=-1, le=9007199254740991)
    last_timestamp_ms: int = Field(ge=-1, le=9007199254740991)
    reason_codes: list[str]


class AckEvent(Contract):
    type: Literal["ack"] = "ack"
    sequence_id: int = Field(ge=0, le=9007199254740991)


class AnalysisGapEvent(Contract):
    type: Literal["analysis_gap"] = "analysis_gap"
    reason_codes: list[str]
