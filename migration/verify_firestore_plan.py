"""
Independent verifier for a Firestore NDJSON migration plan.

This file intentionally does not import firestore_import.py. It decodes the REST
Value format independently, recomputes source metrics, and checks identity,
counts, order totals, and source payload preservation before any target write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    """Serialize JSON deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    """Hash bytes with SHA-256."""
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    """Hash JSON deterministically."""
    return digest_bytes(canonical(value).encode("utf-8"))


def decode_value(value: dict[str, Any]) -> Any:
    """Decode one Firestore REST Value independently."""
    if "nullValue" in value:
        return None
    if "booleanValue" in value:
        return bool(value["booleanValue"])
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "timestampValue" in value:
        return value["timestampValue"]
    if "stringValue" in value:
        return value["stringValue"]
    if "referenceValue" in value:
        return value["referenceValue"]
    if "geoPointValue" in value:
        return value["geoPointValue"]
    if "bytesValue" in value:
        return value["bytesValue"]
    if "arrayValue" in value:
        return [decode_value(item) for item in value.get("arrayValue", {}).get("values", [])]
    if "mapValue" in value:
        return {key: decode_value(item) for key, item in value.get("mapValue", {}).get("fields", {}).items()}
    raise ValueError(f"unknown Firestore value shape: {value!r}")


def decode_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Decode a Firestore REST field map."""
    return {key: decode_value(value) for key, value in fields.items()}


def source_metrics(source: dict[str, Any]) -> dict[str, Any]:
    """Compute independent metrics from the local JSON source."""
    products = source.get("products", [])
    categories = source.get("categories", [])
    delivery_fees = source.get("delivery_fees", [])
    orders = source.get("orders", [])
    product_ids = [str(item.get("id", "")) for item in products]
    order_ids = [str(item.get("id", item.get("order_id", ""))) for item in orders]
    order_item_count = 0
    order_total_sum = 0
    for order in orders:
        items = order.get("items") if isinstance(order.get("items"), list) else []
        order_item_count += len(items)
        if isinstance(order.get("total"), (int, float)):
            order_total_sum += order["total"]
    return {
        "product_count": len(products),
        "category_count": len(categories),
        "delivery_fee_count": len(delivery_fees),
        "order_count": len(orders),
        "order_item_count": order_item_count,
        "product_ids": sorted(product_ids),
        "order_ids": sorted(order_ids),
        "order_total_sum": order_total_sum,
        "duplicate_product_ids": sorted(key for key, count in Counter(product_ids).items() if key and count > 1),
        "duplicate_order_ids": sorted(key for key, count in Counter(order_ids).items() if key and count > 1),
    }


def load_plan(plan_path: Path) -> tuple[dict[str, list[tuple[str, dict[str, Any]]]], str]:
    """Load and independently decode the NDJSON plan grouped by collection."""
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    raw_lines = []
    for line_number, line in enumerate(plan_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            path = str(record["path"])
            collection = str(record["collection"])
            fields = decode_fields(record["fields"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid plan record at line {line_number}: {error}") from error
        if path.split("/", 1)[0] != collection:
            raise ValueError(f"collection/path mismatch at line {line_number}: {path}")
        grouped[collection].append((path, fields))
        raw_lines.append(line)
    return grouped, digest_bytes(("\n".join(raw_lines) + "\n").encode("utf-8"))


def target_metrics(grouped: dict[str, list[tuple[str, dict[str, Any]]]]) -> dict[str, Any]:
    """Compute independent metrics from decoded Firestore plan documents."""
    products = [fields for _, fields in grouped.get("products", [])]
    orders = [fields for _, fields in grouped.get("orders", [])]
    product_ids = [str(item.get("legacyId", item.get("id", ""))) for item in products]
    order_ids = [str(item.get("legacyOrderId", "")) for item in orders]
    order_item_count = sum(len(item.get("items", [])) for item in orders if isinstance(item.get("items"), list))
    order_total_sum = sum(item.get("total", 0) for item in orders if isinstance(item.get("total"), (int, float)))
    return {
        "product_count": len(products),
        "category_count": len(grouped.get("categories", [])),
        "delivery_fee_count": len(grouped.get("deliveryFees", [])),
        "order_count": len(orders),
        "order_item_count": order_item_count,
        "product_ids": sorted(product_ids),
        "order_ids": sorted(order_ids),
        "order_total_sum": order_total_sum,
        "duplicate_product_ids": sorted(key for key, count in Counter(product_ids).items() if key and count > 1),
        "duplicate_order_ids": sorted(key for key, count in Counter(order_ids).items() if key and count > 1),
    }


def verify(source: dict[str, Any], plan_path: Path, expected_source_hash: str | None) -> dict[str, Any]:
    """Compare the local source with an independently decoded Firestore plan."""
    grouped, plan_hash = load_plan(plan_path)
    source_values = source_metrics(source)
    target_values = target_metrics(grouped)
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
    errors: list[str] = []
    if differences:
        errors.append("metric mismatch")
    if source_values["duplicate_product_ids"] or target_values["duplicate_product_ids"]:
        errors.append("duplicate product IDs")
    if source_values["duplicate_order_ids"] or target_values["duplicate_order_ids"]:
        errors.append("duplicate order IDs")

    product_docs = {path.split("/", 1)[1]: fields for path, fields in grouped.get("products", [])}
    for product_id, fields in product_docs.items():
        if fields.get("id") != product_id or fields.get("legacyId") != product_id:
            errors.append(f"product identity mismatch: {product_id}")
        if fields.get("legacyPayload", {}).get("id") != product_id:
            errors.append(f"product legacy payload mismatch: {product_id}")
    order_docs = {path.split("/", 1)[1]: fields for path, fields in grouped.get("orders", [])}
    for document_id, fields in order_docs.items():
        if fields.get("id") != document_id:
            errors.append(f"order identity mismatch: {document_id}")
        if fields.get("legacyPayload", {}).get("order_id", fields.get("legacyPayload", {}).get("id")) != fields.get("legacyOrderId"):
            errors.append(f"order legacy payload mismatch: {document_id}")
        if not isinstance(fields.get("items"), list):
            errors.append(f"order items missing: {document_id}")
        if fields.get("total") != max(0, int(fields.get("subtotal", 0))) + max(0, int(fields.get("deliveryFee", 0))):
            errors.append(f"order total arithmetic mismatch: {document_id}")

    metadata = grouped.get("migrationMetadata", [])
    if len(metadata) != 1:
        errors.append("migration metadata document count is not one")
    elif expected_source_hash and metadata[0][1].get("sourceFileSha256") != expected_source_hash:
        errors.append("migration metadata source hash mismatch")

    return {
        "status": "verified" if not errors else "failed",
        "errors": sorted(set(errors)),
        "differences": differences,
        "sourceSha256": expected_source_hash,
        "planSha256": plan_hash,
        "source": source_values,
        "target": target_values,
    }


def main() -> int:
    """Run independent plan verification."""
    parser = argparse.ArgumentParser(description="Independently verify a Firestore NDJSON plan.")
    parser.add_argument("source", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source = json.loads(source_bytes.decode("utf-8"))
    result = verify(source, args.plan, digest_bytes(source_bytes))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
