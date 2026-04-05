from __future__ import annotations

from typing import Generic, TypeVar

import requests


TAction = TypeVar("TAction")
TObservation = TypeVar("TObservation")
TState = TypeVar("TState")


class EnvClient(Generic[TAction, TObservation, TState]):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def reset(self, **payload):
        response = requests.post(f"{self.base_url}/reset", json=payload, timeout=30)
        response.raise_for_status()
        return self._parse_result({"observation": response.json(), "reward": response.json().get("reward", 0.0), "done": response.json().get("done", False)}).observation

    def step(self, action: TAction):
        response = requests.post(f"{self.base_url}/step", json={"action": self._step_payload(action)}, timeout=30)
        response.raise_for_status()
        return self._parse_result(response.json())

    def state(self) -> TState:
        response = requests.get(f"{self.base_url}/state", timeout=30)
        response.raise_for_status()
        return self._parse_state(response.json())

    def _step_payload(self, action: TAction) -> dict:
        raise NotImplementedError

    def _parse_result(self, payload: dict):
        raise NotImplementedError

    def _parse_state(self, payload: dict) -> TState:
        raise NotImplementedError

