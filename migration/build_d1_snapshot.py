"""Build a deterministic local SQLite/D1 snapshot from legacy Baak Books JSON.

ADR: D1SnapshotBuilder
======================
Problem:
    The legacy store keeps products, orders, gift data, and settings in one JSON
    document, while D1 needs explicit relational tables and constraints.
Decision:
    Normalize stable business fields into SQLite tables, preserve legacy payloads
    in JSON text columns, and fail closed on missing product references or invalid
    quantities. The resulting database and SQL dump are deterministic.
Consequences:
    The import can be checked offline before a one-shot D1 cutover. Existing
    legacy identifiers remain available for reconciliation and rollback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "d1_schema.sql"


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    """Hash a JSON-compatible value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sql_json(value: Any) -> str:
    """Encode JSON for a SQL TEXT column."""
    return canonical_json(value)


def as_int(value: Any, default: int = 0) -> int:
    """Convert a legacy numeric value to a bounded integer."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any, default: bool = False) -> int:
    """Convert legacy truthy values to SQLite integer booleans."""
    if value is None:
        return int(default)
    return int(bool(value))


def category_slug(name: str) -> str:
    """Return a stable internal category slug that works with Arabic names."""
    normalized = unicodedata.normalize("NFKC", str(name).strip())
    compact = re.sub(r"\s+", "-", normalized)
    compact = re.sub(r"[^\w\-\u0600-\u06ff]", "", compact, flags=re.UNICODE).strip("-")
    if compact:
        return compact[:80]
    return "category-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def product_rows(source: dict[str, Any]) -> tuple[list[tuple[Any, ...]], dict[str, str]]:
    """Build category and product rows and return the product-to-category map."""
    products = source.get("products", [])
    categories_by_name: dict[str, str] = {}
    for raw in source.get("categories", []):
        name = str(raw).strip()
        if name:
            categories_by_name.setdefault(name, category_slug(name))
    for raw in products:
        name = str(raw.get("category", "غير مصنف")).strip() or "غير مصنف"
        categories_by_name.setdefault(name, category_slug(name))

    categories = [
        (slug, name, 1)
        for name, slug in sorted(categories_by_name.items(), key=lambda pair: pair[0])
    ]
    rows: list[tuple[Any, ...]] = []
    product_category: dict[str, str] = {}
    seen: set[str] = set()
    for raw in products:
        product_id = str(raw.get("id", "")).strip()
        if not product_id or product_id in seen:
            raise ValueError(f"duplicate or missing product id: {product_id!r}")
        seen.add(product_id)
        category = str(raw.get("category", "غير مصنف")).strip() or "غير مصنف"
        category_id = categories_by_name[category]
        availability = str(raw.get("availability_type", "in_stock"))
        if availability not in {"in_stock", "on_demand"}:
            raise ValueError(f"invalid availability_type for product {product_id}: {availability}")
        minimum = min(1, max(0, as_int(raw.get("lead_time_min_days", 0))))
        maximum = min(1, max(minimum, as_int(raw.get("lead_time_max_days", raw.get("lead_time_days", 0)))))
        if availability == "on_demand" and maximum > 1:
            raise ValueError(f"on-demand lead time exceeds one day for product {product_id}")
        rows.append(
            (
                product_id,
                product_id,
                category_id,
                str(raw.get("title", "")).strip(),
                str(raw.get("desc", "")),
                str(raw.get("img", "")),
                max(0, as_int(raw.get("price", 0))),
                max(0, as_int(raw.get("stock_quantity", 0))),
                availability,
                minimum,
                maximum,
                maximum,
                as_bool(raw.get("active"), True),
                as_bool(raw.get("featured")),
                as_bool(raw.get("giftable")),
                as_bool(raw.get("discoverable"), True),
                as_bool(raw.get("archived")),
                sql_json(raw),
                1,
            )
        )
        product_category[product_id] = category_id
    return categories, rows, product_category


def delivery_rows(source: dict[str, Any]) -> list[tuple[Any, ...]]:
    """Build delivery fee rows."""
    rows = []
    for raw in source.get("delivery_fees", []):
        rows.append(
            (
                as_int(raw.get("num")),
                str(raw.get("name", "")).strip(),
                max(0, as_int(raw.get("domicile"))),
                max(0, as_int(raw.get("stop_desk"))),
            )
        )
    return rows


def normalize_status(value: Any) -> tuple[str, str | None]:
    """Map the legacy order status to the D1 contract."""
    mapping = {"New": "new", "Processing": "processing", "Delivered": "delivered"}
    legacy = str(value or "new")
    status = mapping.get(legacy, legacy.lower())
    valid = {"new", "confirmed", "awaiting_supply", "processing", "ready_to_ship", "shipped", "delivered", "cancelled", "returned"}
    if status not in valid:
        status = "new"
    return status, legacy if status != legacy else None


def order_rows(source: dict[str, Any], product_ids: set[str]) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    """Build orders, line items, and gift rows from legacy orders."""
    orders: list[tuple[Any, ...]] = []
    items: list[tuple[Any, ...]] = []
    gifts: list[tuple[Any, ...]] = []
    seen_orders: set[str] = set()
    for index, raw in enumerate(source.get("orders", [])):
        legacy_id = str(raw.get("order_id", raw.get("id", index + 1)))
        order_id = f"legacy-order-{legacy_id}"
        if order_id in seen_orders:
            raise ValueError(f"duplicate order id: {legacy_id}")
        seen_orders.add(order_id)
        status, legacy_status = normalize_status(raw.get("status"))
        orders.append(
            (
                order_id,
                legacy_id,
                status,
                str(raw.get("customer_name", "")),
                str(raw.get("phone", "")),
                str(raw.get("address", "")),
                str(raw.get("wilaya", "")),
                str(raw.get("delivery_type", "")),
                max(0, as_int(raw.get("delivery_fee"))),
                str(raw.get("order_type", "")),
                str(raw.get("shipping_policy", "")),
                str(raw.get("fulfillment_note", "")),
                max(0, as_int(raw.get("subtotal"))),
                max(0, as_int(raw.get("total"))),
                str(raw.get("timestamp", "")),
                None,
                legacy_status,
                sql_json(raw),
                1,
            )
        )

        personal = raw.get("personal_items") if isinstance(raw.get("personal_items"), list) else []
        gift_items = raw.get("gift_items") if isinstance(raw.get("gift_items"), list) else []
        if not personal and not gift_items:
            combined = raw.get("items") if isinstance(raw.get("items"), list) else []
            personal = combined
        line_number = 1
        for role, line_items in (("personal", personal), ("gift", gift_items)):
            for item in line_items:
                product_id = str(item.get("id", "")).strip()
                if product_id not in product_ids:
                    raise ValueError(f"order {legacy_id} references unknown product {product_id!r}")
                quantity = as_int(item.get("qty", 0))
                if quantity <= 0:
                    raise ValueError(f"order {legacy_id} has invalid quantity for {product_id}")
                items.append(
                    (
                        order_id,
                        line_number,
                        product_id,
                        role,
                        str(item.get("title", "")),
                        str(item.get("img", "")),
                        max(0, as_int(item.get("price"))),
                        quantity,
                        str(item.get("purchase_purpose", "")),
                        str(item.get("availability_type", "")),
                        min(1, max(0, as_int(item.get("lead_time_min_days", 0)))),
                        min(1, max(0, as_int(item.get("lead_time_max_days", item.get("lead_time_days", 0))))),
                        sql_json(item),
                    )
                )
                line_number += 1

        gift = raw.get("gift")
        if isinstance(gift, dict):
            budget = gift.get("budget")
            gifts.append(
                (
                    order_id,
                    str(gift.get("source", "")),
                    str(gift.get("sender_name", "")),
                    str(gift.get("recipient_name", "")),
                    str(gift.get("recipient_phone", "")),
                    str(gift.get("recipient_type", "")),
                    str(gift.get("message", "")),
                    str(gift.get("occasion", "")),
                    str(gift.get("mood", "")),
                    None if budget in (None, "") else max(0, as_int(budget)),
                    as_bool(gift.get("anonymous")),
                    sql_json(gift.get("gift_item_ids", [])),
                    sql_json(gift),
                )
            )
    return orders, items, gifts


def build(source_path: Path, database_path: Path, sql_path: Path, batch_id: str) -> dict[str, Any]:
    """Build the local D1-compatible database and SQL dump."""
    with source_path.open("r", encoding="utf-8") as handle:
        source = json.load(handle)
    categories, products, product_category = product_rows(source)
    product_ids = set(product_category)
    orders, items, gifts = order_rows(source, product_ids)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executemany("INSERT INTO categories (slug, name, active) VALUES (?, ?, ?)", categories)
        connection.executemany(
            "INSERT INTO products (id, legacy_id, category_slug, title, description, image_url, price, stock_quantity, availability_type, lead_time_min_days, lead_time_max_days, lead_time_days, active, featured, giftable, discoverable, archived, legacy_payload_json, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            products,
        )
        connection.executemany("INSERT INTO delivery_fees (region_number, region_name, domicile_fee, stop_desk_fee) VALUES (?, ?, ?, ?)", delivery_rows(source))
        connection.executemany(
            "INSERT INTO orders (id, legacy_order_id, status, customer_name, phone, address, wilaya, delivery_type, delivery_fee, order_type, shipping_policy, fulfillment_note, subtotal, total, source_timestamp, idempotency_key, legacy_status, legacy_payload_json, schema_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            orders,
        )
        connection.executemany(
            "INSERT INTO order_items (order_id, line_number, product_id, item_role, title_snapshot, image_snapshot, price_snapshot, quantity, purchase_purpose, availability_type, lead_time_min_days, lead_time_max_days, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            items,
        )
        connection.executemany(
            "INSERT INTO order_gifts (order_id, source, sender_name, recipient_name, recipient_phone, recipient_type, message, occasion, mood, budget, anonymous, gift_item_ids_json, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            gifts,
        )
        settings = source.get("settings", {})
        features = settings.get("features", {}) if isinstance(settings, dict) else {}
        connection.executemany(
            "INSERT INTO feature_flags (key, enabled) VALUES (?, ?)",
            [(str(key), as_bool(value)) for key, value in sorted(features.items())],
        )
        connection.execute(
            "INSERT INTO store_settings (key, value_json) VALUES (?, ?)",
            ("legacy_settings", sql_json(settings)),
        )
        for product in source.get("products", []):
            product_id = str(product.get("id", "")).strip()
            for tag_type, field in (("discovery", "discovery_tags"), ("gift", "gift_tags")):
                tags = product.get(field, []) if isinstance(product.get(field), list) else []
                connection.executemany(
                    "INSERT INTO product_tags (product_id, tag_type, tag) VALUES (?, ?, ?)",
                    [(product_id, tag_type, str(tag).strip()) for tag in tags if str(tag).strip()],
                )
            image_url = str(product.get("img", ""))
            if image_url:
                connection.execute(
                    "INSERT INTO image_assets (id, product_id, storage_provider, object_key, public_url, original_filename, mime_type, byte_size, archived, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f"legacy-image-{product_id}", product_id, "external", None, image_url, None, None, None, 0, sql_json({"source": "data.json", "product_id": product_id})),
                )
        counts = {
            "categories": connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
            "delivery_fees": connection.execute("SELECT COUNT(*) FROM delivery_fees").fetchone()[0],
            "products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "product_tags": connection.execute("SELECT COUNT(*) FROM product_tags").fetchone()[0],
            "orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            "order_items": connection.execute("SELECT COUNT(*) FROM order_items").fetchone()[0],
            "order_gifts": connection.execute("SELECT COUNT(*) FROM order_gifts").fetchone()[0],
            "feature_flags": connection.execute("SELECT COUNT(*) FROM feature_flags").fetchone()[0],
            "image_assets": connection.execute("SELECT COUNT(*) FROM image_assets").fetchone()[0],
        }
        connection.execute(
            "INSERT INTO migration_batches (batch_id, source_sha256, row_counts_json, status) VALUES (?, ?, ?, ?)",
            (batch_id, sha256_json(source), sql_json(counts), "prepared"),
        )
        connection.commit()
        dump = "\n".join(connection.iterdump()) + "\n"
        sql_path.parent.mkdir(parents=True, exist_ok=True)
        sql_path.write_text(dump, encoding="utf-8")
        return {"batch_id": batch_id, "source_sha256": sha256_json(source), "counts": counts}
    finally:
        connection.close()


def main() -> None:
    """Build a local snapshot and print its reconciliation metadata."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("database", type=Path)
    parser.add_argument("sql", type=Path)
    parser.add_argument("--batch-id", default="local-d1-dry-run")
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.database, args.sql, args.batch_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
