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
}
RAW_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".log", ".trace", ".pcap"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


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
        if path.suffix.lower() in RAW_SUFFIXES and "private" not in path.parts:
            errors.append(f"raw artifact is public or staged: {path.relative_to(ROOT)}")

    summaries = sorted((ROOT / "reports").glob("*summary*.md")) if (ROOT / "reports").exists() else []
    canonical = ROOT / "reports/testing-summary.md"
    if summaries != [canonical]:
        errors.append("exactly one canonical report is required: reports/testing-summary.md")

    for path in sorted((ROOT / "evidence/ledger").rglob("*.jsonl")) if (ROOT / "evidence/ledger").exists() else []:
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

    if errors:
        print("public evidence verification failed:", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"- {error}", file=sys.stderr)
        return 1
    print("public evidence verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
