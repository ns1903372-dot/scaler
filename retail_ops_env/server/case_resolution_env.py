from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

from retail_ops_env.graders import grade_task
from retail_ops_env.models import RetailOpsAction, RetailOpsObservation, RetailOpsState
from retail_ops_env.tasks import TASKS, get_task


class RetailOpsEnvironment(Environment):
    def __init__(self) -> None:
        self._task_pointer = 0
        self._task = get_task(TASKS[0]["id"])
        self._workspace: dict[str, Any] = {}
        self._state = self._new_state(self._task, episode_id=str(uuid4()))
        self._initialize_workspace()

    def _new_state(self, task: dict[str, Any], episode_id: str) -> RetailOpsState:
        return RetailOpsState(
            episode_id=episode_id,
            step_count=0,
            task_id=task["id"],
            difficulty=task["difficulty"],
            score=0.0,
            remaining_steps=task["max_steps"],
            resolution_status="active",
            revealed_entities={"orders": [], "policies": [], "inventory": []},
            completed_milestones={},
            action_history=[],
        )

    def _initialize_workspace(self) -> None:
        self._workspace = {
            "revealed": {"orders": set(), "policies": set(), "inventory": set()},
            "address_updates": {},
            "refunds": [],
            "replacements": [],
            "messages": [],
            "notes": [],
            "resolution": {"status": "active", "summary": "", "resolution_code": ""},
            "escalated": False,
        }

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        **kwargs: Any,
    ) -> RetailOpsObservation:
        if task_id is None:
            task_id = TASKS[self._task_pointer % len(TASKS)]["id"]
            self._task_pointer += 1

        self._task = get_task(task_id)
        self._initialize_workspace()
        self._state = self._new_state(self._task, episode_id=episode_id or str(uuid4()))

        score, breakdown = grade_task(self._task, self._workspace)
        self._state.score = score
        self._state.completed_milestones = breakdown

        return RetailOpsObservation(
            summary=f"Loaded task {self._task['id']}",
            visible_case=self._build_visible_case(),
            last_action_success=True,
            last_action_message="Environment ready.",
            available_commands=self._available_commands(),
            score=score,
            score_breakdown=breakdown,
            done=False,
            reward=score,
            metadata={"task_title": self._task["title"], "instruction": self._task["instruction"]},
        )

    def step(self, action: RetailOpsAction) -> RetailOpsObservation:
        if self._state.resolution_status != "active":
            return self._observation(False, "Episode already finished.", done=True)

        self._state.step_count += 1
        success, message = self._apply_action(action)

        score, breakdown = grade_task(self._task, self._workspace)
        self._state.score = score
        self._state.remaining_steps = max(0, self._task["max_steps"] - self._state.step_count)
        self._state.completed_milestones = breakdown
        self._state.revealed_entities = {
            key: sorted(value) for key, value in self._workspace["revealed"].items()
        }
        self._state.action_history.append(
            {
                "step": self._state.step_count,
                "command": action.command,
                "order_id": action.order_id,
                "reference_id": action.reference_id,
                "payload": deepcopy(action.payload),
                "success": success,
            }
        )

        done = self._workspace["resolution"]["status"] in {"resolved", "escalated"}
        if not done and self._state.step_count >= self._task["max_steps"]:
            self._state.resolution_status = "timeout"
            self._workspace["resolution"]["status"] = "timeout"
            done = True
            message = f"{message} Step budget exhausted."

        if done and self._state.resolution_status == "active":
            self._state.resolution_status = self._workspace["resolution"]["status"]

        return self._observation(success, message, done=done)

    @property
    def state(self) -> RetailOpsState:
        return self._state

    def _observation(self, success: bool, message: str, done: bool) -> RetailOpsObservation:
        score, breakdown = grade_task(self._task, self._workspace)
        self._state.score = score
        self._state.completed_milestones = breakdown
        return RetailOpsObservation(
            summary=self._task["title"],
            visible_case=self._build_visible_case(),
            last_action_success=success,
            last_action_message=message,
            available_commands=self._available_commands(),
            score=score,
            score_breakdown=breakdown,
            done=done,
            reward=score,
            metadata={"task_id": self._task["id"], "resolution_status": self._workspace["resolution"]["status"]},
        )

    def _build_visible_case(self) -> dict[str, Any]:
        return {
            "task_id": self._task["id"],
            "difficulty": self._task["difficulty"],
            "title": self._task["title"],
            "instruction": self._task["instruction"],
            "case": deepcopy(self._task["case"]),
            "catalog": {
                "order_ids": sorted(self._task["orders"].keys()),
                "policy_ids": sorted(self._task["policies"].keys()),
                "inventory_skus": sorted(self._task["inventory"].keys()),
            },
            "revealed_orders": {
                order_id: deepcopy(self._task["orders"][order_id])
                for order_id in sorted(self._workspace["revealed"]["orders"])
            },
            "revealed_policies": {
                policy_id: deepcopy(self._task["policies"][policy_id])
                for policy_id in sorted(self._workspace["revealed"]["policies"])
            },
            "revealed_inventory": {
                sku: deepcopy(self._task["inventory"][sku])
                for sku in sorted(self._workspace["revealed"]["inventory"])
            },
            "workspace": {
                "address_updates": deepcopy(self._workspace["address_updates"]),
                "refunds": deepcopy(self._workspace["refunds"]),
                "replacements": deepcopy(self._workspace["replacements"]),
                "messages": deepcopy(self._workspace["messages"]),
                "notes": deepcopy(self._workspace["notes"]),
                "resolution": deepcopy(self._workspace["resolution"]),
                "escalated": self._workspace["escalated"],
            },
        }

    def _available_commands(self) -> list[str]:
        return [
            "inspect_case",
            "inspect_order",
            "inspect_policy",
            "inspect_inventory",
            "update_shipping_address",
            "issue_refund",
            "create_replacement",
            "send_message",
            "add_internal_note",
            "resolve_case",
            "escalate_case",
        ]

    def _apply_action(self, action: RetailOpsAction) -> tuple[bool, str]:
        if action.command == "inspect_case":
            return True, f"Case {self._task['case']['case_id']} reviewed."
        if action.command == "inspect_order":
            return self._inspect_order(action.order_id)
        if action.command == "inspect_policy":
            return self._inspect_policy(action.reference_id)
        if action.command == "inspect_inventory":
            return self._inspect_inventory(action.reference_id)
        if action.command == "update_shipping_address":
            return self._update_shipping_address(action.order_id, action.payload)
        if action.command == "issue_refund":
            return self._issue_refund(action.order_id, action.payload)
        if action.command == "create_replacement":
            return self._create_replacement(action.order_id, action.payload)
        if action.command == "send_message":
            return self._send_message(action.payload)
        if action.command == "add_internal_note":
            return self._add_internal_note(action.payload)
        if action.command == "resolve_case":
            return self._resolve_case(action.payload)
        if action.command == "escalate_case":
            return self._escalate_case(action.payload)
        return False, f"Unsupported command: {action.command}"

    def _inspect_order(self, order_id: str | None) -> tuple[bool, str]:
        if not order_id or order_id not in self._task["orders"]:
            return False, "Unknown order id."
        self._workspace["revealed"]["orders"].add(order_id)
        return True, f"Order {order_id} revealed."

    def _inspect_policy(self, policy_id: str | None) -> tuple[bool, str]:
        if not policy_id or policy_id not in self._task["policies"]:
            return False, "Unknown policy id."
        self._workspace["revealed"]["policies"].add(policy_id)
        return True, f"Policy {policy_id} revealed."

    def _inspect_inventory(self, sku: str | None) -> tuple[bool, str]:
        if not sku or sku not in self._task["inventory"]:
            return False, "Unknown inventory SKU."
        self._workspace["revealed"]["inventory"].add(sku)
        return True, f"Inventory for {sku} revealed."

    def _update_shipping_address(self, order_id: str | None, payload: dict[str, Any]) -> tuple[bool, str]:
        if self._task["id"] != "easy_address_fix":
            return False, "Address changes are not relevant for this case."
        if order_id != "ORD-1001":
            return False, "This case only allows address changes on ORD-1001."
        self._workspace["address_updates"][order_id] = {
            "line1": payload.get("line1"),
            "apartment": payload.get("apartment"),
            "city": payload.get("city"),
            "postal_code": payload.get("postal_code"),
        }
        return True, "Shipping address updated in the order workspace."

    def _issue_refund(self, order_id: str | None, payload: dict[str, Any]) -> tuple[bool, str]:
        if not order_id or order_id not in self._task["orders"]:
            return False, "Refund target order is invalid."
        amount = float(payload.get("amount", 0.0))
        self._workspace["refunds"].append(
            {
                "order_id": order_id,
                "amount": amount,
                "reason": payload.get("reason", ""),
                "method": payload.get("method", "original_payment"),
            }
        )
        return True, f"Refund of {amount:.2f} recorded for {order_id}."

    def _create_replacement(self, order_id: str | None, payload: dict[str, Any]) -> tuple[bool, str]:
        if not order_id or order_id not in self._task["orders"]:
            return False, "Replacement target order is invalid."
        self._workspace["replacements"].append(
            {
                "order_id": order_id,
                "sku": payload.get("sku"),
                "warehouse": payload.get("warehouse"),
                "shipping_speed": payload.get("shipping_speed", "standard"),
                "waive_return": bool(payload.get("waive_return", False)),
            }
        )
        return True, f"Replacement recorded for {order_id}."

    def _send_message(self, payload: dict[str, Any]) -> tuple[bool, str]:
        message = str(payload.get("message", "")).strip()
        if not message:
            return False, "Customer message cannot be empty."
        self._workspace["messages"].append({"message": message})
        return True, "Customer message queued."

    def _add_internal_note(self, payload: dict[str, Any]) -> tuple[bool, str]:
        note = str(payload.get("note", "")).strip()
        if not note:
            return False, "Internal note cannot be empty."
        self._workspace["notes"].append({"note": note})
        return True, "Internal note saved."

    def _resolve_case(self, payload: dict[str, Any]) -> tuple[bool, str]:
        self._workspace["resolution"] = {
            "status": "resolved",
            "summary": str(payload.get("summary", "")),
            "resolution_code": str(payload.get("resolution_code", "")),
        }
        self._state.resolution_status = "resolved"
        return True, "Case marked as resolved."

    def _escalate_case(self, payload: dict[str, Any]) -> tuple[bool, str]:
        self._workspace["escalated"] = True
        self._workspace["resolution"] = {
            "status": "escalated",
            "summary": str(payload.get("reason", "")),
            "resolution_code": str(payload.get("team", "escalation")),
        }
        self._state.resolution_status = "escalated"
        return True, "Case escalated."
