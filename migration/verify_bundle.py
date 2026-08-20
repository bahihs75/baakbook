"""Independent verifier for a Firestore-shaped migration bundle.

This verifier intentionally does not import the transformation module. It reads
the raw source inventory and the target bundle separately, recomputes core
metrics, and fails on unexplained loss, duplication, or financial drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    """Serialize a JSON value deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    """Return a stable SHA-256 digest."""
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def source_metrics(source: dict[str, Any]) -> dict[str, Any]:
    """Compute independent metrics from the legacy source."""
    products = source.get("products", [])
    orders = source.get("orders", [])
    product_ids = [str(item.get("id", "")) for item in products]
    order_ids = [str(item.get("id", item.get("order_id", ""))) for item in orders]
    totals = [item.get("total") for item in orders if isinstance(item.get("total"), (int, float))]
    return {
        "product_count": len(products),
        "category_count": len(source.get("categories", [])),
        "delivery_fee_count": len(source.get("delivery_fees", [])),
        "order_count": len(orders),
        "order_item_count": sum(len(item.get("items", [])) for item in orders if isinstance(item.get("items"), list)),
        "product_ids": sorted(product_ids),
        "order_ids": sorted(order_ids),
        "order_total_sum": sum(totals),
        "duplicate_product_ids": sorted(key for key, count in Counter(product_ids).items() if key and count > 1),
        "duplicate_order_ids": sorted(key for key, count in Counter(order_ids).items() if key and count > 1),
    }


def target_metrics(target: dict[str, Any]) -> dict[str, Any]:
    """Compute independent metrics from a target bundle."""
    products = target.get("products", [])
    orders = target.get("orders", [])
    product_ids = [str(item.get("legacyId", item.get("id", ""))) for item in products]
    order_ids = [str(item.get("legacyOrderId", "")) for item in orders]
    totals = [item.get("total") for item in orders if isinstance(item.get("total"), (int, float))]
    return {
        "product_count": len(products),
        "category_count": len(target.get("categories", [])),
        "delivery_fee_count": len(target.get("deliveryFees", [])),
        "order_count": len(orders),
        "order_item_count": sum(len(item.get("items", [])) for item in orders if isinstance(item.get("items"), list)),
        "product_ids": sorted(product_ids),
        "order_ids": sorted(order_ids),
        "order_total_sum": sum(totals),
        "duplicate_product_ids": sorted(key for key, count in Counter(product_ids).items() if key and count > 1),
        "duplicate_order_ids": sorted(key for key, count in Counter(order_ids).items() if key and count > 1),
    }


def verify(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Compare independently calculated source and target metrics."""
    source_values = source_metrics(source)
    target_values = target_metrics(target)
    exact_keys = [
        "product_count",
        "category_count",
        "delivery_fee_count",
        "order_count",
        "order_item_count",
        "product_ids",
        "order_ids",
        "order_total_sum",
    ]
    differences = {
        key: {"source": source_values[key], "target": target_values[key]}
        for key in exact_keys
        if source_values[key] != target_values[key]
    }
    errors = []
    if source_values["duplicate_product_ids"] or target_values["duplicate_product_ids"]:
        errors.append("duplicate product IDs")
    if source_values["duplicate_order_ids"] or target_values["duplicate_order_ids"]:
        errors.append("duplicate order IDs")
    if differences:
        errors.append("metric mismatch")
    return {
        "status": "verified" if not errors else "failed",
        "errors": errors,
        "differences": differences,
        "sourceSha256": digest(source),
        "source": source_values,
        "target": target_values,
    }


def main() -> None:
    """Run independent verification and exit non-zero on failure."""
    parser = argparse.ArgumentParser(description="Independently verify a target migration bundle.")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    target = json.loads(args.target.read_text(encoding="utf-8"))
    result = verify(source, target)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "verified":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
