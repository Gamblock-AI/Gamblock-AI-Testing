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


def load_validator():
    path = SCRIPT_ROOT / "validate_android_tamper_report.py"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("android-tamper",))
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
        validator = load_validator()
        records = promote(read_jsonl(args.input), visual_hashes, validator)
    except (OSError, ValueError, TypeError) as error:
        print(f"evidence promotion failed: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as destination:
        for record in records:
            destination.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "samples": len(records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
