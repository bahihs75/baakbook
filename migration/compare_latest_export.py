#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collection_items(data, name):
    value = data.get(name, [])
    if isinstance(value, dict):
        return [{"id": key, **(item if isinstance(item, dict) else {"value": item})} for key, item in value.items()]
    return value if isinstance(value, list) else []


def id_for(item):
    if not isinstance(item, dict):
        return None
    return item.get("id") or item.get("order_id") or item.get("legacyOrderId") or item.get("code")


def summary(data):
    result = {}
    for name in ("products", "categories", "delivery_fees", "deliveryFees", "orders"):
        items = collection_items(data, name)
        if items:
            ids = sorted(str(item_id) for item_id in (id_for(x) for x in items) if item_id is not None)
            result[name] = {"count": len(items), "ids": ids}
            if name == "orders":
                total = 0
                item_count = 0
                for order in items:
                    if isinstance(order, dict):
                        total += order.get("total", order.get("total_price", order.get("amount", 0))) or 0
                        order_items = order.get("items", order.get("order_items", [])) or []
                        item_count += len(order_items) if isinstance(order_items, list) else 0
                result[name]["order_item_count"] = item_count
                result[name]["total_sum"] = total
    return result


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: compare_latest_export.py <latest-normalized> <previous-normalized>")
    latest_path, previous_path = sys.argv[1:]
    latest = load(latest_path)
    previous = load(previous_path)
    latest_summary = summary(latest)
    previous_summary = summary(previous)
    print(json.dumps({
        "latest_sha256": sha(latest_path),
        "previous_sha256": sha(previous_path),
        "latest_summary": latest_summary,
        "previous_summary": previous_summary,
        "summary_equal": latest_summary == previous_summary,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
