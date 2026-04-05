from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from retail_ops_env.models import RetailOpsAction, RetailOpsObservation, RetailOpsState


class RetailOpsEnv(EnvClient[RetailOpsAction, RetailOpsObservation, RetailOpsState]):
    def _step_payload(self, action: RetailOpsAction) -> dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict) -> StepResult[RetailOpsObservation]:
        observation_payload = payload.get("observation", payload)
        observation = RetailOpsObservation.model_validate(observation_payload)
        return StepResult(
            observation=observation,
            reward=payload.get("reward", observation.reward),
            done=payload.get("done", observation.done),
        )

    def _parse_state(self, payload: dict) -> RetailOpsState:
        return RetailOpsState.model_validate(payload)

