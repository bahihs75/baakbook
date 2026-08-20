"""Deterministic, offline transformation from the legacy JSON store to a Firestore-shaped bundle.

The transformer has no Firebase dependency and performs no network or source-file
writes. It is deliberately separate from the target verifier so the migration
can be checked by two independent implementations.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

VALID_AVAILABILITY = {"in_stock", "on_demand"}
VALID_STATUSES = {
    "new",
    "confirmed",
    "awaiting_supply",
    "processing",
    "ready_to_ship",
    "shipped",
    "delivered",
    "cancelled",
    "returned",
}
LEGACY_STATUS_MAP = {
    "New": "new",
    "Processing": "processing",
    "Delivered": "delivered",
}


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    """Return a stable SHA-256 digest for a JSON-compatible value."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def as_int(value: Any, default: int = 0) -> int:
    """Convert a value to an integer without raising for legacy data."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def tags(value: Any) -> list[str]:
    """Normalize comma-separated or list tags while preserving order."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def normalize_product(source: dict[str, Any]) -> dict[str, Any]:
    """Convert one legacy product to the version-one Firestore contract."""
    product = copy.deepcopy(source)
    product_id = str(product.get("id", "")).strip()
    if not product_id:
        raise ValueError("product is missing id")

    availability = str(product.get("availability_type", "in_stock"))
    if availability not in VALID_AVAILABILITY:
        raise ValueError(f"product {product_id} has invalid availability_type={availability!r}")

    legacy_lead = min(1, max(0, as_int(product.get("lead_time_days", 0))))
    minimum = min(1, max(0, as_int(product.get("lead_time_min_days", legacy_lead), legacy_lead)))
    maximum = min(1, max(minimum, as_int(product.get("lead_time_max_days", legacy_lead), legacy_lead)))
    product.update(
        {
            "id": product_id,
            "legacyId": product_id,
            "availability_type": availability,
            "stock_quantity": max(0, as_int(product.get("stock_quantity", 0))),
            "lead_time_min_days": minimum,
            "lead_time_max_days": maximum,
            "lead_time_days": maximum,
            "discovery_tags": tags(product.get("discovery_tags", [])),
            "gift_tags": tags(product.get("gift_tags", [])),
            "active": bool(product.get("active", True)),
            "featured": bool(product.get("featured", False)),
            "giftable": bool(product.get("giftable", False)),
            "discoverable": bool(product.get("discoverable", True)),
            "archived": bool(product.get("archived", False)),
            "schemaVersion": 1,
        }
    )
    return product


def normalize_status(value: Any) -> tuple[str, str | None]:
    """Normalize a legacy status and retain the old value when it changes."""
    legacy = str(value or "new")
    normalized = LEGACY_STATUS_MAP.get(legacy, legacy.lower())
    if normalized not in VALID_STATUSES:
        normalized = "new"
    return normalized, legacy if normalized != legacy else None


def normalize_order(source: dict[str, Any], index: int) -> dict[str, Any]:
    """Convert one legacy order while preserving the original payload."""
    order = copy.deepcopy(source)
    raw_id = order.get("id", order.get("order_id", index + 1))
    legacy_id = str(raw_id)
    status, legacy_status = normalize_status(order.get("status"))
    target = copy.deepcopy(order)
    target.update(
        {
            "id": f"legacy-order-{legacy_id}",
            "legacyOrderId": raw_id,
            "status": status,
            "source": "legacy-pythonanywhere",
            "schemaVersion": 1,
            "legacyPayload": order,
        }
    )
    if legacy_status is not None:
        target["legacyStatus"] = legacy_status
    return target


def transform(source: dict[str, Any], batch_id: str) -> dict[str, Any]:
    """Transform a complete source payload into a deterministic target bundle."""
    products = [normalize_product(item) for item in source.get("products", [])]
    product_ids = [item["id"] for item in products]
    if len(product_ids) != len(set(product_ids)):
        raise ValueError("duplicate product IDs")

    orders = [normalize_order(item, index) for index, item in enumerate(source.get("orders", []))]
    order_ids = [item["id"] for item in orders]
    if len(order_ids) != len(set(order_ids)):
        raise ValueError("duplicate order IDs")

    settings = copy.deepcopy(source.get("settings", {}))
    settings.setdefault("features", {})
    return {
        "products": products,
        "categories": copy.deepcopy(source.get("categories", [])),
        "deliveryFees": copy.deepcopy(source.get("delivery_fees", [])),
        "orders": orders,
        "settings": settings,
        "nextOrderId": source.get("next_order_id", 1),
        "migrationMetadata": {
            "batchId": batch_id,
            "sourceSha256": digest(source),
            "toolVersion": "1.0.0",
            "status": "dry_run_bundle",
        },
    }


def main() -> None:
    """Transform a source JSON file into an offline target fixture."""
    parser = argparse.ArgumentParser(description="Transform Baak Books JSON to a deterministic Firestore-shaped bundle.")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-id", default="local-dry-run")
    args = parser.parse_args()

    with args.source.open("r", encoding="utf-8") as handle:
        source = json.load(handle)
    target = transform(source, args.batch_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(target, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(target["migrationMetadata"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
