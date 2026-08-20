"""Verify a Firestore REST/Emulator target against an NDJSON migration plan."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    """Serialize JSON deterministically."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decode_value(value: dict[str, Any]) -> Any:
    """Decode a Firestore REST Value."""
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
    if "arrayValue" in value:
        return [decode_value(item) for item in value.get("arrayValue", {}).get("values", [])]
    if "mapValue" in value:
        return {key: decode_value(item) for key, item in value.get("mapValue", {}).get("fields", {}).items()}
    raise ValueError(f"unknown Firestore value shape: {value!r}")


def decode_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Decode a Firestore document field map."""
    return {key: decode_value(value) for key, value in fields.items()}


def get_document(base: str, path: str) -> tuple[int, dict[str, Any] | None]:
    """Read one Firestore document."""
    url = f"{base}/{urllib.parse.quote(path, safe='/')}"
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "Authorization": "Bearer owner"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            return response.status, json.loads(body.decode("utf-8")) if body else None
    except urllib.error.HTTPError as error:
        return error.code, None


def verify(plan_path: Path, base: str) -> dict[str, Any]:
    """Compare every plan document with the target document."""
    errors: list[str] = []
    checked = 0
    for line_number, line in enumerate(plan_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        path = str(record["path"])
        expected = decode_fields(record["fields"])
        status, target = get_document(base, path)
        if status != 200 or target is None:
            errors.append(f"missing target document at line {line_number}: {path} (HTTP {status})")
            continue
        actual = decode_fields(target.get("fields", {}))
        if canonical(actual) != canonical(expected):
            errors.append(f"target drift for {path}")
        checked += 1
    return {"status": "verified" if not errors else "failed", "checked": checked, "errors": errors}


def main() -> int:
    """Run target verification and exit non-zero on drift."""
    parser = argparse.ArgumentParser(description="Verify a Firestore target against a plan.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--project", default="demo-baakbook")
    parser.add_argument("--emulator-host", default="127.0.0.1:8080")
    args = parser.parse_args()
    base = f"http://{args.emulator_host}/v1/projects/{args.project}/databases/(default)/documents"
    result = verify(args.plan, base)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
