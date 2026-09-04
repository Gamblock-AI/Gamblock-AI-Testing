#!/usr/bin/env python3
"""Validate privacy-safe Phase 4 latency evidence and enforce its local gate."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from itertools import product
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
    "product_flavor",
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
GROUP_IDENTITY_FIELDS = (
    "platform",
    "product_flavor",
    "device_alias",
    "scenario",
    "browser_family",
    "build_mode",
    "model_version",
    "ruleset_version",
)
SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


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
        elif SAFE_LABEL_PATTERN.fullmatch(record[field]) is None:
            errors.append(f"{prefix}: {field} must be a safe opaque label")
    if "product_flavor" in record:
        if not isinstance(record["product_flavor"], str) or not record["product_flavor"]:
            errors.append(f"{prefix}: product_flavor must be a non-empty string when present")
        elif SAFE_LABEL_PATTERN.fullmatch(record["product_flavor"]) is None:
            errors.append(f"{prefix}: product_flavor must be a safe opaque label")
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


def required_coverage(
    platforms: tuple[str, ...],
    product_flavors: tuple[str, ...],
    browsers: tuple[str, ...],
    build_modes: tuple[str, ...],
    scenarios: tuple[str, ...],
) -> list[dict[str, str]]:
    dimensions = [
        ("platform", platforms),
        ("product_flavor", product_flavors),
        ("browser_family", browsers),
        ("build_mode", build_modes),
        ("scenario", scenarios),
    ]
    configured = [(field, values) for field, values in dimensions if values]
    if not configured:
        return []
    return [
        dict(zip((field for field, _ in configured), values, strict=True))
        for values in product(*(values for _, values in configured))
    ]


def matches_scope(
    record: dict[str, Any],
    platforms: tuple[str, ...],
    product_flavors: tuple[str, ...],
    browsers: tuple[str, ...],
    build_modes: tuple[str, ...],
    scenarios: tuple[str, ...],
) -> bool:
    return (
        (not platforms or record["platform"] in platforms)
        and (not product_flavors or record.get("product_flavor") in product_flavors)
        and (not browsers or record["browser_family"] in browsers)
        and (not build_modes or record["build_mode"] in build_modes)
        and (not scenarios or record["scenario"] in scenarios)
    )


def report(
    records: list[dict[str, Any]],
    minimum_samples: int,
    target_ms: float,
    required_platforms: tuple[str, ...] = (),
    required_product_flavors: tuple[str, ...] = (),
    required_browsers: tuple[str, ...] = (),
    required_build_modes: tuple[str, ...] = (),
    required_scenarios: tuple[str, ...] = (),
    minimum_passing_groups: int = 1,
    require_all_scoped_groups: bool = True,
) -> dict[str, Any]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    scoped_records = [
        record for record in records
        if matches_scope(
            record,
            required_platforms,
            required_product_flavors,
            required_browsers,
            required_build_modes,
            required_scenarios,
        )
    ]
    for record in scoped_records:
        grouped[tuple(record.get(field, "unrecorded") for field in GROUP_IDENTITY_FIELDS)].append(record)
    groups: list[dict[str, Any]] = []
    for identity, rows in sorted(grouped.items()):
        successful = [row["input_to_visible_ms"] for row in rows if row["outcome"] == "visible" and row["block_succeeded"]]
        failures = [row["outcome"] for row in rows if row["outcome"] != "visible" or not row["block_succeeded"]]
        item = dict(zip(GROUP_IDENTITY_FIELDS, identity, strict=True))
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
    expected_coverage = required_coverage(
        required_platforms,
        required_product_flavors,
        required_browsers,
        required_build_modes,
        required_scenarios,
    )
    missing_coverage = [
        item for item in expected_coverage
        if not any(all(group[field] == value for field, value in item.items()) for group in groups)
    ]
    coverage_complete = not missing_coverage
    passing_group_count = sum(group["passed"] for group in groups)
    return {
        "schema_version": 3,
        "target_metric": "input_to_visible_ms",
        "target_ms_exclusive": target_ms,
        "minimum_samples": minimum_samples,
        "minimum_passing_groups": minimum_passing_groups,
        "require_all_scoped_groups": require_all_scoped_groups,
        "scoped_record_count": len(scoped_records),
        "required_coverage": expected_coverage,
        "missing_coverage": missing_coverage,
        "coverage_complete": coverage_complete,
        "groups": groups,
        "passed_group_count": passing_group_count,
        "passed": (
            bool(groups)
            and coverage_complete
            and passing_group_count >= minimum_passing_groups
            and (not require_all_scoped_groups or all(group["passed"] for group in groups))
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="+", type=Path, help="Phase 4 JSONL export(s)")
    parser.add_argument("--minimum-samples", type=int, default=30)
    parser.add_argument("--target-ms", type=float, default=200.0)
    parser.add_argument("--required-platform", action="append", default=[])
    parser.add_argument("--required-product-flavor", action="append", default=[])
    parser.add_argument("--required-browser", action="append", default=[])
    parser.add_argument("--required-build-mode", action="append", default=[])
    parser.add_argument("--required-scenario", action="append", default=[])
    parser.add_argument("--minimum-passing-groups", type=int, default=1)
    parser.add_argument("--allow-failing-scoped-groups", action="store_true")
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path")
    args = parser.parse_args()
    if (
        args.minimum_samples < 1
        or args.minimum_passing_groups < 1
        or not math.isfinite(args.target_ms)
        or args.target_ms <= 0
    ):
        parser.error("sample and passing-group minimums must be positive and target ms must be finite and positive")
    records, errors = load_records(args.evidence)
    result = report(
        records,
        args.minimum_samples,
        args.target_ms,
        tuple(args.required_platform),
        tuple(args.required_product_flavor),
        tuple(args.required_browser),
        tuple(args.required_build_mode),
        tuple(args.required_scenario),
        args.minimum_passing_groups,
        not args.allow_failing_scoped_groups,
    ) if not errors else {"passed": False, "errors": errors}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
