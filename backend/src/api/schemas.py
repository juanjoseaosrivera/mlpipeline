"""Wire schemas for the inference API.

Mirrored on the frontend in `frontend/src/app/models/`. When one moves the
other moves in the same PR.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_1: float
    feature_2: float
    category: int = Field(ge=0)


class PredictResponse(BaseModel):
    prediction: int
    probability: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)
    model_version: str
