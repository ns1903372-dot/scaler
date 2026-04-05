from __future__ import annotations

import traceback
from typing import Any, Type

from fastapi import Body, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def create_app(env_cls: Type, action_model: Type[BaseModel], observation_model: Type[BaseModel], env_name: str = "openenv") -> FastAPI:
    app = FastAPI(title=env_name)
    env = env_cls()
    last_error: dict[str, Any] = {}

    @app.get("/api")
    def root() -> dict[str, str]:
        return {"name": env_name, "status": "ok"}

    @app.post("/reset")
    def reset(body: dict[str, Any] | None = Body(default=None)):
        nonlocal last_error
        try:
            body = body or {}
            last_error = {}
            observation = env.reset(
                seed=body.get("seed"),
                episode_id=body.get("episode_id"),
                task_id=body.get("task_id"),
                **body.get("metadata", {}),
            )
            return JSONResponse(status_code=200, content=jsonable_encoder(observation))
        except Exception as exc:  # noqa: BLE001
            last_error = {
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "reset_body": body or {},
            }
            return JSONResponse(status_code=500, content=last_error)

    @app.post("/step")
    def step(body: dict[str, Any] = Body(...)):
        nonlocal last_error
        try:
            action = action_model.model_validate(body.get("action", {}))
            observation = env.step(action)
            last_error = {}
            payload = {
                "observation": jsonable_encoder(observation),
                "reward": float(observation.reward),
                "done": bool(observation.done),
            }
            return JSONResponse(status_code=200, content=payload)
        except Exception as exc:  # noqa: BLE001
            last_error = {
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "action": body.get("action", {}),
            }
            return JSONResponse(
                status_code=500,
                content=last_error,
            )

    @app.get("/last-error")
    def get_last_error():
        return last_error

    @app.get("/state")
    def state():
        return env.state.model_dump()

    return app
