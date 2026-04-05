from __future__ import annotations

from typing import Any, Protocol


class Environment(Protocol):
    def reset(self, seed: int | None = None, episode_id: str | None = None, task_id: str | None = None, **kwargs: Any):
        ...

    def step(self, action):
        ...

    @property
    def state(self):
        ...

