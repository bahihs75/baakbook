"""Read-only source inventory for the Baak Books one-shot migration.

This module never writes to the source data file and never contacts an external
service. It produces deterministic counts, identifier checks, and a SHA-256
fingerprint of the canonical source payload so the final cutover can be
verified independently from the importer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically for reproducible fingerprints."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    """Return a SHA-256 digest for a JSON-compatible value."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def inventory(source_path: Path) -> dict[str, Any]:
    """Build a read-only inventory of a Baak Books JSON export."""
    with source_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    products = payload.get("products", [])
    categories = payload.get("categories", [])
    delivery_fees = payload.get("delivery_fees", [])
    orders = payload.get("orders", [])
    settings = payload.get("settings", {})

    product_ids = [str(item.get("id", "")) for item in products]
    order_ids = [str(item.get("id", item.get("order_id", ""))) for item in orders]
    availability = Counter(str(item.get("availability_type", "missing")) for item in products)
    order_statuses = Counter(str(item.get("status", "missing")) for item in orders)
    product_images = [item.get("img") for item in products]
    prices = [item.get("price") for item in products if isinstance(item.get("price"), (int, float))]
    order_totals = [item.get("total") for item in orders if isinstance(item.get("total"), (int, float))]
    order_item_count = sum(len(item.get("items", [])) for item in orders if isinstance(item.get("items"), list))

    duplicate_product_ids = sorted(key for key, count in Counter(product_ids).items() if key and count > 1)
    duplicate_order_ids = sorted(key for key, count in Counter(order_ids).items() if key and count > 1)
    missing_product_ids = sum(1 for key in product_ids if not key)
    missing_order_ids = sum(1 for key in order_ids if not key)
    missing_image_urls = sum(1 for image in product_images if not image)

    return {
        "source_file": str(source_path),
        "source_sha256": sha256_json(payload),
        "source_bytes": source_path.stat().st_size,
        "counts": {
            "products": len(products),
            "categories": len(categories),
            "delivery_fees": len(delivery_fees),
            "orders": len(orders),
            "order_items": order_item_count,
        },
        "products": {
            "availability_types": dict(sorted(availability.items())),
            "missing_ids": missing_product_ids,
            "duplicate_ids": duplicate_product_ids,
            "missing_image_urls": missing_image_urls,
            "price_sum": sum(prices),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
        },
        "orders": {
            "statuses": dict(sorted(order_statuses.items())),
            "missing_ids": missing_order_ids,
            "duplicate_ids": duplicate_order_ids,
            "total_sum": sum(order_totals),
            "total_min": min(order_totals) if order_totals else None,
            "total_max": max(order_totals) if order_totals else None,
        },
        "settings_feature_flags": sorted((settings.get("features") or {}).keys()),
        "validation": {
            "has_duplicate_product_ids": bool(duplicate_product_ids),
            "has_duplicate_order_ids": bool(duplicate_order_ids),
            "has_missing_product_ids": bool(missing_product_ids),
            "has_missing_order_ids": bool(missing_order_ids),
            "has_invalid_availability_types": any(key not in {"in_stock", "on_demand", "missing"} for key in availability),
        },
    }


def main() -> None:
    """Parse CLI arguments and write a JSON inventory report."""
    parser = argparse.ArgumentParser(description="Inventory a Baak Books JSON export without modifying it.")
    parser.add_argument("source", type=Path, help="Path to data.json export")
    parser.add_argument("report", type=Path, help="Output report path")
    args = parser.parse_args()

    report = inventory(args.source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
