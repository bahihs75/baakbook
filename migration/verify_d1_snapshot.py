"""Independently verify a local SQLite/D1 snapshot against legacy JSON.

This verifier intentionally does not import or reuse the snapshot builder. It
recomputes source facts and queries the target database independently so the
migration check can detect importer mistakes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    """Hash a JSON-compatible value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def source_facts(source: dict[str, Any]) -> dict[str, Any]:
    """Compute reconciliation facts directly from source JSON."""
    orders = source.get("orders", [])
    return {
        "categories": len(source.get("categories", [])),
        "delivery_fees": len(source.get("delivery_fees", [])),
        "products": len(source.get("products", [])),
        "orders": len(orders),
        "order_items": sum(len(order.get("items", [])) for order in orders),
        "order_gift_records": sum(1 for order in orders if isinstance(order.get("gift"), dict)),
        "product_price_sum": sum(int(item.get("price", 0)) for item in source.get("products", [])),
        "order_total_sum": sum(int(order.get("total", 0)) for order in orders),
        "source_sha256": sha256_json(source),
    }


def target_facts(database: Path) -> dict[str, Any]:
    """Compute reconciliation facts directly from SQLite."""
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        tables = ["categories", "delivery_fees", "products", "orders", "order_items", "order_gifts"]
        facts: dict[str, Any] = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
        facts["product_price_sum"] = connection.execute("SELECT COALESCE(SUM(price), 0) FROM products").fetchone()[0]
        facts["order_total_sum"] = connection.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone()[0]
        facts["source_sha256"] = connection.execute("SELECT source_sha256 FROM migration_batches ORDER BY created_at DESC LIMIT 1").fetchone()[0]
        facts["foreign_key_violations"] = connection.execute("PRAGMA foreign_key_check").fetchall()
        facts["duplicate_products"] = connection.execute("SELECT legacy_id, COUNT(*) FROM products GROUP BY legacy_id HAVING COUNT(*) > 1").fetchall()
        facts["duplicate_orders"] = connection.execute("SELECT legacy_order_id, COUNT(*) FROM orders GROUP BY legacy_order_id HAVING COUNT(*) > 1").fetchall()
        return facts
    finally:
        connection.close()


def verify(source_path: Path, database_path: Path) -> dict[str, Any]:
    """Return a detailed independent comparison."""
    with source_path.open("r", encoding="utf-8") as handle:
        source = json.load(handle)
    source_data = source_facts(source)
    target_data = target_facts(database_path)
    mapping = {
        "categories": "categories",
        "delivery_fees": "delivery_fees",
        "products": "products",
        "orders": "orders",
        "order_items": "order_items",
        "order_gift_records": "order_gifts",
        "product_price_sum": "product_price_sum",
        "order_total_sum": "order_total_sum",
    }
    comparisons = {
        key: {"source": source_data[source_key], "target": target_data[target_key], "match": source_data[source_key] == target_data[target_key]}
        for source_key, target_key in mapping.items()
        for key in [source_key]
    }
    checks = {
        "all_mapped_values_match": all(item["match"] for item in comparisons.values()),
        "source_hash_recorded": source_data["source_sha256"] == target_data["source_sha256"],
        "foreign_keys_clean": not target_data["foreign_key_violations"],
        "no_duplicate_product_legacy_ids": not target_data["duplicate_products"],
        "no_duplicate_order_legacy_ids": not target_data["duplicate_orders"],
    }
    return {
        "source": source_data,
        "target": target_data,
        "comparisons": comparisons,
        "checks": checks,
        "verified": all(checks.values()),
    }


def main() -> None:
    """Run verification and fail if any reconciliation check fails."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("database", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = verify(args.source, args.database)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
