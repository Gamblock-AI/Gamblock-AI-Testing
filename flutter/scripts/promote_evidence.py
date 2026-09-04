#!/usr/bin/env python3
"""Promote local aggregate evidence into the public testing ledger."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
SAFE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def load_validator(name: str = "validate_android_tamper_report.py"):
    path = SCRIPT_ROOT / name
    spec = importlib.util.spec_from_file_location("android_tamper_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_visual_hashes(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        sample_id, separator, raw_path = value.partition("=")
        if not separator or not sample_id or not raw_path:
            raise ValueError("--visual-hash must use SAMPLE_ID=PATH")
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError(f"visual evidence file does not exist: {path}")
        result[sample_id] = sha256(path)
    return result


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: record must be an object")
        records.append(value)
    return records


def promote(records: list[dict[str, Any]], visual_hashes: dict[str, str], validator: Any) -> list[dict[str, Any]]:
    promoted: list[dict[str, Any]] = []
    for record in records:
        value = dict(record)
        value["schema_version"] = 2
        sample_id = value.get("sample_id")
        digest = visual_hashes.get(sample_id)
        value["visual_evidence_present"] = digest is not None
        if digest is None:
            value.pop("visual_evidence_sha256", None)
        else:
            value["visual_evidence_sha256"] = digest
        errors = validator.validate_record(value, "local-evidence", len(promoted) + 1)
        if errors:
            raise ValueError("; ".join(errors))
        promoted.append(value)

    sample_ids = [record["sample_id"] for record in promoted]
    duplicates = sorted({sample_id for sample_id in sample_ids if sample_ids.count(sample_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate sample_id values: {duplicates}")
    return sorted(promoted, key=lambda record: (record["run_id"], record["sample_id"]))


def promote_latency(records: list[dict[str, Any]], validator: Any) -> list[dict[str, Any]]:
    """Promote Phase 4 records without adding visual evidence fields.

    The Phase 4 schema is an explicit privacy allowlist. Retaining the record
    exactly after validation prevents this generic promoter from broadening it.
    """

    promoted: list[dict[str, Any]] = []
    for record in records:
        value = dict(record)
        errors = validator.validate_record(value, "local-evidence", len(promoted) + 1)
        if errors:
            raise ValueError("; ".join(errors))
        promoted.append(value)

    sample_ids = [record["sample_id"] for record in promoted]
    duplicates = sorted({sample_id for sample_id in sample_ids if sample_ids.count(sample_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate sample_id values: {duplicates}")
    return sorted(promoted, key=lambda record: (record["run_id"], record["sample_id"]))


def merge_records(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge a device ledger without silently replacing existing samples."""

    merged: dict[str, dict[str, Any]] = {}
    for record in [*existing, *incoming]:
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise ValueError("all promoted records require a non-empty sample_id")
        if sample_id in merged:
            raise ValueError(f"duplicate sample_id across existing and incoming evidence: {sample_id!r}")
        merged[sample_id] = record
    return sorted(merged.values(), key=lambda record: (record["run_id"], record["sample_id"]))


def validate_device_output(records: list[dict[str, Any]], output: Path, kind: str) -> None:
    """Require one safe device folder and the matching ledger filename."""

    expected_filename = f"{kind}.jsonl"
    if output.name != expected_filename:
        raise ValueError(f"--output must end with {expected_filename}")
    device_alias = output.parent.name
    if SAFE_LABEL_PATTERN.fullmatch(device_alias) is None:
        raise ValueError("--output parent must be a safe device_alias folder")
    aliases = {record.get("device_alias") for record in records}
    if aliases != {device_alias}:
        raise ValueError(
            f"--output folder {device_alias!r} must match all record device_alias values {sorted(aliases)!r}"
        )


def load_existing(path: Path, validator: Any) -> list[dict[str, Any]]:
    """Load an existing ledger and refuse to build on invalid public data."""

    if not path.exists():
        return []
    existing, errors = validator.load_records([path])
    if errors:
        raise ValueError("existing ledger is invalid: " + "; ".join(errors))
    return existing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("android-tamper", "phase4-latency"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--visual-hash",
        action="append",
        default=[],
        metavar="SAMPLE_ID=PATH",
        help="hash a local visual artifact without copying it",
    )
    args = parser.parse_args()

    try:
        visual_hashes = parse_visual_hashes(args.visual_hash)
        source_records = read_jsonl(args.input)
        if args.kind == "android-tamper":
            validator = load_validator()
            records = promote(source_records, visual_hashes, validator)
        else:
            if visual_hashes:
                raise ValueError("phase4-latency does not accept visual evidence")
            validator = load_validator("phase4_latency_report.py")
            records = promote_latency(source_records, validator)
        validate_device_output(records, args.output, args.kind)
        existing = load_existing(args.output, validator)
        records = merge_records(existing, records)
        validate_device_output(records, args.output, args.kind)
    except (OSError, ValueError, TypeError) as error:
        print(f"evidence promotion failed: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.tmp")
    with temporary.open("w", encoding="utf-8") as destination:
        for record in records:
            destination.write(json.dumps(record, sort_keys=True) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "samples": len(records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
