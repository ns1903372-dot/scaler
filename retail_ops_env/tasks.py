from __future__ import annotations

from copy import deepcopy


TASKS: list[dict] = [
    {
        "id": "easy_address_fix",
        "difficulty": "easy",
        "title": "Fix a shipping address before dispatch cutoff",
        "max_steps": 6,
        "instruction": (
            "A customer noticed the apartment number on an order is wrong. "
            "Correct the shipping address before warehouse cutoff, confirm the change, and close the case."
        ),
        "case": {
            "case_id": "CASE-1001",
            "priority": "standard",
            "customer_name": "Asha Mehta",
            "customer_tier": "standard",
            "customer_message": "Please change my apartment number from Apt 2 to Apt 5 before it ships.",
            "warehouse_cutoff_minutes": 45,
            "order_ids": ["ORD-1001"],
        },
        "orders": {
            "ORD-1001": {
                "status": "packed",
                "sku": "LAMP-01",
                "item_name": "Desk Lamp",
                "shipping_address": {
                    "line1": "221B Baker Street",
                    "apartment": "Apt 2",
                    "city": "Mumbai",
                    "postal_code": "400001",
                },
                "requested_address": {
                    "line1": "221B Baker Street",
                    "apartment": "Apt 5",
                    "city": "Mumbai",
                    "postal_code": "400001",
                },
                "price": 39.99,
            }
        },
        "policies": {
            "ADDR-01": {
                "title": "Pre-dispatch address corrections",
                "body": "Address changes are allowed before dispatch cutoff without extra fees.",
            }
        },
        "inventory": {},
    },
    {
        "id": "medium_damaged_item",
        "difficulty": "medium",
        "title": "Replace a damaged delivery using inventory and policy",
        "max_steps": 8,
        "instruction": (
            "A customer received a damaged coffee grinder yesterday. "
            "Use policy and inventory data to choose the correct remedy, notify the customer, and close the case."
        ),
        "case": {
            "case_id": "CASE-2301",
            "priority": "high",
            "customer_name": "Rohan Kapoor",
            "customer_tier": "standard",
            "customer_message": "The grinder jar arrived cracked. I still want the product if you can replace it quickly.",
            "warehouse_cutoff_minutes": 180,
            "order_ids": ["ORD-2301"],
        },
        "orders": {
            "ORD-2301": {
                "status": "delivered",
                "sku": "GRIND-09",
                "item_name": "Ceramic Coffee Grinder",
                "shipping_address": {
                    "line1": "14 Residency Road",
                    "apartment": "Flat 8C",
                    "city": "Bengaluru",
                    "postal_code": "560025",
                },
                "price": 48.50,
            }
        },
        "policies": {
            "RET-07": {
                "title": "Damaged on arrival policy",
                "body": (
                    "For damaged items reported within 7 days, offer free replacement or full refund. "
                    "For products priced below $50, no return shipment is required."
                ),
            }
        },
        "inventory": {
            "GRIND-09": {
                "warehouses": {
                    "north": 0,
                    "west": 7,
                }
            }
        },
    },
    {
        "id": "hard_vip_exchange_and_refund",
        "difficulty": "hard",
        "title": "Resolve a VIP duplicate charge and size exchange",
        "max_steps": 10,
        "instruction": (
            "A VIP customer has two linked issues: one order was charged twice and another needs a size exchange. "
            "Follow policy, use live inventory, send a clear customer update, and close the case."
        ),
        "case": {
            "case_id": "CASE-4107",
            "priority": "vip",
            "customer_name": "Neha Suri",
            "customer_tier": "vip",
            "customer_lifetime_value": 3820.40,
            "customer_message": (
                "I was charged twice for my belt order, and the jacket on my second order is the wrong size. "
                "I need the replacement before next week."
            ),
            "warehouse_cutoff_minutes": 300,
            "order_ids": ["ORD-4101", "ORD-4102"],
        },
        "orders": {
            "ORD-4101": {
                "status": "delivered",
                "sku": "BELT-77",
                "item_name": "Leather Belt",
                "price": 129.99,
                "duplicate_charge_amount": 129.99,
            },
            "ORD-4102": {
                "status": "delivered",
                "sku": "JACKET-11-M",
                "requested_exchange_sku": "JACKET-11-L",
                "item_name": "Travel Jacket",
                "price": 189.00,
            },
        },
        "policies": {
            "VIP-03": {
                "title": "VIP service recovery",
                "body": (
                    "VIP customers may receive instant exchanges if stock is available. "
                    "Return shipment may be waived for size issues. "
                    "Shipping may be upgraded to express for customers with lifetime value above $1000."
                ),
            },
            "PAY-02": {
                "title": "Duplicate charge policy",
                "body": "Duplicate charges must be refunded in full to the original payment method.",
            },
        },
        "inventory": {
            "JACKET-11-L": {
                "warehouses": {
                    "west": 2,
                    "south": 0,
                }
            }
        },
    },
]


TASK_INDEX = {task["id"]: task for task in TASKS}


def get_task(task_id: str) -> dict:
    if task_id not in TASK_INDEX:
        raise KeyError(f"Unknown task_id: {task_id}")
    return deepcopy(TASK_INDEX[task_id])


def list_tasks() -> list[dict]:
    return [deepcopy(task) for task in TASKS]
