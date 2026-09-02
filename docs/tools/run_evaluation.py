#!/usr/bin/env python3
"""Generate aggregate Gamblock-AI reports, one per technology."""

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
REPORT_PATHS = {
    "flutter": Path("flutter/report.md"),
    "golang": Path("golang/report.md"),
    "next": Path("next/report.md"),
    "browser-extention": Path("browser-extention/report.md"),
    "model": Path("model/report.md"),
}


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
    ledger = TESTING_ROOT / "flutter/evidence/ledger/android-tamper.jsonl"
    if not ledger.exists():
        return pending("android_anti_uninstall", "No promoted Android tamper ledger exists.")
    validator = load_module("android_tamper_validator", TESTING_ROOT / "flutter/scripts/validate_android_tamper_report.py")
    records, errors = validator.load_records([ledger])
    if errors:
        return {"name": "android_anti_uninstall", "status": "failed", "error_count": len(errors)}
    aggregate = validator.summarize(records)
    matrix = json.loads((TESTING_ROOT / "flutter/config/device-matrix.json").read_text(encoding="utf-8"))
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
    ledger = TESTING_ROOT / "flutter/evidence/ledger/phase4-latency.jsonl"
    if not ledger.exists():
        return pending("phase4_latency", "No promoted Phase 4 latency ledger exists.")
    validator = load_module("phase4_latency_validator", TESTING_ROOT / "flutter/scripts/phase4_latency_report.py")
    records, errors = validator.load_records([ledger])
    if errors:
        return {"name": "phase4_latency", "status": "failed", "error_count": len(errors)}
    targets = json.loads((TESTING_ROOT / "docs/config/targets.json").read_text(encoding="utf-8"))
    latency_targets = targets["latency"]
    aggregate = validator.report(
        records,
        minimum_samples=int(latency_targets["minimum_successful_samples_per_group"]),
        target_ms=float(latency_targets["input_to_visible_ms_p95_exclusive"]),
    )
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
                str(TESTING_ROOT / "docs/tools/runtime_projection.py"),
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
        ("testing_orchestration_unit", [sys.executable, "-m", "unittest", "discover", "-s", "docs/tools/tests", "-p", "test_*.py"], TESTING_ROOT),
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


def select_checks(checks: list[dict[str, Any]], names: set[str], fallback_name: str) -> list[dict[str, Any]]:
    selected = [item for item in checks if item.get("name") in names]
    if selected:
        return selected
    if checks:
        fallback = dict(checks[0])
        fallback["name"] = fallback_name
        return [fallback]
    return [pending(fallback_name, "Not requested; use --run-code-tests explicitly.")]


def render_check_section(checks: list[dict[str, Any]], names: set[str], fallback_name: str) -> list[str]:
    lines = [
        "## Component checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    lines.extend(f"| {item['name']} | {item['status']} |" for item in select_checks(checks, names, fallback_name))
    return lines


def render_report(title: str, description: str, sections: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        "This is the canonical aggregate report for this technology. It is",
        "generated from validated public evidence and aggregate command results.",
        "Raw URL, domain, DOM, browsing history, screenshot, serial, credential,",
        "participant, and raw log data are never included.",
        "",
        description,
        "",
    ]
    lines.extend(sections)
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "Offline replay is not physical browser, Android, or Windows runtime proof.",
        "A missing matrix cell remains pending. This report contains aggregate",
        "results only; source code and component unit tests remain in their owners.",
        "",
    ])
    return "\n".join(lines)


def render_flutter_report(android: dict[str, Any], latency: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    sections = [
        "## Android anti-uninstall",
        "",
        "| Status | Samples | Groups | OEM families | Scenarios | Coverage complete |",
        "|---|---:|---:|---:|---:|---|",
        f"| {android.get('status', 'pending')} | {android.get('sample_count', 0)} | {android.get('group_count', 0)} | {android.get('oem_family_count', 0)} | {android.get('scenario_count', 0)} | {android.get('coverage_complete', False)} |",
        "",
        "## Phase 4 latency",
        "",
        "| Status | Groups | Passed groups |",
        "|---|---:|---:|",
        f"| {latency.get('status', 'pending')} | {latency.get('group_count', 0)} | {latency.get('passed_group_count', 0)} |",
        "",
    ]
    sections.extend(render_check_section(checks, {"testing_flutter_unit", "client_python_contract_unit", "flutter_pattern_interrupt_unit", "android_instrumented_runtime"}, "flutter_component_checks"))
    return render_report("Gamblock-AI Flutter / Android Report", "This report covers Flutter client checks and Android Research runtime evidence.", sections)


def render_component_report(title: str, description: str, checks: list[dict[str, Any]], names: set[str], fallback_name: str) -> str:
    return render_report(title, description, render_check_section(checks, names, fallback_name))


def render_model_report(model: dict[str, Any], projection: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    sections = [
        "## Model replay",
        "",
        "| Status | Evidence maturity | Test rows |",
        "|---|---|---:|",
        f"| {model.get('status', 'pending')} | {model.get('aggregate', {}).get('evidence_maturity', 'not generated')} | {model.get('aggregate', {}).get('dataset_rows', 'not generated')} |",
        "",
        "## Runtime projection",
        "",
        "| Status | Accuracy | Precision | Recall | F1 | False-positive rate |",
        "|---|---:|---:|---:|---:|---:|",
        f"| {projection.get('status', 'pending')} | {projection.get('aggregate', {}).get('accuracy', 'not generated')} | {projection.get('aggregate', {}).get('precision', 'not generated')} | {projection.get('aggregate', {}).get('recall', 'not generated')} | {projection.get('aggregate', {}).get('f1_score', 'not generated')} | {projection.get('aggregate', {}).get('false_positive_rate', 'not generated')} |",
        "",
    ]
    sections.extend(render_check_section(checks, {"model_tooling_unit"}, "model_tooling_unit"))
    return render_report("Gamblock-AI Model Report", "This report covers offline model evidence and runtime projection only.", sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=TESTING_ROOT)
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
    reports = {
        "flutter": render_flutter_report(android, latency, checks),
        "golang": render_component_report("Gamblock-AI Golang Report", "This report covers the Go backend component checks.", checks, {"backend_unit"}, "backend_unit"),
        "next": render_component_report("Gamblock-AI Next.js Report", "This report covers the Next.js website component checks.", checks, {"website_unit"}, "website_unit"),
        "browser-extention": render_component_report("Gamblock-AI Browser Extention Report", "This report covers the passive browser extension component checks.", checks, {"extension_unit"}, "extension_unit"),
        "model": render_model_report(model, projection, checks),
    }
    outputs: dict[str, str] = {}
    for technology, content in reports.items():
        output = args.output_dir / REPORT_PATHS[technology]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        outputs[technology] = str(output)
    print(json.dumps({"outputs": outputs, "android_samples": android.get("sample_count", 0)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
