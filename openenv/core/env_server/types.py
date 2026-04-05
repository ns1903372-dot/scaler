from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Action(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    done: bool = False
    reward: float = Field(0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class State(BaseModel):
    episode_id: str
    step_count: int = 0
