"""Profile nested order structures for the local D1 migration."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def type_name(value: Any) -> str:
    """Return a stable JSON-oriented type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def profile_list(values: list[Any]) -> dict[str, Any]:
    """Profile keys and types across a list of JSON objects."""
    keys: Counter[str] = Counter()
    types: dict[str, Counter[str]] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        for key, item in value.items():
            keys[key] += 1
            types.setdefault(key, Counter())[type_name(item)] += 1
    return {
        "count": len(values),
        "keys": dict(sorted(keys.items())),
        "types": {key: dict(sorted(counter.items())) for key, counter in sorted(types.items())},
    }


def profile(source_path: Path) -> dict[str, Any]:
    """Return nested order and gift field profiles."""
    with source_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    orders = payload.get("orders", [])
    items: list[Any] = []
    personal_items: list[Any] = []
    gift_items: list[Any] = []
    gifts: list[Any] = []
    for order in orders:
        items.extend(order.get("items", []) if isinstance(order.get("items"), list) else [])
        personal_items.extend(order.get("personal_items", []) if isinstance(order.get("personal_items"), list) else [])
        gift_items.extend(order.get("gift_items", []) if isinstance(order.get("gift_items"), list) else [])
        if isinstance(order.get("gift"), dict):
            gifts.append(order["gift"])
    return {
        "orders": len(orders),
        "items": profile_list(items),
        "personal_items": profile_list(personal_items),
        "gift_items": profile_list(gift_items),
        "gift": profile_list(gifts),
    }


def main() -> None:
    """Write the nested order profile."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = profile(args.source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
