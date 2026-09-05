#!/usr/bin/env python3
"""Validate all public evidence and reject raw/private artifacts."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_REPORTS = {
    "flutter/report.md",
    "golang/report.md",
    "next/report.md",
    "browser-extention/report.md",
    "model/report.md",
}
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
RAW_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".log", ".trace", ".pcap"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
MODEL_PUBLIC_AGGREGATES = {
    Path("model/evidence/aggregate/deployment_projection_evidence.json"),
    Path("model/evidence/aggregate/domain_grouped_evidence.json"),
}
MODEL_PUBLIC_VISUALS = {
    Path("model/evidence/visuals/domain_grouped_confusion_matrix.png"),
    Path("model/evidence/visuals/domain_grouped_ablation_metrics.png"),
    Path("model/evidence/visuals/domain_grouped_threshold_sensitivity.png"),
    Path("model/evidence/visuals/domain_grouped_calibration.png"),
}
DEVICE_REGISTER_FIELDS = {
    "device_alias",
    "display_name",
    "oem_family",
    "source",
    "service",
    "access_path",
    "evidence_status",
    "android_api",
    "build_mode",
    "retest_required",
}
DEVICE_REGISTER_ENUMS = {
    "oem_family": {"aosp", "samsung", "xiaomi_redmi", "oppo_realme", "vivo", "other"},
    "source": {"firebase_test_lab", "local_physical_device"},
    "service": {"firebase_test_lab_android_device_streaming", "local_physical_device"},
    "access_path": {"android_studio_remote_devices", "local_adb"},
    "evidence_status": {"valid_evidence", "pending_retest"},
    "build_mode": {"debug", "profile", "release"},
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=False,
    )
    return [ROOT / Path(item) for item in result.stdout.decode().split("\0") if item]


def forbidden_nested_values(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}.{key}" if path else key
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden public evidence field: {key_path}")
            errors.extend(forbidden_nested_values(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(forbidden_nested_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and URL_PATTERN.search(value):
        errors.append(f"URL-like public evidence value at {path}")
    return errors


def validate_device_register(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path}: invalid device register: {error}"]
    if not isinstance(value, dict):
        return [f"{path}: device register must be an object"]
    if set(value) - {"schema_version", "scope", "devices"}:
        errors.append(f"{path}: unexpected device register fields")
    if value.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must be 1")
    if value.get("scope") != "android_research_anti_uninstall":
        errors.append(f"{path}: scope must be android_research_anti_uninstall")
    devices = value.get("devices")
    if not isinstance(devices, list):
        return [*errors, f"{path}: devices must be a list"]

    aliases: set[str] = set()
    for index, device in enumerate(devices):
        prefix = f"{path}:devices[{index}]"
        if not isinstance(device, dict):
            errors.append(f"{prefix}: device must be an object")
            continue
        unexpected = set(device) - DEVICE_REGISTER_FIELDS
        if unexpected:
            errors.append(f"{prefix}: unexpected fields {sorted(unexpected)}")
        for field in ("device_alias", "display_name", "oem_family", "source", "service", "access_path", "evidence_status", "retest_required"):
            if field not in device:
                errors.append(f"{prefix}: missing {field}")
        alias = device.get("device_alias")
        if not isinstance(alias, str) or LABEL_PATTERN.fullmatch(alias) is None:
            errors.append(f"{prefix}: device_alias must be an ASCII label")
        elif alias in aliases:
            errors.append(f"{prefix}: duplicate device_alias {alias!r}")
        else:
            aliases.add(alias)
        display_name = device.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip() or "|" in display_name or "\n" in display_name:
            errors.append(f"{prefix}: display_name must be a non-empty markdown-safe string")
        for field, choices in DEVICE_REGISTER_ENUMS.items():
            if field == "build_mode" and device.get(field) is None:
                continue
            if device.get(field) not in choices:
                errors.append(f"{prefix}: {field} must be one of {sorted(choices)}")
        if device.get("source") == "firebase_test_lab" and device.get("service") != "firebase_test_lab_android_device_streaming":
            errors.append(f"{prefix}: firebase_test_lab source requires Android Device Streaming service")
        if device.get("source") == "local_physical_device" and device.get("service") != "local_physical_device":
            errors.append(f"{prefix}: local_physical_device source requires local_physical_device service")
        android_api = device.get("android_api")
        if android_api is not None and (
            isinstance(android_api, bool) or not isinstance(android_api, int) or not 21 <= android_api <= 99
        ):
            errors.append(f"{prefix}: android_api must be null or an integer between 21 and 99")
        if not isinstance(device.get("retest_required"), bool):
            errors.append(f"{prefix}: retest_required must be boolean")
        if device.get("evidence_status") == "valid_evidence" and device.get("retest_required") is not False:
            errors.append(f"{prefix}: valid_evidence requires retest_required=false")
        if device.get("evidence_status") == "pending_retest" and device.get("retest_required") is not True:
            errors.append(f"{prefix}: pending_retest requires retest_required=true")
        build_mode = device.get("build_mode")
        if build_mode is not None and build_mode not in DEVICE_REGISTER_ENUMS["build_mode"]:
            errors.append(f"{prefix}: build_mode must be null or a supported build mode")
        errors.extend(forbidden_nested_values(device, prefix))
    errors.extend(forbidden_nested_values(value, str(path)))
    return errors


def validate_ledger(path: Path, errors: list[str]) -> None:
    if path.name == "android-tamper.jsonl":
        validator = load_module("android_tamper_validator", ROOT / "flutter/scripts/validate_android_tamper_report.py")
        _, validation_errors = validator.load_records([path])
        errors.extend(validation_errors)
        return
    if path.name == "phase4-latency.jsonl":
        validator = load_module("phase4_latency_validator", ROOT / "flutter/scripts/phase4_latency_report.py")
        _, validation_errors = validator.load_records([path])
        errors.extend(validation_errors)
        return

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"{path}:{line_number}: invalid JSON: {error.msg}")
            continue
        errors.extend(forbidden_nested_values(value, f"{path}:{line_number}"))


def main() -> int:
    errors: list[str] = []
    files = public_files()
    for path in files:
        if not path.exists():
            continue
        relative = path.relative_to(ROOT)
        allowed_model_visual = relative in MODEL_PUBLIC_VISUALS
        if path.suffix.lower() in RAW_SUFFIXES and "private" not in path.parts and not allowed_model_visual:
            errors.append(f"raw artifact is public or staged: {path.relative_to(ROOT)}")
        if relative.parts[:2] == ("model", "evidence") and relative not in MODEL_PUBLIC_AGGREGATES | MODEL_PUBLIC_VISUALS:
            errors.append(f"unexpected model evidence file: {relative}")

    report_files = {
        str(path.relative_to(ROOT))
        for path in ROOT.glob("*/report.md")
    }
    if report_files != CANONICAL_REPORTS:
        errors.append(
            "exactly one canonical report is required per technology: "
            + ", ".join(sorted(CANONICAL_REPORTS))
        )
    legacy_reports = [path for path in public_files() if "reports" in path.relative_to(ROOT).parts]
    for path in legacy_reports:
        errors.append(f"legacy root report path is not allowed: {path.relative_to(ROOT)}")

    for path in sorted(MODEL_PUBLIC_AGGREGATES):
        if not path.exists():
            errors.append(f"missing public model aggregate: {path}")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: invalid public model aggregate: {error}")
            continue
        errors.extend(forbidden_nested_values(value, str(path)))

    client_runtime_validator = load_module(
        "client_runtime_evidence",
        ROOT / "docs/tools/client_runtime_evidence.py",
    )
    targets_path = ROOT / "docs/config/targets.json"
    try:
        targets_configuration = json.loads(targets_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{targets_path}: invalid target configuration: {error}")
        targets_configuration = {}
    for test_name, target in client_runtime_validator.configured_runtime_targets(targets_configuration).items():
        evidence_root = target.get("evidence", {}).get("root")
        if not isinstance(evidence_root, str):
            errors.append(f"{test_name}: missing client-runtime evidence root")
            continue
        errors.extend(
            client_runtime_validator.validate_client_runtime_root(
                ROOT / evidence_root,
                test_name,
                target,
            )
        )

    for path in sorted(ROOT.glob("*/evidence/ledger/**/*.jsonl")):
        validate_ledger(path, errors)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            errors.extend(forbidden_nested_values(value, f"{path}:{line_number}"))
            if isinstance(value, dict) and "visual_evidence_sha256" in value:
                digest = value["visual_evidence_sha256"]
                if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
                    errors.append(f"{path}:{line_number}: invalid visual evidence hash")

    device_register = ROOT / "flutter/config/device-register.json"
    if not device_register.exists():
        errors.append(f"missing public device register: {device_register.relative_to(ROOT)}")
    else:
        errors.extend(validate_device_register(device_register))

    if errors:
        print("public evidence verification failed:", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"- {error}", file=sys.stderr)
        return 1
    print("public evidence verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
