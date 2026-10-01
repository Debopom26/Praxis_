from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1.0.0"
Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:@-]+$")]
Version = Annotated[str, Field(min_length=1, max_length=128)]
UnitScore = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
RiskScore = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_assignment=True)
