"""Profile legacy JSON field shapes for the local D1 migration.

ADR: LegacyFieldProfiler
========================
Problem:
    The source store is a flexible JSON document whose nested order and settings
    fields must be understood before choosing stable SQL columns.
Decision:
    Produce a read-only, deterministic field/type profile. The profiler never
    mutates source data and never contacts an external service.
Consequences:
    The report makes schema decisions auditable, while uncommon nested fields can
    remain in JSON-compatible metadata columns during the first migration.
"""

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


def profile_records(records: list[Any]) -> dict[str, Any]:
    """Profile top-level keys and their observed JSON types."""
    keys: Counter[str] = Counter()
    types: dict[str, Counter[str]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        for key, value in record.items():
            keys[key] += 1
            types.setdefault(key, Counter())[type_name(value)] += 1
    return {
        "record_count": len(records),
        "keys": dict(sorted(keys.items())),
        "types": {key: dict(sorted(counter.items())) for key, counter in sorted(types.items())},
    }


def profile(source_path: Path) -> dict[str, Any]:
    """Build a read-only field profile for the legacy source."""
    with source_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return {
        "source_file": str(source_path),
        "top_level_keys": sorted(payload.keys()),
        "products": profile_records(payload.get("products", [])),
        "orders": profile_records(payload.get("orders", [])),
        "categories": profile_records(payload.get("categories", [])),
        "delivery_fees": profile_records(payload.get("delivery_fees", [])),
        "settings": {
            "top_level": profile_records([payload.get("settings", {})]),
            "feature_flags": profile_records([payload.get("settings", {}).get("features", {})]),
        },
    }


def main() -> None:
    """Write a deterministic field profile report."""
    parser = argparse.ArgumentParser(description="Profile legacy Baak Books JSON fields.")
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = profile(args.source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
