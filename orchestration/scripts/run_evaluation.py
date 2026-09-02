#!/usr/bin/env python3
"""Generate the single aggregate Gamblock-AI testing summary."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


TESTING_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE_ROOT = TESTING_ROOT.parent


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output_hash(output: str) -> str:
    return hashlib.sha256(output.encode("utf-8")).hexdigest()


def run_command(name: str, command: list[str], cwd: Path, workspace_root: Path, timeout: int = 240) -> dict[str, Any]:
    started = time.monotonic()
    environment = os.environ.copy()
    environment.setdefault("GOCACHE", "/tmp/gamblock-go-cache")
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        output = ((error.stdout or "") + "\n" + (error.stderr or "")).strip()
        return {
            "name": name,
            "status": "failed",
            "return_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output_sha256": output_hash(output),
            "reason": f"timeout after {timeout} seconds",
        }

    output = (completed.stdout + "\n" + completed.stderr).strip()
    status = "passed" if completed.returncode == 0 else "failed"
    if "Read-only file system" in output:
        status = "blocked_environment"
    try:
        relative_cwd = str(cwd.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        relative_cwd = cwd.name
    return {
        "name": name,
        "status": status,
        "return_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "working_directory": relative_cwd,
        "output_sha256": output_hash(output),
    }


def pending(name: str, reason: str) -> dict[str, Any]:
    return {"name": name, "status": "pending", "reason": reason}


def read_android_summary() -> dict[str, Any]:
    ledger = TESTING_ROOT / "evidence/ledger/android-tamper.jsonl"
    if not ledger.exists():
        return pending("android_anti_uninstall", "No promoted Android tamper ledger exists.")
    validator = load_module("android_tamper_validator", TESTING_ROOT / "flutter/scripts/validate_android_tamper_report.py")
    records, errors = validator.load_records([ledger])
    if errors:
        return {"name": "android_anti_uninstall", "status": "failed", "error_count": len(errors)}
    aggregate = validator.summarize(records)
    matrix = json.loads((TESTING_ROOT / "config/device-matrix.json").read_text(encoding="utf-8"))
    observed_families = {record["oem_family"] for record in records}
    observed_scenarios = {record["scenario"] for record in records}
    required_families = set(matrix["required_oem_families"])
    required_scenarios = set(matrix["scenarios"])
    coverage_complete = required_families <= observed_families and required_scenarios <= observed_scenarios
    return {
        "name": "android_anti_uninstall",
        "status": "passed" if aggregate["passed"] and coverage_complete else "partial" if aggregate["passed"] else "failed",
        "sample_count": aggregate["sample_count"],
        "group_count": aggregate["group_count"],
        "passed_group_count": sum(group["passed"] for group in aggregate["groups"]),
        "oem_family_count": len(observed_families),
        "scenario_count": len(observed_scenarios),
        "coverage_complete": coverage_complete,
    }


def read_latency_summary() -> dict[str, Any]:
    ledger = TESTING_ROOT / "evidence/ledger/phase4-latency.jsonl"
    if not ledger.exists():
        return pending("phase4_latency", "No promoted Phase 4 latency ledger exists.")
    validator = load_module("phase4_latency_validator", TESTING_ROOT / "flutter/scripts/phase4_latency_report.py")
    records, errors = validator.load_records([ledger])
    if errors:
        return {"name": "phase4_latency", "status": "failed", "error_count": len(errors)}
    aggregate = validator.report(records, minimum_samples=30, target_ms=200.0)
    return {
        "name": "phase4_latency",
        "status": "passed" if aggregate["passed"] else "pending",
        "group_count": len(aggregate["groups"]),
        "passed_group_count": sum(group["passed"] for group in aggregate["groups"]),
    }


def run_model_replay(workspace_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    model_root = workspace_root / "gamblock-ai-model"
    if not model_root.is_dir():
        return pending("model_evidence", "Model repository is not available."), pending("runtime_projection", "Model repository is not available.")
    with tempfile.TemporaryDirectory(prefix="gamblock-testing-") as temporary:
        directory = Path(temporary)
        model_output = directory / "model-evidence.json"
        projection_output = directory / "runtime-projection.json"
        model_result = run_command(
            "model_evidence",
            [sys.executable, "scripts/evaluate_model_evidence.py", "--output", str(model_output)],
            model_root,
            workspace_root,
        )
        projection_result = run_command(
            "runtime_projection",
            [
                sys.executable,
                str(TESTING_ROOT / "orchestration/scripts/runtime_projection.py"),
                "--workspace-root",
                str(workspace_root),
                "--output",
                str(projection_output),
            ],
            TESTING_ROOT,
            workspace_root,
            timeout=360,
        )
        if model_output.exists():
            model = json.loads(model_output.read_text(encoding="utf-8"))
            model_result["aggregate"] = {
                "evidence_maturity": model.get("evidence_maturity"),
                "dataset_rows": model.get("dataset", {}).get("test", {}).get("rows"),
            }
        if projection_output.exists():
            projection = json.loads(projection_output.read_text(encoding="utf-8"))
            metrics = projection.get("evaluation", {}).get("deployed_hybrid", {})
            projection_result["aggregate"] = {
                key: metrics.get(key) for key in ("accuracy", "precision", "recall", "f1_score", "false_positive_rate")
            }
        return model_result, projection_result


def run_code_checks(workspace_root: Path, include_flutter: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    commands = [
        ("model_tooling_unit", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], workspace_root / "gamblock-ai-model"),
        ("testing_flutter_unit", [sys.executable, "-m", "unittest", "discover", "-s", "flutter/tests", "-p", "test_*.py"], TESTING_ROOT),
        ("testing_orchestration_unit", [sys.executable, "-m", "unittest", "discover", "-s", "orchestration/tests", "-p", "test_*.py"], TESTING_ROOT),
        ("extension_unit", ["npm", "test"], workspace_root / "browser_extension"),
        ("website_unit", ["npm", "test", "--", "hooks/use-approval.test.tsx", "hooks/use-accountability.test.tsx", "lib/recovery/runtime.test.ts"], workspace_root / "gamblock-ai-website"),
        ("backend_unit", ["go", "test", "./internal/service", "-run", "Test(ProtectionGrantSigner_SignsDeviceBoundES256Grant|Accountability_CreateApprovalRequestAndResolve|Admin_EmergencyKeyGenerateAndValidate|ReflectionService)"], workspace_root / "gamblock-ai-backend"),
        ("client_python_contract_unit", [sys.executable, "-m", "unittest", "discover", "-s", "test/scripts", "-p", "*test.py"], workspace_root / "gamblock_ai_apps"),
    ]
    if include_flutter:
        commands.append(("flutter_pattern_interrupt_unit", ["flutter", "test", "test/features/pattern_interrupt/pattern_interrupt_screen_test.dart"], workspace_root / "gamblock_ai_apps"))
    else:
        results = [pending("flutter_pattern_interrupt_unit", "Use --include-flutter explicitly on a writable Flutter SDK installation.")]
    for name, command, cwd in commands:
        if not cwd.is_dir():
            results.append(pending(name, "Required component checkout is unavailable."))
        else:
            results.append(run_command(name, command, cwd, workspace_root))
    results.extend([
        pending("android_instrumented_runtime", "Requires an explicitly approved Android device run."),
        pending("windows_service_runtime", "Requires an approved Windows VM/device run."),
    ])
    return results


def render_summary(android: dict[str, Any], latency: dict[str, Any], model: dict[str, Any], projection: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    lines = [
        "# Gamblock-AI Testing Summary",
        "",
        "This is the canonical cross-repository testing summary. It is generated",
        "from the public aggregate ledger and aggregate command results only.",
        "Raw URL, domain, DOM, browsing history, screenshot, serial, credential,",
        "participant, and raw log data are never included.",
        "",
        "## Evidence status",
        "",
        "| Evidence family | Status | Aggregate |",
        "|---|---|---|",
        f"| Android anti-uninstall | {android['status']} | {android.get('sample_count', 0)} samples / {android.get('group_count', 0)} groups |",
        f"| Phase 4 latency | {latency['status']} | {latency.get('group_count', 0)} groups |",
        f"| Model evidence | {model['status']} | {model.get('aggregate', {}).get('evidence_maturity', 'not generated')} |",
        f"| Runtime projection | {projection['status']} | {projection.get('aggregate', {}).get('accuracy', 'not generated')} accuracy when generated |",
        "",
        "## Android baseline",
        "",
        "The initial baseline contains seven validated Android Research samples",
        "from one AOSP/Pixel device. This is provisional evidence and does not",
        "establish compatibility across Samsung, Xiaomi/Redmi, OPPO/Realme, or",
        "Vivo devices. The interrupted reboot scenario remains pending.",
        "",
        "## Component checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    lines.extend(f"| {item['name']} | {item['status']} |" for item in checks)
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "Offline replay is not physical browser, Android, or Windows runtime proof.",
        "A missing matrix cell remains pending. Component repositories retain",
        "ownership of their source code and local unit tests; this repository owns",
        "the cross-repository evidence ledger and this summary only.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--output", type=Path, default=TESTING_ROOT / "reports/testing-summary.md")
    parser.add_argument("--run-model-replay", action="store_true")
    parser.add_argument("--run-code-tests", action="store_true")
    parser.add_argument("--include-flutter", action="store_true")
    args = parser.parse_args()

    workspace_root = args.workspace_root.resolve()
    android = read_android_summary()
    latency = read_latency_summary()
    if args.run_model_replay:
        model, projection = run_model_replay(workspace_root)
    else:
        model = pending("model_evidence", "Not requested; use --run-model-replay explicitly.")
        projection = pending("runtime_projection", "Not requested; use --run-model-replay explicitly.")
    checks = run_code_checks(workspace_root, args.include_flutter) if args.run_code_tests else [
        pending("component_checks", "Not requested; use --run-code-tests explicitly."),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_summary(android, latency, model, projection, checks), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "android_samples": android.get("sample_count", 0)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
