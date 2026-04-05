from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from openenv.core.env_server.types import Action, Observation, State


Command = Literal[
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


class RetailOpsAction(Action):
    command: Command = Field(..., description="The operation the agent wants to execute.")
    order_id: str | None = Field(default=None, description="Order identifier when the action targets an order.")
    reference_id: str | None = Field(default=None, description="Policy id, SKU, or other reference identifier.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured parameters for the selected command.")
    rationale: str | None = Field(default=None, description="Optional reasoning for auditability and debugging.")


class RetailOpsObservation(Observation):
    summary: str = Field(..., description="Short summary of what changed after the action.")
    visible_case: dict[str, Any] = Field(default_factory=dict, description="Revealed task information and current workspace state.")
    last_action_success: bool = Field(..., description="Whether the last action was accepted and applied.")
    last_action_message: str = Field(..., description="Detailed feedback for the last action.")
    available_commands: list[str] = Field(default_factory=list, description="Commands that can be executed next.")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Current cumulative task score.")
    score_breakdown: dict[str, float] = Field(default_factory=dict, description="Progress on grading milestones.")


class RetailOpsState(State):
    task_id: str = Field(..., description="Current task identifier.")
    difficulty: str = Field(..., description="Task difficulty band.")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Current cumulative score.")
    remaining_steps: int = Field(..., ge=0, description="Remaining action budget.")
    resolution_status: str = Field(..., description="One of active, resolved, escalated, timeout.")
    revealed_entities: dict[str, list[str]] = Field(default_factory=dict, description="Case entities the agent has inspected.")
    completed_milestones: dict[str, float] = Field(default_factory=dict, description="Grader milestone progress.")
    action_history: list[dict[str, Any]] = Field(default_factory=list, description="Structured action audit log.")
