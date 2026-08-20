"""
ADR: FirestoreImportPlan
========================
Problem:
    The legacy Baak Books store keeps products, orders, delivery fees, categories,
    and feature flags in one JSON document. The first Firestore migration must
    preserve identifiers and legacy payloads, produce an auditable plan, and make
    accidental writes to the real project difficult.

Alternatives Considered:
    1. Import directly from the browser — rejected: the browser is not trusted
       and cannot safely write historical orders or migration metadata.
    2. Use Firebase Admin SDK with an embedded service-account file — rejected:
       credentials must never be stored in the repository or local source tree.
    3. Use Firestore REST documents with a dry-run plan and explicit target modes —
       chosen: dependency-light, inspectable, emulator-friendly, and fail-closed.

Decision:
    Build a complete Firestore document plan from the local source file, write it
    as NDJSON plus a manifest, and apply it only when the caller explicitly uses
    --apply. Emulator writes use the Emulator-only owner token. Production REST
    writes require FIRESTORE_ACCESS_TOKEN and --confirm-live, and refuse existing
    documents before creating anything.

Consequences:
    + Every document and source hash can be reviewed before import.
    + Existing target documents are protected by a create-only preflight.
    + The same plan can be tested against demo-baakbook Emulator.
    - A production access token must be provided out-of-band at cutover time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data.json"
DEFAULT_REPORT_ROOT = ROOT / "migration" / "reports"
EXPECTED_PRODUCTION_PROJECT = "baakbook-77c00"
SCHEMA_VERSION = 1
TOOL_VERSION = "firestore-import-1.0.0"


class ImportValidationError(ValueError):
    """Raised when the local source violates the Firestore data contract."""


class TargetWriteError(RuntimeError):
    """Raised when a target preflight or document creation fails."""


@dataclass(frozen=True)
class DocumentPlan:
    """One Firestore document and its exact REST field map."""

    path: str
    fields: dict[str, Any]
    collection: str
    legacy_id: str | int | None = None


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    """Return a SHA-256 digest for bytes."""
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    """Return a deterministic SHA-256 digest for JSON-compatible data."""
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def as_int(value: Any, default: int = 0) -> int:
    """Convert a legacy numeric value to an integer or a safe default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any, default: bool = False) -> bool:
    """Convert legacy truthy values to a JSON boolean."""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def category_slug(name: str) -> str:
    """Create a stable category document ID that supports Arabic names."""
    normalized = unicodedata.normalize("NFKC", str(name).strip())
    compact = re.sub(r"\s+", "-", normalized)
    compact = re.sub(r"[^\w\-\u0600-\u06ff]", "", compact, flags=re.UNICODE).strip("-")
    return (compact[:80] or "category-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12])


def now_iso() -> str:
    """Return an RFC 3339 UTC timestamp accepted by Firestore REST."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_timestamp(value: Any, fallback: str) -> str:
    """Normalize a legacy timestamp to RFC 3339, retaining fallback on failure."""
    if not value:
        return fallback
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp_value(value: str) -> dict[str, str]:
    """Mark an RFC 3339 timestamp for conversion by ``firestore_value``."""
    return {"__firestore_type__": "timestamp", "value": value}


def firestore_value(value: Any) -> dict[str, Any]:
    """Encode ordinary JSON values using the Firestore REST Value format."""
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, list):
        return {"arrayValue": {"values": [firestore_value(item) for item in value]}}
    if isinstance(value, dict) and value.get("__firestore_type__") == "timestamp" and set(value) == {"__firestore_type__", "value"}:
        return {"timestampValue": str(value["value"])}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {str(k): firestore_value(v) for k, v in value.items()}}}
    raise ImportValidationError(f"unsupported value type: {type(value).__name__}")


def fields(values: dict[str, Any]) -> dict[str, Any]:
    """Encode a document field map for Firestore REST."""
    return {key: firestore_value(value) for key, value in values.items()}


def validate_product(raw: dict[str, Any], seen: set[str]) -> tuple[str, str, dict[str, Any]]:
    """Validate and normalize one legacy product."""
    product_id = str(raw.get("id", "")).strip()
    if not product_id or product_id in seen:
        raise ImportValidationError(f"duplicate or missing product id: {product_id!r}")
    seen.add(product_id)
    title = str(raw.get("title", "")).strip()
    category = str(raw.get("category", "غير مصنف")).strip() or "غير مصنف"
    if not title:
        raise ImportValidationError(f"product {product_id} has an empty title")
    price = as_int(raw.get("price"), -1)
    if price <= 0:
        raise ImportValidationError(f"product {product_id} has a non-positive price")
    stock = as_int(raw.get("stock_quantity"), -1)
    if stock < 0:
        raise ImportValidationError(f"product {product_id} has a negative stock quantity")
    availability = str(raw.get("availability_type", "in_stock")).strip() or "in_stock"
    if availability not in {"in_stock", "on_demand"}:
        raise ImportValidationError(f"product {product_id} has invalid availability_type {availability!r}")
    minimum = min(1, max(0, as_int(raw.get("lead_time_min_days", 0))))
    maximum = min(1, max(minimum, as_int(raw.get("lead_time_max_days", raw.get("lead_time_days", 0)))))
    if availability == "on_demand" and maximum > 1:
        raise ImportValidationError(f"product {product_id} exceeds the one-day on-demand limit")
    normalized = {
        "id": product_id,
        "legacyId": product_id,
        "title": title,
        "author": str(raw.get("author", "")).strip(),
        "category": category,
        "desc": str(raw.get("desc", "")),
        "img": str(raw.get("img", "")),
        "price": price,
        "active": as_bool(raw.get("active"), True),
        "stock_quantity": stock,
        "availability_type": availability,
        "lead_time_min_days": minimum,
        "lead_time_max_days": maximum,
        "lead_time_days": maximum,
        "featured": as_bool(raw.get("featured")),
        "giftable": as_bool(raw.get("giftable")),
        "discoverable": as_bool(raw.get("discoverable"), True),
        "discovery_tags": raw.get("discovery_tags", []) if isinstance(raw.get("discovery_tags", []), list) else [],
        "gift_tags": raw.get("gift_tags", []) if isinstance(raw.get("gift_tags", []), list) else [],
        "editorial_note": str(raw.get("editorial_note", "")),
        "archived": as_bool(raw.get("archived")),
        "legacyPayload": raw,
        "schemaVersion": SCHEMA_VERSION,
    }
    return product_id, category, normalized


def normalize_status(value: Any) -> tuple[str, str | None]:
    """Normalize a legacy order status while preserving its original value."""
    mapping = {"New": "new", "Processing": "processing", "Delivered": "delivered"}
    legacy = str(value or "new")
    status = mapping.get(legacy, legacy.lower())
    valid = {"new", "confirmed", "awaiting_supply", "processing", "ready_to_ship", "shipped", "delivered", "cancelled", "returned"}
    if status not in valid:
        status = "new"
    return status, legacy if status != legacy else None


def normalize_item(item: dict[str, Any], product_ids: set[str], order_id: str) -> dict[str, Any]:
    """Validate and normalize one historical order item snapshot."""
    product_id = str(item.get("id", "")).strip()
    if product_id not in product_ids:
        raise ImportValidationError(f"order {order_id} references unknown product {product_id!r}")
    quantity = as_int(item.get("qty", 0))
    if quantity <= 0:
        raise ImportValidationError(f"order {order_id} has invalid quantity for {product_id}")
    minimum = min(1, max(0, as_int(item.get("lead_time_min_days", 0))))
    maximum = min(1, max(minimum, as_int(item.get("lead_time_max_days", item.get("lead_time_days", 0)))))
    return {
        "id": product_id,
        "title": str(item.get("title", "")),
        "img": str(item.get("img", "")),
        "price": max(0, as_int(item.get("price"))),
        "quantity": quantity,
        "purchase_purpose": str(item.get("purchase_purpose", "")),
        "availability_type": str(item.get("availability_type", "")),
        "lead_time_min_days": minimum,
        "lead_time_max_days": maximum,
        "legacyPayload": item,
    }


def build_plan(source: dict[str, Any], source_hash: str, batch_id: str, imported_at: str) -> list[DocumentPlan]:
    """Build all Firestore documents from one validated local JSON source."""
    plans: list[DocumentPlan] = []
    seen_products: set[str] = set()
    products: list[dict[str, Any]] = []
    category_names: set[str] = set()
    for raw in source.get("products", []):
        if not isinstance(raw, dict):
            raise ImportValidationError("products must contain objects")
        product_id, category, normalized = validate_product(raw, seen_products)
        category_names.add(category)
        normalized["createdAt"] = timestamp_value(imported_at)
        normalized["updatedAt"] = timestamp_value(imported_at)
        plans.append(DocumentPlan(f"products/{product_id}", fields(normalized), "products", product_id))
        products.append(normalized)

    explicit_categories = source.get("categories", [])
    if not isinstance(explicit_categories, list):
        raise ImportValidationError("categories must be a list")
    for raw_category in explicit_categories:
        if isinstance(raw_category, dict):
            name = str(raw_category.get("name", "")).strip()
        else:
            name = str(raw_category).strip()
        if name:
            category_names.add(name)
    for sort_order, name in enumerate(sorted(category_names), start=1):
        category_id = category_slug(name)
        plans.append(
            DocumentPlan(
                f"categories/{category_id}",
                fields({
                    "name": name,
                    "sortOrder": sort_order,
                    "active": True,
                    "legacyValue": name,
                    "schemaVersion": SCHEMA_VERSION,
                }),
                "categories",
                name,
            )
        )

    delivery_fees = source.get("delivery_fees", [])
    if not isinstance(delivery_fees, list):
        raise ImportValidationError("delivery_fees must be a list")
    for raw in delivery_fees:
        if not isinstance(raw, dict):
            raise ImportValidationError("delivery_fees must contain objects")
        number = as_int(raw.get("num"), -1)
        name = str(raw.get("name", "")).strip()
        if number < 0 or not name:
            raise ImportValidationError(f"invalid delivery fee identity: {raw!r}")
        domicile = as_int(raw.get("domicile"), -1)
        stop_desk = as_int(raw.get("stop_desk"), -1)
        active = domicile >= 0 and stop_desk >= 0
        plans.append(
            DocumentPlan(
                f"deliveryFees/{number}",
                fields({
                    "num": number,
                    "name": name,
                    "domicile": max(0, domicile),
                    "stop_desk": max(0, stop_desk),
                    "active": active,
                    "legacyNum": number,
                    "legacyPayload": raw,
                    "schemaVersion": SCHEMA_VERSION,
                }),
                "deliveryFees",
                number,
            )
        )

    settings = source.get("settings", {})
    if not isinstance(settings, dict):
        settings = {}
    features = settings.get("features", {})
    if not isinstance(features, dict):
        features = {}
    plans.append(
        DocumentPlan(
            "settings/public",
            fields({"features": features, "schemaVersion": SCHEMA_VERSION, "updatedAt": timestamp_value(imported_at)}),
            "settings",
            "public",
        )
    )

    product_ids = set(seen_products)
    seen_orders: set[str] = set()
    orders = source.get("orders", [])
    if not isinstance(orders, list):
        raise ImportValidationError("orders must be a list")
    for index, raw in enumerate(orders, start=1):
        if not isinstance(raw, dict):
            raise ImportValidationError("orders must contain objects")
        legacy_id = str(raw.get("order_id", raw.get("id", index))).strip()
        order_id = f"legacy-order-{legacy_id}"
        if order_id in seen_orders:
            raise ImportValidationError(f"duplicate order id {legacy_id!r}")
        seen_orders.add(order_id)
        status, legacy_status = normalize_status(raw.get("status"))
        personal = raw.get("personal_items") if isinstance(raw.get("personal_items"), list) else []
        gift_items = raw.get("gift_items") if isinstance(raw.get("gift_items"), list) else []
        if not personal and not gift_items:
            personal = raw.get("items") if isinstance(raw.get("items"), list) else []
        normalized_items: list[dict[str, Any]] = []
        for item in personal:
            if isinstance(item, dict):
                normalized = normalize_item(item, product_ids, order_id)
                normalized["item_role"] = "personal"
                normalized_items.append(normalized)
        for item in gift_items:
            if isinstance(item, dict):
                normalized = normalize_item(item, product_ids, order_id)
                normalized["item_role"] = "gift"
                normalized_items.append(normalized)
        gift = raw.get("gift") if isinstance(raw.get("gift"), dict) else None
        gift_groups = []
        if gift is not None:
            gift_groups.append({
                "source": str(gift.get("source", "")),
                "sender_name": str(gift.get("sender_name", "")),
                "recipient_name": str(gift.get("recipient_name", "")),
                "recipient_phone": str(gift.get("recipient_phone", "")),
                "recipient_type": str(gift.get("recipient_type", "")),
                "message": str(gift.get("message", "")),
                "occasion": str(gift.get("occasion", "")),
                "mood": str(gift.get("mood", "")),
                "budget": None if gift.get("budget") in (None, "") else max(0, as_int(gift.get("budget"))),
                "anonymous": as_bool(gift.get("anonymous")),
                "gift_item_ids": gift.get("gift_item_ids", []) if isinstance(gift.get("gift_item_ids", []), list) else [],
                "legacyPayload": gift,
            })
        legacy_status_field = {"legacyStatus": legacy_status} if legacy_status is not None else {}
        order_fields = {
            "id": order_id,
            "legacyOrderId": legacy_id,
            "status": status,
            **legacy_status_field,
            "items": normalized_items,
            "giftGroups": gift_groups,
            "customer": {
                "name": str(raw.get("customer_name", "")),
                "phone": str(raw.get("phone", "")),
                "address": str(raw.get("address", "")),
            },
            "delivery": {
                "wilaya": str(raw.get("wilaya", "")),
                "type": str(raw.get("delivery_type", "")),
                "fee": max(0, as_int(raw.get("delivery_fee"))),
            },
            "subtotal": max(0, as_int(raw.get("subtotal"))),
            "deliveryFee": max(0, as_int(raw.get("delivery_fee"))),
            "total": max(0, as_int(raw.get("total"))),
            "currency": "DZD",
            "idempotencyKey": None,
            "source": "legacy-pythonanywhere",
            "shippingPolicy": str(raw.get("shipping_policy", "")),
            "fulfillmentNote": str(raw.get("fulfillment_note", "")),
            "legacyPayload": raw,
            "schemaVersion": SCHEMA_VERSION,
            "createdAt": timestamp_value(source_timestamp(raw.get("timestamp"), imported_at)),
            "updatedAt": timestamp_value(imported_at),
        }
        plans.append(DocumentPlan(f"orders/{order_id}", fields(order_fields), "orders", legacy_id))

    counts = {
        "products": len(products),
        "categories": len(category_names),
        "deliveryFees": len(delivery_fees),
        "orders": len(seen_orders),
        "settings": 1,
    }
    fingerprints = {
        collection: sha256_json(sorted((plan.path, plan.fields) for plan in plans if plan.collection == collection))
        for collection in sorted({plan.collection for plan in plans})
    }
    metadata = {
        "batchId": batch_id,
        "sourceFileSha256": source_hash,
        "sourceCounts": counts,
        "targetCounts": counts,
        "sourceRecordFingerprints": fingerprints,
        "targetRecordFingerprints": fingerprints,
        "status": "planned",
        "startedAt": timestamp_value(imported_at),
        "toolVersion": TOOL_VERSION,
        "schemaVersion": SCHEMA_VERSION,
    }
    plans.append(DocumentPlan(f"migrationMetadata/{batch_id}", fields(metadata), "migrationMetadata", batch_id))
    return plans


def rest_base(project: str, emulator_host: str | None) -> str:
    """Build a Firestore REST document base URL for Emulator or Google APIs."""
    if emulator_host:
        return f"http://{emulator_host}/v1/projects/{project}/databases/(default)/documents"
    return f"https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents"


def http_json(method: str, url: str, body: dict[str, Any] | None, headers: dict[str, str]) -> tuple[int, dict[str, Any] | None]:
    """Perform one JSON HTTP request and return status plus decoded body."""
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method=method, headers={"Accept": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            decoded = json.loads(raw.decode("utf-8")) if raw else None
        except json.JSONDecodeError:
            decoded = {"raw": raw.decode("utf-8", errors="replace")}
        return error.code, decoded
    except urllib.error.URLError as error:
        raise TargetWriteError(f"target request failed: {error.reason}") from error


def document_url(base: str, path: str) -> str:
    """Return a URL for one Firestore document path."""
    return f"{base}/{urllib.parse.quote(path, safe='/')}"


def create_url(base: str, path: str) -> str:
    """Return the Firestore REST create-document URL for a document path."""
    parts = path.split("/")
    parent = "/".join(parts[:-1])
    document_id = urllib.parse.quote(parts[-1], safe="")
    return f"{base}/{urllib.parse.quote(parent, safe='/')}?documentId={document_id}"


def apply_plan(plans: list[DocumentPlan], project: str, emulator_host: str | None, token: str | None, allow_existing: bool) -> None:
    """Create planned documents after a fail-closed existence preflight."""
    base = rest_base(project, emulator_host)
    headers = {"Content-Type": "application/json"}
    if emulator_host:
        headers["Authorization"] = "Bearer owner"
    elif token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        raise TargetWriteError("FIRESTORE_ACCESS_TOKEN is required for REST apply")

    if not allow_existing:
        for plan in plans:
            status, payload = http_json("GET", document_url(base, plan.path), None, headers)
            if status == 200:
                raise TargetWriteError(f"refusing existing target document: {plan.path}")
            if status not in {404, 403}:
                raise TargetWriteError(f"preflight failed for {plan.path}: HTTP {status} {payload}")

    for plan in plans:
        status, payload = http_json("POST", create_url(base, plan.path), {"fields": plan.fields}, headers)
        if status not in {200, 201}:
            raise TargetWriteError(f"create failed for {plan.path}: HTTP {status} {payload}")


def write_plan(report_dir: Path, source_path: Path, source_hash: str, batch_id: str, plans: list[DocumentPlan]) -> None:
    """Write an inspectable NDJSON plan and manifest."""
    report_dir.mkdir(parents=True, exist_ok=True)
    plan_path = report_dir / "firestore-import.ndjson"
    with plan_path.open("w", encoding="utf-8") as handle:
        for plan in plans:
            handle.write(canonical_json({"path": plan.path, "collection": plan.collection, "legacyId": plan.legacy_id, "fields": plan.fields}) + "\n")
    counts: dict[str, int] = {}
    for plan in plans:
        counts[plan.collection] = counts.get(plan.collection, 0) + 1
    manifest = {
        "batchId": batch_id,
        "toolVersion": TOOL_VERSION,
        "sourcePath": str(source_path),
        "sourceFileSha256": source_hash,
        "documentCount": len(plans),
        "targetCounts": counts,
        "planSha256": sha256_bytes(plan_path.read_bytes()),
        "mode": "plan",
    }
    (report_dir / "manifest.json").write_text(canonical_json(manifest) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse safe-by-default importer arguments."""
    parser = argparse.ArgumentParser(description="Build or explicitly apply a Baak Books Firestore migration plan.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Local JSON source; never a PythonAnywhere path.")
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--batch-id", default="", help="Stable migration batch identifier.")
    parser.add_argument("--apply", action="store_true", help="Apply documents after preflight; otherwise plan only.")
    parser.add_argument("--target", choices=("emulator", "rest"), default="emulator")
    parser.add_argument("--project", default="demo-baakbook")
    parser.add_argument("--emulator-host", default="127.0.0.1:8080")
    parser.add_argument("--allow-existing", action="store_true", help="Disable create-only protection; forbidden for live REST mode.")
    parser.add_argument("--confirm-live", action="store_true", help="Required for any production REST apply.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Validate, write, and optionally apply one Firestore migration plan."""
    args = parse_args(argv or sys.argv[1:])
    source_path = args.source.resolve()
    if not source_path.is_file():
        raise ImportValidationError(f"source file does not exist: {source_path}")
    if "pythonanywhere" in str(source_path).lower():
        raise ImportValidationError("PythonAnywhere paths are forbidden; use a reviewed local export")
    raw_source = source_path.read_bytes()
    source_hash = sha256_bytes(raw_source)
    try:
        source = json.loads(raw_source.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ImportValidationError(f"source is not valid UTF-8 JSON: {error}") from error
    if not isinstance(source, dict):
        raise ImportValidationError("source root must be an object")

    imported_at = now_iso()
    batch_id = args.batch_id.strip() or f"migration-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    plans = build_plan(source, source_hash, batch_id, imported_at)
    report_dir = args.report_root / batch_id
    write_plan(report_dir, source_path, source_hash, batch_id, plans)

    if args.apply:
        if args.target == "rest":
            if args.project != EXPECTED_PRODUCTION_PROJECT:
                raise TargetWriteError(f"live REST target must be {EXPECTED_PRODUCTION_PROJECT}, got {args.project}")
            if not args.confirm_live:
                raise TargetWriteError("live REST apply requires --confirm-live")
            if args.allow_existing:
                raise TargetWriteError("--allow-existing is forbidden for live REST apply")
            apply_plan(plans, args.project, None, os.environ.get("FIRESTORE_ACCESS_TOKEN"), False)
        else:
            apply_plan(plans, args.project, args.emulator_host, None, args.allow_existing)
        print(f"APPLIED: {len(plans)} documents to {args.target}:{args.project}; plan={report_dir}")
    else:
        print(f"PLAN ONLY: {len(plans)} documents; source_sha256={source_hash}; plan={report_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportValidationError, TargetWriteError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
