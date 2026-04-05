from __future__ import annotations

from typing import Any


def _has_message(messages: list[dict[str, Any]], *phrases: str) -> bool:
    lowered = [msg.get("message", "").lower() for msg in messages]
    return any(all(phrase.lower() in text for phrase in phrases) for text in lowered)


def _find_refund(refunds: list[dict[str, Any]], order_id: str, amount: float) -> bool:
    for refund in refunds:
        if refund.get("order_id") == order_id and abs(float(refund.get("amount", 0.0)) - amount) < 1e-6:
            return True
    return False


def _find_replacement(
    replacements: list[dict[str, Any]],
    order_id: str,
    sku: str,
    warehouse: str,
    shipping_speed: str | None = None,
    waive_return: bool | None = None,
) -> bool:
    for replacement in replacements:
        if replacement.get("order_id") != order_id:
            continue
        if replacement.get("sku") != sku or replacement.get("warehouse") != warehouse:
            continue
        if shipping_speed is not None and replacement.get("shipping_speed") != shipping_speed:
            continue
        if waive_return is not None and bool(replacement.get("waive_return")) is not waive_return:
            continue
        return True
    return False


def grade_task(task: dict[str, Any], workspace: dict[str, Any]) -> tuple[float, dict[str, float]]:
    task_id = task["id"]
    if task_id == "easy_address_fix":
        return _grade_easy(task, workspace)
    if task_id == "medium_damaged_item":
        return _grade_medium(task, workspace)
    if task_id == "hard_vip_exchange_and_refund":
        return _grade_hard(task, workspace)
    return 0.0, {"unrecognized_task": 0.0}


def _grade_easy(task: dict[str, Any], workspace: dict[str, Any]) -> tuple[float, dict[str, float]]:
    revealed = workspace["revealed"]
    updates = workspace["address_updates"]
    messages = workspace["messages"]
    resolution = workspace["resolution"]
    order = task["orders"]["ORD-1001"]
    wanted = order["requested_address"]

    breakdown = {
        "diagnosis": 0.15 if "ORD-1001" in revealed["orders"] else 0.0,
        "operational_execution": 0.45
        if updates.get("ORD-1001", {}).get("apartment") == wanted["apartment"]
        else 0.0,
        "customer_communication": 0.15
        if _has_message(messages, "apt 5") or _has_message(messages, "apartment 5")
        else 0.0,
        "final_resolution": 0.25
        if resolution.get("status") == "resolved" and "address" in resolution.get("summary", "").lower()
        else 0.0,
    }

    if workspace["refunds"] or workspace["replacements"] or workspace["escalated"]:
        breakdown["final_resolution"] = max(0.0, breakdown["final_resolution"] - 0.1)

    score = max(0.0, min(1.0, round(sum(breakdown.values()), 4)))
    return score, breakdown


def _grade_medium(task: dict[str, Any], workspace: dict[str, Any]) -> tuple[float, dict[str, float]]:
    revealed = workspace["revealed"]
    messages = workspace["messages"]
    resolution = workspace["resolution"]

    diagnosis_hits = 0
    diagnosis_hits += int("ORD-2301" in revealed["orders"])
    diagnosis_hits += int("RET-07" in revealed["policies"])
    diagnosis_hits += int("GRIND-09" in revealed["inventory"])

    breakdown = {
        "diagnosis": round(0.2 * (diagnosis_hits / 3.0), 4),
        "policy_compliance": 0.15 if not workspace["refunds"] else 0.0,
        "operational_execution": 0.35
        if _find_replacement(workspace["replacements"], "ORD-2301", "GRIND-09", "west")
        else 0.0,
        "customer_communication": 0.1
        if _has_message(messages, "replacement") and (_has_message(messages, "no return") or _has_message(messages, "do not need to send"))
        else 0.0,
        "final_resolution": 0.2
        if resolution.get("status") == "resolved" and "replacement" in resolution.get("summary", "").lower()
        else 0.0,
    }

    if workspace["escalated"]:
        breakdown["final_resolution"] = max(0.0, breakdown["final_resolution"] - 0.1)

    score = max(0.0, min(1.0, round(sum(breakdown.values()), 4)))
    return score, breakdown


def _grade_hard(task: dict[str, Any], workspace: dict[str, Any]) -> tuple[float, dict[str, float]]:
    revealed = workspace["revealed"]
    messages = workspace["messages"]
    resolution = workspace["resolution"]

    diagnosis_hits = 0
    diagnosis_hits += int("ORD-4101" in revealed["orders"])
    diagnosis_hits += int("ORD-4102" in revealed["orders"])
    diagnosis_hits += int("VIP-03" in revealed["policies"])
    diagnosis_hits += int("PAY-02" in revealed["policies"])
    diagnosis_hits += int("JACKET-11-L" in revealed["inventory"])

    breakdown = {
        "diagnosis": round(0.2 * (diagnosis_hits / 5.0), 4),
        "financial_fix": 0.25 if _find_refund(workspace["refunds"], "ORD-4101", 129.99) else 0.0,
        "operational_execution": 0.25
        if _find_replacement(
            workspace["replacements"],
            "ORD-4102",
            "JACKET-11-L",
            "west",
            shipping_speed="express",
            waive_return=True,
        )
        else 0.0,
        "customer_communication": 0.15
        if _has_message(messages, "refund") and _has_message(messages, "exchange")
        else 0.0,
        "final_resolution": 0.15
        if resolution.get("status") == "resolved"
        and "refund" in resolution.get("summary", "").lower()
        and "exchange" in resolution.get("summary", "").lower()
        else 0.0,
    }

    if workspace["escalated"]:
        breakdown["final_resolution"] = max(0.0, breakdown["final_resolution"] - 0.1)

    score = max(0.0, min(1.0, round(sum(breakdown.values()), 4)))
    return score, breakdown
