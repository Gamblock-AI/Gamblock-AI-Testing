#!/usr/bin/env python3
"""Validate privacy-safe Phase 4 latency evidence and enforce its local gate."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ALLOWED_FIELDS = {
    "schema_version",
    "platform",
    "run_id",
    "sample_id",
    "device_alias",
    "scenario",
    "browser_family",
    "build_mode",
    "model_version",
    "ruleset_version",
    "outcome",
    "presentation_path",
    "block_succeeded",
    "extraction_ms",
    "relay_ms",
    "queue_ms",
    "preprocessing_ms",
    "rule_ms",
    "inference_ms",
    "decision_ms",
    "classification_ms",
    "block_action_ms",
    "dispatch_to_visible_ms",
    "input_to_visible_ms",
    "scan_to_visible_ms",
}
IDENTITY_FIELDS = (
    "platform",
    "device_alias",
    "scenario",
    "browser_family",
    "build_mode",
    "model_version",
    "ruleset_version",
)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def duration_summary(values: list[float]) -> dict[str, float]:
    return {
        "median_ms": percentile(values, 0.50),
        "p95_ms": percentile(values, 0.95),
        "p99_ms": percentile(values, 0.99),
        "maximum_ms": max(values),
    }


def validate_record(record: Any, source: str, line_number: int) -> list[str]:
    prefix = f"{source}:{line_number}"
    if not isinstance(record, dict):
        return [f"{prefix}: record must be an object"]
    errors: list[str] = []
    unexpected = set(record) - ALLOWED_FIELDS
    if unexpected:
        errors.append(f"{prefix}: privacy allowlist rejected fields {sorted(unexpected)}")
    if record.get("schema_version") != 3:
        errors.append(f"{prefix}: schema_version must be 3")
    for field in IDENTITY_FIELDS + ("run_id", "sample_id", "outcome", "presentation_path"):
        if not isinstance(record.get(field), str) or not record[field]:
            errors.append(f"{prefix}: {field} must be a non-empty string")
    if not isinstance(record.get("block_succeeded"), bool):
        errors.append(f"{prefix}: block_succeeded must be boolean")
    for field, value in record.items():
        if field.endswith("_ms") and (
            isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0
        ):
            errors.append(f"{prefix}: {field} must be a finite non-negative number")
    if record.get("outcome") == "visible" and "input_to_visible_ms" not in record:
        errors.append(f"{prefix}: visible samples require input_to_visible_ms")
    return errors


def load_records(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            errors.append(f"{path}: cannot read evidence: {error}")
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{path}:{line_number}: invalid JSON: {error.msg}")
                continue
            record_errors = validate_record(record, str(path), line_number)
            errors.extend(record_errors)
            if not record_errors and isinstance(record, dict):
                records.append(record)
    return records, errors


def report(records: list[dict[str, Any]], minimum_samples: int, target_ms: float) -> dict[str, Any]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[field] for field in IDENTITY_FIELDS)].append(record)
    groups: list[dict[str, Any]] = []
    for identity, rows in sorted(grouped.items()):
        successful = [row["input_to_visible_ms"] for row in rows if row["outcome"] == "visible" and row["block_succeeded"]]
        failures = [row["outcome"] for row in rows if row["outcome"] != "visible" or not row["block_succeeded"]]
        item = dict(zip(IDENTITY_FIELDS, identity, strict=True))
        item["sample_count"] = len(successful)
        item["failure_count"] = len(failures)
        item["outcomes"] = sorted(set(failures))
        if successful:
            item.update(duration_summary(successful))
        item["passed"] = (
            len(successful) >= minimum_samples and
            not failures and
            bool(successful) and
            item["p95_ms"] < target_ms
        )
        groups.append(item)
    return {
        "schema_version": 1,
        "target_metric": "input_to_visible_ms",
        "target_ms_exclusive": target_ms,
        "minimum_samples": minimum_samples,
        "groups": groups,
        "passed": bool(groups) and all(group["passed"] for group in groups),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="+", type=Path, help="Phase 4 JSONL export(s)")
    parser.add_argument("--minimum-samples", type=int, default=30)
    parser.add_argument("--target-ms", type=float, default=200.0)
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path")
    args = parser.parse_args()
    if args.minimum_samples < 1 or not math.isfinite(args.target_ms) or args.target_ms <= 0:
        parser.error("minimum samples must be positive and target ms must be finite and positive")
    records, errors = load_records(args.evidence)
    result = report(records, args.minimum_samples, args.target_ms) if not errors else {"passed": False, "errors": errors}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
