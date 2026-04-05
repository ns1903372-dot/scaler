from __future__ import annotations

import traceback
from typing import Any, Type

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def create_app(env_cls: Type, action_model: Type[BaseModel], observation_model: Type[BaseModel], env_name: str = "openenv") -> FastAPI:
    app = FastAPI(title=env_name)
    env = env_cls()

    class StepBody(BaseModel):
        action: action_model

    class ResetBody(BaseModel):
        seed: int | None = None
        episode_id: str | None = None
        task_id: str | None = None
        metadata: dict[str, Any] = {}

    @app.get("/api")
    def root() -> dict[str, str]:
        return {"name": env_name, "status": "ok"}

    @app.post("/reset", response_model=observation_model)
    def reset(body: ResetBody | None = Body(default=None)):
        body = body or ResetBody()
        return env.reset(
            seed=body.seed,
            episode_id=body.episode_id,
            task_id=body.task_id,
            **body.metadata,
        )

    @app.post("/step")
    def step(body: StepBody = Body(...)):
        try:
            observation = env.step(body.action)
            return {
                "observation": observation.model_dump(),
                "reward": observation.reward,
                "done": observation.done,
            }
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )

    @app.get("/state")
    def state():
        return env.state.model_dump()

    return app
