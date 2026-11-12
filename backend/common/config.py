"""AMSDP org/branch queue configuration helpers (default-disabled).

Reads ``queue_config`` from the Organization ``config`` JSON:

    {
      "queue_config": {
        "walk_in_reserve_mode": "percent" | "count",
        "walk_in_reserve_value": int   # percent of capacity, or fixed count
      }
    }

Default: no reservation configured -> behaviour identical to prior releases.
"""


def get_queue_config(org_config=None) -> dict:
    cfg = (org_config or {}).get("queue_config") or {}
    mode = cfg.get("walk_in_reserve_mode")
    if mode not in ("percent", "count"):
        mode = "percent"
    value = int(cfg.get("walk_in_reserve_value") or 0)
    return {"walk_in_reserve_mode": mode,
            "walk_in_reserve_value": max(value, 0)}


def reserved_for_capacity(capacity: int, org_config=None) -> int:
    """Number of slots reserved for walk-ins for a capacity of *capacity*."""
    cfg = get_queue_config(org_config)
    value = cfg["walk_in_reserve_value"]
    if value <= 0 or capacity <= 0:
        return 0
    if cfg["walk_in_reserve_mode"] == "count":
        return min(value, capacity)
    return int(round(capacity * value / 100.0))