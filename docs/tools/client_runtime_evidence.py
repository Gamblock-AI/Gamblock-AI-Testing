#!/usr/bin/env python3
"""Validate and aggregate the public Flutter client-runtime evidence contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
PLATFORMS = ("android", "windows")
CASES = ("gambling", "non_gambling")
FORBIDDEN_KEYS = {
    "url",
    "urls",
    "domain",
    "domains",
    "dom",
    "html",
    "screenshot",
    "screenshot_path",
    "device_serial",
    "serial",
    "participant",
    "participant_id",
    "token",
    "password",
    "account",
    "path",
}

COMMON_SUMMARY_FIELDS = {
    "schema_version",
    "test",
    "platform",
    "browser",
    "case",
    "device_alias",
    "build_mode",
    "product_flavor",
    "artifact",
    "run_id",
    "sample_count",
    "status",
}
COMMON_SAMPLE_FIELDS = {
    "schema_version",
    "test",
    "platform",
    "browser",
    "case",
    "device_alias",
    "build_mode",
    "product_flavor",
    "artifact",
    "run_id",
    "sample_id",
    "result",
}
BROWSER_SUMMARY_FIELDS = COMMON_SUMMARY_FIELDS | {
    "expected_outcome",
    "passed_sample_count",
}
BROWSER_SAMPLE_FIELDS = COMMON_SAMPLE_FIELDS | {"expected_outcome", "actual_outcome"}


def pending(name: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "pending", "reason": reason, **extra}


def _safe_label(value: Any) -> bool:
    return isinstance(value, str) and LABEL_PATTERN.fullmatch(value) is not None


def _forbidden_values(value: Any, location: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if str(key).lower() in FORBIDDEN_KEYS:
                errors.append(f"{child_location}: forbidden public evidence field")
            errors.extend(_forbidden_values(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_forbidden_values(child, f"{location}[{index}]"))
    elif isinstance(value, str) and re.search(r"https?://", value, re.IGNORECASE):
        errors.append(f"{location}: URL-like public evidence value")
    return errors


def _target_platforms(target: dict[str, Any], include_optional: bool = False) -> list[str]:
    platforms = list(target.get("required_platforms", PLATFORMS))
    if include_optional:
        for platform in target.get("optional_platforms", []):
            if platform not in platforms:
                platforms.append(platform)
    return platforms


def _expected_cells(
    test_name: str,
    target: dict[str, Any],
    include_optional: bool = False,
) -> list[dict[str, str]]:
    cells: list[dict[str, str]] = []
    browsers = target.get("required_browsers", {})
    for platform in _target_platforms(target, include_optional):
        for browser in browsers.get(platform, []):
            for case in CASES:
                cells.append({"platform": platform, "browser": browser, "case": case})
    return cells


def _cell_path(root: Path, cell: dict[str, str]) -> Path:
    parts = [cell["platform"]]
    if "browser" in cell:
        parts.append(cell["browser"])
    parts.append(cell["case"])
    return root.joinpath(*parts)


def _read_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)


def _read_samples(path: Path) -> tuple[list[dict[str, Any]], list[str], bool]:
    errors: list[str] = []
    samples: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [], [f"{path}: could not be read: {error}"], False
    nonempty = False
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        nonempty = True
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"{path}:{line_number}: invalid JSON: {error.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}:{line_number}: sample must be an object")
            continue
        errors.extend(_forbidden_values(value, f"{path}:{line_number}"))
        samples.append(value)
    return samples, errors, nonempty


def _required_artifact(target: dict[str, Any], platform: str) -> dict[str, Any]:
    return target.get("required_artifacts_by_platform", {}).get(platform, {})


def _validate_common(
    value: dict[str, Any],
    expected: set[str],
    cell: dict[str, str],
    target: dict[str, Any],
    location: str,
) -> list[str]:
    errors: list[str] = []
    unexpected = set(value) - expected
    if unexpected:
        errors.append(f"{location}: unexpected fields {sorted(unexpected)}")
    for field in ("schema_version", "test", "platform", "case", "device_alias", "build_mode", "artifact", "run_id"):
        if field not in value:
            errors.append(f"{location}: missing {field}")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{location}: schema_version must be {SCHEMA_VERSION}")
    if value.get("test") != target.get("test_name"):
        errors.append(f"{location}: test does not match target")
    for field, expected_value in cell.items():
        if value.get(field) != expected_value:
            errors.append(f"{location}: {field} must be {expected_value!r}")
    for field in ("device_alias", "run_id"):
        if not _safe_label(value.get(field)):
            errors.append(f"{location}: {field} must be an ASCII label")
    if value.get("build_mode") not in target.get("required_build_modes", ["release"]):
        errors.append(f"{location}: build_mode is not an allowed runtime build")
    artifact = _required_artifact(target, cell["platform"])
    if artifact:
        if value.get("product_flavor") != artifact.get("product_flavor"):
            errors.append(f"{location}: product_flavor does not match the platform artifact contract")
        if value.get("artifact") != artifact.get("artifact"):
            errors.append(f"{location}: artifact does not match the platform artifact contract")
    return errors


def _validate_cell(
    test_name: str,
    target: dict[str, Any],
    cell: dict[str, str],
    directory: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {**cell, "status": "pending", "errors": []}
    summary_path = directory / "summary.json"
    samples_path = directory / "samples.jsonl"
    if not directory.is_dir():
        result["reason"] = "required cell directory is missing"
        return result
    missing = [str(path.name) for path in (summary_path, samples_path) if not path.is_file()]
    if missing:
        result["reason"] = f"required evidence files are missing: {', '.join(missing)}"
        return result
    summary, summary_error = _read_json(summary_path)
    samples, sample_errors, nonempty = _read_samples(samples_path)
    if summary_error:
        result["status"] = "failed"
        result["errors"].append(f"{summary_path}: invalid JSON: {summary_error}")
    if sample_errors:
        result["status"] = "failed"
        result["errors"].extend(sample_errors)
    if not nonempty:
        result["reason"] = "samples.jsonl is empty"
        return result
    if not isinstance(summary, dict):
        result["status"] = "failed"
        result["errors"].append(f"{summary_path}: summary must be an object")
        return result

    summary_fields = BROWSER_SUMMARY_FIELDS
    sample_fields = BROWSER_SAMPLE_FIELDS
    target_with_name = {**target, "test_name": test_name}
    result["errors"].extend(_validate_common(summary, summary_fields, cell, target_with_name, str(summary_path)))
    for field in ("sample_count", "status"):
        if field not in summary:
            result["errors"].append(f"{summary_path}: missing {field}")
    for field in ("expected_outcome", "passed_sample_count"):
        if field not in summary:
            result["errors"].append(f"{summary_path}: missing {field}")
    expected_count = int(target.get("samples_per_class_per_browser", 0))
    result["sample_count"] = len(samples)
    if len(samples) < expected_count:
        result["reason"] = f"cell has {len(samples)} of {expected_count} required samples"
    elif len(samples) > expected_count:
        result["status"] = "failed"
        result["errors"].append(f"{samples_path}: expected exactly {expected_count} samples")
    sample_ids: set[str] = set()
    run_ids: set[str] = set()
    for index, sample in enumerate(samples, 1):
        location = f"{samples_path}:{index}"
        result["errors"].extend(_validate_common(sample, sample_fields, cell, target_with_name, location))
        unexpected = set(sample) - sample_fields
        if unexpected:
            continue
        sample_id = sample.get("sample_id")
        if not _safe_label(sample_id):
            result["errors"].append(f"{location}: sample_id must be an ASCII label")
        elif sample_id in sample_ids:
            result["errors"].append(f"{location}: duplicate sample_id {sample_id!r}")
        else:
            sample_ids.add(sample_id)
        run_ids.add(str(sample.get("run_id")))
        expected_outcome = cell["case"]
        outcome = {"gambling": "intervention", "non_gambling": "allow"}[expected_outcome]
        if sample.get("expected_outcome") != outcome:
            result["errors"].append(f"{location}: expected_outcome does not match case")
        if sample.get("actual_outcome") not in {"allow", "intervention", "error"}:
            result["errors"].append(f"{location}: actual_outcome is invalid")
        if sample.get("result") not in {"passed", "failed"}:
            result["errors"].append(f"{location}: result must be passed or failed")
    if len(run_ids) > 1:
        result["errors"].append(f"{samples_path}: a cell must contain one run_id")
    if summary.get("sample_count") != len(samples):
        result["errors"].append(f"{summary_path}: sample_count does not match samples.jsonl")
    if samples and summary.get("run_id") != samples[0].get("run_id"):
        result["errors"].append(f"{summary_path}: run_id does not match samples.jsonl")
    expected_outcome = target.get("expected_outcomes", {}).get(cell["case"])
    passed_count = sum(
        sample.get("actual_outcome") == expected_outcome and sample.get("result") == "passed"
        for sample in samples
    )
    if summary.get("expected_outcome") != expected_outcome:
        result["errors"].append(f"{summary_path}: expected_outcome does not match target")
    if summary.get("passed_sample_count") != passed_count:
        result["errors"].append(f"{summary_path}: passed_sample_count does not match samples.jsonl")
    result["run_id"] = summary.get("run_id")
    result["device_alias"] = summary.get("device_alias")
    result["artifact"] = summary.get("artifact")
    result["samples"] = samples
    if result["errors"]:
        result["status"] = "failed"
    elif len(samples) == expected_count:
        expected_result = all(sample.get("result") == "passed" for sample in samples)
        result["status"] = "passed" if expected_result else "failed"
        result["reason"] = "complete cell"
    return result


def aggregate_client_runtime(test_name: str, target: dict[str, Any], testing_root: Path) -> dict[str, Any]:
    """Return the report-safe status for one client-runtime contract."""

    evidence = target.get("evidence", {})
    relative_root = evidence.get("root")
    if not isinstance(relative_root, str) or not relative_root.startswith("flutter/evidence/client-runtime/"):
        return {"name": test_name, "status": "failed", "reason": "target has an invalid evidence root"}
    root = testing_root / relative_root
    if not root.is_dir():
        return pending(test_name, "No complete client-runtime evidence root exists.")
    required_cells = [
        _validate_cell(test_name, target, cell, _cell_path(root, cell))
        for cell in _expected_cells(test_name, target)
    ]
    optional_platforms = list(target.get("optional_platforms", []))
    optional_candidates = [
        cell
        for cell in _expected_cells(test_name, target, include_optional=True)
        if cell["platform"] in optional_platforms
    ]
    optional_has_evidence = any(
        _cell_path(root, cell).exists() for cell in optional_candidates
    )
    optional_cells = (
        [
            _validate_cell(test_name, target, cell, _cell_path(root, cell))
            for cell in optional_candidates
        ]
        if optional_has_evidence
        else []
    )
    missing_cells = sum(1 for cell in required_cells if cell["status"] == "pending")
    invalid_cells = sum(1 for cell in required_cells if cell["status"] == "failed")
    complete_cells = len(required_cells) - missing_cells - invalid_cells
    result: dict[str, Any] = {
        "name": test_name,
        "status": "pending",
        "required_cells": len(required_cells),
        "complete_cells": complete_cells,
        "missing_cells": missing_cells,
        "failed_cells": invalid_cells,
        "cells": [
            {key: value for key, value in cell.items() if key != "samples"}
            for cell in required_cells
        ],
        "optional_platforms": {},
    }

    def browser_failed_samples(cells: list[dict[str, Any]]) -> int:
        expected_outcomes = target.get("expected_outcomes", {})
        return sum(
            sample.get("actual_outcome") != expected_outcomes.get(cell["case"])
            or sample.get("result") != "passed"
            for cell in cells
            for sample in cell.get("samples", [])
        )

    for platform in optional_platforms:
        platform_cells = [cell for cell in optional_cells if cell["platform"] == platform]
        platform_result: dict[str, Any] = {
            "status": "not_run" if not optional_has_evidence else "pending",
            "required": False,
            "cells": [
                {key: value for key, value in cell.items() if key != "samples"}
                for cell in platform_cells
            ],
        }
        if not optional_has_evidence:
            platform_result["reason"] = "optional platform was not executed"
            result["optional_platforms"][platform] = platform_result
            continue
        platform_missing = sum(cell["status"] == "pending" for cell in platform_cells)
        platform_failed = sum(cell["status"] == "failed" for cell in platform_cells)
        platform_result.update(
            {
                "required_cells": len(platform_cells),
                "complete_cells": len(platform_cells) - platform_missing - platform_failed,
                "missing_cells": platform_missing,
                "failed_cells": platform_failed,
            }
        )
        if platform_failed:
            platform_result["status"] = "failed"
            platform_result["reason"] = "one or more optional evidence cells failed schema or privacy validation"
        elif platform_missing:
            platform_result["reason"] = "one or more optional evidence cells are incomplete"
        else:
            aliases = {cell.get("device_alias", "") for cell in platform_cells}
            expected_devices = int(
                target.get("optional_devices", target.get("required_devices", {})).get(platform, 1)
            )
            if len(aliases) != expected_devices:
                platform_result["status"] = "failed"
                platform_result["reason"] = (
                    f"expected {expected_devices} device alias(es) for {platform}, observed {len(aliases)}"
                )
            else:
                failed_samples = browser_failed_samples(platform_cells)
                platform_result["failed_sample_count"] = failed_samples
                platform_result["status"] = "passed" if failed_samples == 0 else "failed"
                platform_result["reason"] = (
                    "all optional browser cells complete and expected outcomes observed"
                    if failed_samples == 0
                    else "one or more optional browser outcomes failed"
                )
        result["optional_platforms"][platform] = platform_result

    if invalid_cells:
        result["status"] = "failed"
        result["reason"] = "one or more evidence cells failed schema or privacy validation"
        return result
    if missing_cells:
        result["reason"] = "one or more required evidence cells are incomplete"
        return result

    aliases_by_platform: dict[str, set[str]] = {}
    for cell in required_cells:
        aliases_by_platform.setdefault(cell["platform"], set()).add(cell.get("device_alias", ""))
    for platform, aliases in aliases_by_platform.items():
        expected_devices = int(target.get("required_devices", {}).get(platform, 1))
        if len(aliases) != expected_devices:
            result["status"] = "failed"
            result["reason"] = f"expected {expected_devices} device alias(es) for {platform}, observed {len(aliases)}"
            result["device_aliases"] = sorted(aliases)
            return result

    failed_samples = browser_failed_samples(required_cells)
    result["failed_sample_count"] = failed_samples
    result["status"] = "passed" if failed_samples == 0 else "failed"
    result["reason"] = "all browser cells complete and expected outcomes observed" if failed_samples == 0 else "one or more browser outcomes failed"
    return result


def validate_client_runtime_root(root: Path, test_name: str, target: dict[str, Any]) -> list[str]:
    """Validate all files below an evidence root without changing report status."""

    errors: list[str] = []
    if not root.exists():
        return errors
    expected_paths = {
        _cell_path(root, cell).relative_to(root)
        for cell in _expected_cells(test_name, target, include_optional=True)
    }
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        if relative.name not in {"summary.json", "samples.jsonl"} or relative.parent not in expected_paths:
            errors.append(f"{path}: unexpected client-runtime evidence file")
    aggregate = aggregate_client_runtime(test_name, target, root.parents[3])
    cells = list(aggregate.get("cells", []))
    for platform in aggregate.get("optional_platforms", {}).values():
        cells.extend(platform.get("cells", []))
    for cell in cells:
        for error in cell.get("errors", []):
            errors.append(str(error))
    return sorted(set(errors))


def configured_runtime_targets(configuration: dict[str, Any]) -> dict[str, dict[str, Any]]:
    targets = configuration.get("client_runtime", {})
    return {
        name: {**target, "test_name": name}
        for name, target in targets.items()
        if isinstance(target, dict)
    }
