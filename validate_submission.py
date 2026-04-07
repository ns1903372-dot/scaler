from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from retail_ops_env.graders import grade_task
from retail_ops_env.models import RetailOpsAction
from retail_ops_env.server.case_resolution_env import RetailOpsEnvironment
from retail_ops_env.tasks import TASKS


ROOT = Path(__file__).resolve().parent


def in_open_unit_interval(value: float) -> bool:
    return 0.0 < float(value) < 1.0


def check_files() -> None:
    required = [
        ROOT / "openenv.yaml",
        ROOT / "Dockerfile",
        ROOT / "server" / "Dockerfile",
        ROOT / "inference.py",
        ROOT / "README.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")


def check_manifest() -> None:
    manifest = yaml.safe_load((ROOT / "openenv.yaml").read_text(encoding="utf-8"))
    required_keys = {"spec_version", "name", "type", "runtime", "app", "port"}
    if not required_keys.issubset(manifest):
        raise SystemExit(f"openenv.yaml missing keys: {sorted(required_keys - set(manifest))}")


def check_imports() -> None:
    importlib.import_module("server.app")
    importlib.import_module("retail_ops_env.client")
    importlib.import_module("retail_ops_env.models")


def check_required_env_vars() -> None:
    required = ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {missing}")


def check_http_endpoints() -> None:
    server_app = importlib.import_module("server.app")
    app = server_app.app
    client = TestClient(app)

    health = client.get("/health")
    if health.status_code != 200:
        raise SystemExit(f"/health returned {health.status_code}")

    reset_payload = {"task_id": TASKS[0]["id"]}
    reset_response = client.post("/reset", json=reset_payload)
    if reset_response.status_code != 200:
        raise SystemExit(f"/reset returned {reset_response.status_code}")

    reset_json = reset_response.json()
    if reset_json.get("visible_case", {}).get("task_id") != TASKS[0]["id"]:
        raise SystemExit("/reset did not return the requested task payload")

    step_payload = {
        "action": {
            "command": "inspect_case",
            "payload": {},
        }
    }
    step_response = client.post("/step", json=step_payload)
    if step_response.status_code != 200:
        raise SystemExit(f"/step returned {step_response.status_code}")

    step_json = step_response.json()
    observation = step_json.get("observation", {})
    if "reward" not in step_json or "done" not in step_json or not observation:
        raise SystemExit("/step did not return the expected OpenEnv wrapper payload")

    state_response = client.get("/state")
    if state_response.status_code != 200:
        raise SystemExit(f"/state returned {state_response.status_code}")

    state_json = state_response.json()
    if not reset_json or not state_json:
        raise SystemExit("HTTP endpoints returned empty payloads")
    if state_json.get("task_id") != TASKS[0]["id"]:
        raise SystemExit("/state did not return the active task id")


def check_environment_logic() -> None:
    env = RetailOpsEnvironment()
    for task in TASKS:
        reset_obs = env.reset(task_id=task["id"])
        if not in_open_unit_interval(reset_obs.score):
            raise SystemExit(f"Reset score must be strictly between 0 and 1 for {task['id']}")
        inspection = env.step(RetailOpsAction(command="inspect_case"))
        if not in_open_unit_interval(inspection.score):
            raise SystemExit(f"Step score must be strictly between 0 and 1 for {task['id']}")
        state = env.state
        score, breakdown = grade_task(task, env._workspace)  # noqa: SLF001 - local validator only
        if not in_open_unit_interval(score):
            raise SystemExit(f"Grader score must be strictly between 0 and 1 for {task['id']}")
        if state.task_id != task["id"]:
            raise SystemExit(f"State task mismatch for {task['id']}")
        print(json.dumps({"task_id": task["id"], "score": score, "breakdown": breakdown}, sort_keys=True))


def main() -> None:
    check_files()
    check_manifest()
    check_imports()
    check_required_env_vars()
    check_http_endpoints()
    check_environment_logic()
    print("VALIDATION_OK")


if __name__ == "__main__":
    main()
