#!/usr/bin/env python3
"""Validate privacy-safe Android Research tamper evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ALLOWED_FIELDS = {
    "schema_version",
    "report_kind",
    "run_id",
    "sample_id",
    "device_alias",
    "oem_family",
    "android_api",
    "flavor",
    "build_mode",
    "scenario",
    "surface",
    "action",
    "observed_action",
    "expected_outcome",
    "actual_outcome",
    "result",
    "grant_state",
    "admin_active_before",
    "admin_active_after",
    "accessibility_enabled_before",
    "accessibility_enabled_after",
    "service_running_before",
    "service_running_after",
    "app_present_after",
    "recovery_within_seconds",
    "evidence_reference",
    "failure_code",
    "visual_evidence_present",
    "visual_evidence_sha256",
}

REQUIRED_FIELDS = {
    "schema_version",
    "report_kind",
    "run_id",
    "sample_id",
    "device_alias",
    "oem_family",
    "android_api",
    "flavor",
    "build_mode",
    "scenario",
    "surface",
    "action",
    "observed_action",
    "expected_outcome",
    "actual_outcome",
    "result",
    "grant_state",
    "admin_active_before",
    "admin_active_after",
    "accessibility_enabled_before",
    "accessibility_enabled_after",
    "service_running_before",
    "service_running_after",
    "app_present_after",
    "evidence_reference",
    "visual_evidence_present",
}

ENUMS = {
    "oem_family": {"aosp", "samsung", "xiaomi_redmi", "oppo_realme", "vivo", "other"},
    "flavor": {"research"},
    "build_mode": {"debug", "profile", "release"},
    "scenario": {
        "setup",
        "app_info_passive",
        "launcher_uninstall",
        "settings_uninstall",
        "package_installer_uninstall",
        "disable_accessibility",
        "force_stop",
        "clear_data",
        "process_kill",
        "reboot",
        "valid_grant_removal",
        "invalid_grant_removal",
        "other_app_uninstall",
    },
    "surface": {
        "none",
        "launcher",
        "settings",
        "package_installer",
        "accessibility_settings",
        "app_info",
    },
    "action": {
        "none",
        "uninstall",
        "disable_accessibility",
        "force_stop",
        "clear_data",
        "process_kill",
        "reboot",
    },
    "observed_action": {
        "none",
        "uninstall",
        "disable_accessibility",
        "force_stop",
        "clear_data",
    },
    "expected_outcome": {
        "blocked",
        "warned",
        "degraded",
        "recovered",
        "allowed",
        "no_tamper",
        "not_applicable",
    },
    "actual_outcome": {
        "blocked",
        "warned",
        "degraded",
        "recovered",
        "allowed",
        "no_tamper",
        "not_applicable",
        "failed",
        "pending",
    },
    "result": {"passed", "failed", "pending"},
    "grant_state": {"none", "valid", "invalid", "expired", "wrong_device"},
}

BOOL_FIELDS = {
    "admin_active_before",
    "admin_active_after",
    "accessibility_enabled_before",
    "accessibility_enabled_after",
    "service_running_before",
    "service_running_after",
    "app_present_after",
    "visual_evidence_present",
}
LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
UNAPPROVED_REMOVAL_SCENARIOS = {
    "invalid_grant_removal",
    "launcher_uninstall",
    "settings_uninstall",
    "package_installer_uninstall",
}


def _required_string(record: dict[str, Any], field: str, prefix: str) -> list[str]:
    if not isinstance(record.get(field), str) or not record[field]:
        return [f"{prefix}: {field} must be a non-empty string"]
    if not LABEL_PATTERN.fullmatch(record[field]):
        return [f"{prefix}: {field} must be an ASCII label of 1-64 characters"]
    return []


def validate_record(record: Any, source: str, line_number: int) -> list[str]:
    """Return validation errors for one privacy-safe JSONL record."""

    prefix = f"{source}:{line_number}"
    if not isinstance(record, dict):
        return [f"{prefix}: record must be an object"]

    errors: list[str] = []
    unexpected = set(record) - ALLOWED_FIELDS
    if unexpected:
        errors.append(f"{prefix}: privacy allowlist rejected fields {sorted(unexpected)}")

    missing = REQUIRED_FIELDS - set(record)
    if missing:
        errors.append(f"{prefix}: missing required fields {sorted(missing)}")

    if record.get("schema_version") != 2:
        errors.append(f"{prefix}: schema_version must be 2")
    if record.get("report_kind") != "android_tamper_run":
        errors.append(f"{prefix}: report_kind must be android_tamper_run")

    for field in (
        "run_id",
        "sample_id",
        "device_alias",
        "flavor",
        "build_mode",
        "scenario",
        "surface",
        "action",
        "observed_action",
        "expected_outcome",
        "actual_outcome",
        "result",
        "grant_state",
        "evidence_reference",
    ):
        errors.extend(_required_string(record, field, prefix))

    android_api = record.get("android_api")
    if isinstance(android_api, bool) or not isinstance(android_api, int) or not 21 <= android_api <= 99:
        errors.append(f"{prefix}: android_api must be an integer between 21 and 99")

    for field, choices in ENUMS.items():
        value = record.get(field)
        if isinstance(value, str) and value not in choices:
            errors.append(f"{prefix}: {field} must be one of {sorted(choices)}")

    for field in BOOL_FIELDS:
        if not isinstance(record.get(field), bool):
            errors.append(f"{prefix}: {field} must be boolean")

    visual_hash = record.get("visual_evidence_sha256")
    if visual_hash is not None and (
        not isinstance(visual_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", visual_hash) is None
    ):
        errors.append(f"{prefix}: visual_evidence_sha256 must be a lowercase SHA-256 digest")
    if visual_hash is not None and record.get("visual_evidence_present") is not True:
        errors.append(f"{prefix}: a visual hash requires visual_evidence_present=true")

    recovery = record.get("recovery_within_seconds")
    if recovery is not None and (
        isinstance(recovery, bool)
        or not isinstance(recovery, (int, float))
        or not math.isfinite(recovery)
        or recovery < 0
    ):
        errors.append(f"{prefix}: recovery_within_seconds must be finite and non-negative")

    if record.get("result") == "failed" and not record.get("failure_code"):
        errors.append(f"{prefix}: failed records require failure_code")
    if record.get("failure_code") is not None and (
        not isinstance(record["failure_code"], str) or not record["failure_code"]
    ):
        errors.append(f"{prefix}: failure_code must be a non-empty string when present")
    elif record.get("failure_code") is not None and not LABEL_PATTERN.fullmatch(record["failure_code"]):
        errors.append(f"{prefix}: failure_code must be an ASCII label of 1-64 characters")

    scenario = record.get("scenario")
    grant_state = record.get("grant_state")
    app_present = record.get("app_present_after")
    if scenario == "valid_grant_removal" and grant_state != "valid":
        errors.append(f"{prefix}: valid_grant_removal requires grant_state=valid")
    if scenario == "invalid_grant_removal" and grant_state == "valid":
        errors.append(f"{prefix}: invalid_grant_removal cannot use grant_state=valid")
    if scenario == "valid_grant_removal" and record.get("result") == "passed":
        if (
            record.get("actual_outcome") != "allowed"
            or app_present is not False
            or record.get("admin_active_before") is not True
            or record.get("admin_active_after") is not False
        ):
            errors.append(
                f"{prefix}: passed valid removal requires allowed, admin transition, and app_present_after=false"
            )
    if scenario in UNAPPROVED_REMOVAL_SCENARIOS:
        if record.get("result") == "passed" and record.get("admin_active_before") is not True:
            errors.append(f"{prefix}: passed unapproved removal requires admin_active_before=true")
        if grant_state != "valid" and record.get("result") == "passed" and app_present is not True:
            errors.append(f"{prefix}: unapproved removal must leave app_present_after=true")

    if scenario in {"app_info_passive", "other_app_uninstall"} and record.get("result") == "passed":
        if record.get("observed_action") != "none" or record.get("actual_outcome") != "no_tamper":
            errors.append(f"{prefix}: passive/non-target scenario must produce no_tamper")

    if scenario == "disable_accessibility" and record.get("result") == "passed":
        if record.get("accessibility_enabled_after") is not False:
            errors.append(f"{prefix}: passed disable_accessibility must end with accessibility disabled")

    if scenario in {"process_kill", "force_stop", "reboot"} and record.get("result") == "passed":
        if record.get("service_running_after") is not True:
            errors.append(f"{prefix}: passed lifecycle recovery must end with service_running_after=true")

    return errors


def load_records(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    sample_ids: dict[str, str] = {}
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
            if not record_errors:
                sample_id = record["sample_id"]
                previous = sample_ids.get(sample_id)
                if previous is not None:
                    errors.append(
                        f"{path}:{line_number}: duplicate sample_id {sample_id!r}; already present in {previous}"
                    )
                else:
                    sample_ids[sample_id] = f"{path}:{line_number}"
                    records.append(record)
    return records, errors


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        identity = (
            record["device_alias"],
            record["oem_family"],
            record["android_api"],
            record["scenario"],
            record["surface"],
            record["action"],
        )
        groups[identity].append(record)

    summary_groups: list[dict[str, Any]] = []
    for identity, rows in sorted(groups.items()):
        device_alias, oem_family, android_api, scenario, surface, action = identity
        results = {row["result"] for row in rows}
        summary_groups.append(
            {
                "device_alias": device_alias,
                "oem_family": oem_family,
                "android_api": android_api,
                "scenario": scenario,
                "surface": surface,
                "action": action,
                "sample_count": len(rows),
                "passed_count": sum(row["result"] == "passed" for row in rows),
                "failed_count": sum(row["result"] == "failed" for row in rows),
                "pending_count": sum(row["result"] == "pending" for row in rows),
                "results": sorted(results),
                "passed": results == {"passed"},
            }
        )

    return {
        "schema_version": 2,
        "report_kind": "android_tamper_summary",
        "group_count": len(summary_groups),
        "sample_count": len(records),
        "groups": summary_groups,
        "passed": bool(records) and all(group["passed"] for group in summary_groups),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="+", type=Path, help="Android tamper JSONL export(s)")
    parser.add_argument("--output", type=Path, help="Write the aggregate summary to this path")
    args = parser.parse_args()

    records, errors = load_records(args.evidence)
    result: dict[str, Any]
    if errors:
        result = {"schema_version": 2, "report_kind": "android_tamper_summary", "passed": False, "errors": errors}
    else:
        result = summarize(records)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
