from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


TObservation = TypeVar("TObservation")


@dataclass
class StepResult(Generic[TObservation]):
    observation: TObservation
    reward: float
    done: bool

