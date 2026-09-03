#!/usr/bin/env python3
"""Generate aggregate Gamblock-AI reports, one per technology."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
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
COMPONENT_REPORT_KEYS = {
    "flutter": "flutter",
    "backend": "golang",
    "website": "next",
    "browser_extension": "browser-extention",
    "model": "model",
}
COMPONENT_CHECK_NAMES = {
    "flutter": {
        "testing_flutter_unit",
        "client_python_contract_unit",
        "flutter_pattern_interrupt_unit",
        "windows_extension_model_e2e",
    },
    "backend": {"backend_unit", "backend_integration"},
    "website": {"website_unit", "website_e2e"},
    "browser_extension": {"extension_unit"},
    "model": {"model_tooling_unit"},
}
DEVICE_REGISTER_PATH = TESTING_ROOT / "flutter/config/device-register.json"
MODEL_EVIDENCE_ROOT = TESTING_ROOT / "model/evidence"
MODEL_AGGREGATE_ROOT = MODEL_EVIDENCE_ROOT / "aggregate"
MODEL_VISUAL_ROOT = MODEL_EVIDENCE_ROOT / "visuals"
MODEL_PRIVATE_ROOT = TESTING_ROOT / "model/private"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output_hash(output: str) -> str:
    return hashlib.sha256(output.encode("utf-8")).hexdigest()


def run_command(
    name: str,
    command: list[str],
    cwd: Path,
    workspace_root: Path,
    timeout: int = 240,
    capture_output: bool = False,
) -> dict[str, Any]:
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
        stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        output = (stdout + "\n" + stderr).strip()
        result = {
            "name": name,
            "status": "failed",
            "return_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "output_sha256": output_hash(output),
            "reason": f"timeout after {timeout} seconds",
        }
        if capture_output:
            result["_captured_output"] = output
        return result

    output = (completed.stdout + "\n" + completed.stderr).strip()
    status = "passed" if completed.returncode == 0 else "failed"
    if "Read-only file system" in output:
        status = "blocked_environment"
    try:
        relative_cwd = str(cwd.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        relative_cwd = cwd.name
    result = {
        "name": name,
        "status": status,
        "return_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "working_directory": relative_cwd,
        "output_sha256": output_hash(output),
    }
    if capture_output:
        result["_captured_output"] = output
    return result


def pending(name: str, reason: str) -> dict[str, Any]:
    return {"name": name, "status": "pending", "reason": reason}


def read_android_evidence() -> tuple[list[dict[str, Any]], list[str], bool]:
    ledger = TESTING_ROOT / "flutter/evidence/ledger/android-tamper.jsonl"
    if not ledger.exists():
        return [], [], False
    validator = load_module("android_tamper_validator", TESTING_ROOT / "flutter/scripts/validate_android_tamper_report.py")
    records, errors = validator.load_records([ledger])
    return records, errors, True


def read_device_register() -> dict[str, Any]:
    if not DEVICE_REGISTER_PATH.exists():
        return {"devices": [], "error": "Device register is unavailable."}
    try:
        value = json.loads(DEVICE_REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"devices": [], "error": f"Device register could not be read: {error}"}
    if not isinstance(value, dict) or not isinstance(value.get("devices"), list):
        return {"devices": [], "error": "Device register has an invalid shape."}
    return value


def read_android_summary() -> dict[str, Any]:
    records, errors, exists = read_android_evidence()
    if not exists:
        return pending("android_anti_uninstall", "No promoted Android tamper ledger exists.")
    if errors:
        return {"name": "android_anti_uninstall", "status": "failed", "error_count": len(errors)}
    validator = load_module("android_tamper_validator", TESTING_ROOT / "flutter/scripts/validate_android_tamper_report.py")
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
        reason = "Model repository is not available."
        return pending("runtime_projection", reason), pending("domain_grouped_model", reason)
    MODEL_AGGREGATE_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_VISUAL_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gamblock-testing-") as temporary:
        directory = Path(temporary)
        projection_output = MODEL_AGGREGATE_ROOT / "deployment_projection_evidence.json"
        grouped_output = MODEL_AGGREGATE_ROOT / "domain_grouped_evidence.json"
        grouped_onnx = directory / "domain-grouped-candidate.onnx"
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
        grouped_result = run_command(
            "domain_grouped_model",
            [
                sys.executable,
                "scripts/evaluate_domain_grouped_model.py",
                "--output",
                str(grouped_output),
                "--candidate-onnx",
                str(grouped_onnx),
                "--plot-dir",
                str(MODEL_VISUAL_ROOT),
                "--public-safe",
            ],
            model_root,
            workspace_root,
            timeout=1800,
        )
        if projection_result.get("status") == "passed" and projection_output.exists():
            projection = json.loads(projection_output.read_text(encoding="utf-8"))
            metrics = projection.get("evaluation", {}).get("deployed_hybrid", {})
            projection_result["aggregate"] = {
                key: metrics.get(key) for key in ("accuracy", "precision", "recall", "f1_score", "false_positive_rate")
            }
        if grouped_result.get("status") == "passed" and grouped_output.exists():
            grouped = json.loads(grouped_output.read_text(encoding="utf-8"))
            metrics = grouped.get("evaluation", {}).get("final_test", {})
            grouped_result["aggregate"] = {
                "evidence_maturity": grouped.get("evidence_maturity"),
                "samples": metrics.get("samples"),
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1_score": metrics.get("f1_score"),
                "false_positive_rate": metrics.get("false_positive_rate"),
                "numeric_gate_passed": metrics.get("numeric_gate_passed"),
                "split_audit_passed": grouped.get("split", {}).get("audit_passed"),
                "onnx_parity": grouped.get("parity", {}).get("status"),
                "ablations": grouped.get("evaluation", {}).get("ablations", {}),
                "slices": grouped.get("evaluation", {}).get("slices", {}),
                "camouflage": grouped.get("evaluation", {}).get("camouflage", {}),
                "threshold_sensitivity": grouped.get("evaluation", {}).get("threshold_sensitivity", {}),
                "calibration": grouped.get("evaluation", {}).get("calibration", {}),
                "offline_speed": grouped.get("evaluation", {}).get("offline_speed", {}),
                "repeated_grouped_cv": grouped.get("evaluation", {}).get("repeated_grouped_cv", {}),
                "leakage_audit": grouped.get("leakage_audit", {}),
                "split_integrity": grouped.get("split", {}).get("integrity_audit", {}),
                "visuals": grouped.get("artifacts", {}).get("visuals", {}),
                "scope_exclusions": grouped.get("scope_exclusions", {}),
                "limitations": grouped.get("limitations", {}),
            }
        return projection_result, grouped_result


def run_model_tests(workspace_root: Path) -> dict[str, Any]:
    model_root = workspace_root / "gamblock-ai-model"
    if not model_root.is_dir():
        return pending("model_tooling_unit", "Model repository is not available.")
    return run_command(
        "model_tooling_unit",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        model_root,
        workspace_root,
        timeout=360,
    )


def run_windows_extension_model_e2e(workspace_root: Path) -> dict[str, Any]:
    """Run the real Windows browser-extension/service smoke test when available."""

    if sys.platform != "win32":
        return pending("windows_extension_model_e2e", "Requires an approved Windows 11 VM or Windows runner.")
    script = TESTING_ROOT / "windows/run-extension-model-e2e.ps1"
    if not script.exists():
        return pending("windows_extension_model_e2e", "Windows integration harness is unavailable.")
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        return pending("windows_extension_model_e2e", "PowerShell is required on the Windows runner.")

    result = run_command(
        "windows_extension_model_e2e",
        [
            powershell,
            "-NoProfile",
            "-File",
            str(script),
            "-WorkspaceRoot",
            str(workspace_root),
        ],
        TESTING_ROOT,
        workspace_root,
        timeout=900,
        capture_output=True,
    )
    output = result.pop("_captured_output", "")
    if not output:
        return result
    try:
        summary = json.loads(output.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        if result.get("status") == "passed":
            result["status"] = "failed"
            result["reason"] = "Windows harness did not emit an aggregate result."
        return result
    if not isinstance(summary, dict) or summary.get("check") != "windows_extension_model_e2e":
        result["status"] = "failed"
        result["reason"] = "Windows harness aggregate identity mismatch."
        return result
    summary_status = summary.get("status")
    if summary_status not in {"passed", "pending", "failed"}:
        result["status"] = "failed"
        result["reason"] = "Windows harness aggregate status is invalid."
        return result
    result["status"] = summary_status
    if summary.get("reason_code"):
        result["reason"] = summary["reason_code"]
    if summary_status == "passed" and summary.get("raw_url_or_dom_emitted") is not False:
        result["status"] = "failed"
        result["reason"] = "Windows harness raw-data assertion failed."
    for key in (
        "browser_family",
        "build_mode",
        "scenario_total",
        "scenario_passed",
        "model_version",
        "ruleset_version",
        "model_sha256",
        "rules_sha256",
        "fixtures_sha256",
        "source_onnx_sha256",
        "intervention_samples",
        "intervention_min_ms",
        "intervention_max_ms",
        "raw_url_or_dom_emitted",
    ):
        if key in summary:
            result[key] = summary[key]
    return result


def check_names_for_components(components: list[str] | None) -> set[str] | None:
    if components is None:
        return None
    names: set[str] = set()
    for component in components:
        names.update(COMPONENT_CHECK_NAMES[component])
    return names


def report_keys_for_components(components: list[str] | None) -> set[str]:
    if components is None:
        return set(REPORT_PATHS)
    return {COMPONENT_REPORT_KEYS[component] for component in components}


def run_code_checks(
    workspace_root: Path,
    include_flutter: bool,
    components: list[str] | None = None,
    include_windows_e2e: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    selected_names = check_names_for_components(components)
    commands = [
        ("model_tooling_unit", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], workspace_root / "gamblock-ai-model"),
        ("testing_flutter_unit", [sys.executable, "-m", "unittest", "discover", "-s", "flutter/tests", "-p", "test_*.py"], TESTING_ROOT),
        ("testing_orchestration_unit", [sys.executable, "-m", "unittest", "discover", "-s", "docs/tools/tests", "-p", "test_*.py"], TESTING_ROOT),
        ("extension_unit", ["npm", "test"], workspace_root / "browser_extension"),
        ("website_unit", ["npm", "test"], workspace_root / "gamblock-ai-website"),
        ("website_e2e", ["npm", "run", "e2e"], workspace_root / "gamblock-ai-website"),
        ("backend_unit", ["make", "test"], workspace_root / "gamblock-ai-backend"),
        ("client_python_contract_unit", [sys.executable, "-m", "unittest", "discover", "-s", "test/scripts", "-p", "*test.py"], workspace_root / "gamblock_ai_apps"),
    ]
    if include_flutter and (selected_names is None or "flutter_pattern_interrupt_unit" in selected_names):
        commands.append(("flutter_pattern_interrupt_unit", ["flutter", "test", "test/features/pattern_interrupt/pattern_interrupt_screen_test.dart"], workspace_root / "gamblock_ai_apps"))
    elif selected_names is None or "flutter_pattern_interrupt_unit" in selected_names:
        results = [pending("flutter_pattern_interrupt_unit", "Use --include-flutter explicitly on a writable Flutter SDK installation.")]
    for name, command, cwd in commands:
        if selected_names is not None and name not in selected_names:
            continue
        if not cwd.is_dir():
            results.append(pending(name, "Required component checkout is unavailable."))
        else:
            results.append(run_command(name, command, cwd, workspace_root))
    if selected_names is None or "backend_integration" in selected_names:
        backend_root = workspace_root / "gamblock-ai-backend"
        if not backend_root.is_dir():
            results.append(pending("backend_integration", "Required backend checkout is unavailable."))
        elif os.environ.get("DATABASE_URL", "").strip():
            results.append(run_command("backend_integration", ["make", "test-integration"], backend_root, workspace_root, timeout=360))
        else:
            results.append(pending("backend_integration", "DATABASE_URL is not configured for an isolated PostgreSQL test database."))
    if selected_names is None or "flutter_pattern_interrupt_unit" in selected_names:
        results.append(pending("android_instrumented_runtime", "Requires an explicitly approved Android device run."))
    if selected_names is None or "windows_extension_model_e2e" in selected_names:
        if include_windows_e2e:
            results.append(run_windows_extension_model_e2e(workspace_root))
        else:
            results.append(pending("windows_extension_model_e2e", "Use --include-windows-e2e on an approved Windows VM or runner."))
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
        "Offline evaluation is not physical browser, Android, or Windows runtime proof.",
        "A missing matrix cell remains pending. This report contains aggregate-safe",
        "results and validated scenario detail where applicable; source code and",
        "component unit tests remain in their owners.",
        "",
    ])
    return "\n".join(lines)


def markdown_value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).replace("|", "\\|")


def transition(record: dict[str, Any], before: str, after: str) -> str:
    return f"{markdown_value(record.get(before))} → {markdown_value(record.get(after))}"


def render_android_evidence_details(
    records: list[dict[str, Any]],
    device_register: dict[str, Any],
) -> list[str]:
    lines = [
        "## Android device evidence detail",
        "",
        "Only validated public ledger records appear in this table. The result",
        "column is the evidence assertion status; expected and actual outcomes",
        "remain separate so an observed warning can be distinguished from a",
        "blocked uninstall assertion.",
        "",
        "| Device | Run / sample | OEM | API | Build | Service | Scenario | Surface | Action / observed | Expected → actual | Grant | Admin | Accessibility | Service state | App after | Recovery (s) | Result |",
        "|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---:|---|",
    ]
    registered = {
        device.get("device_alias"): device
        for device in device_register.get("devices", [])
        if isinstance(device, dict)
    }
    for record in sorted(
        records,
        key=lambda item: (
            item["device_alias"],
            item["scenario"],
            item["surface"],
            item["sample_id"],
        ),
    ):
        device = registered.get(record["device_alias"], {})
        display_name = device.get("display_name", record["device_alias"])
        service = device.get("service", "not_registered")
        action = f"{record['action']} / {record['observed_action']}"
        expected_actual = f"{record['expected_outcome']} → {record['actual_outcome']}"
        lines.append(
            "| "
            + " | ".join(
                (
                    markdown_value(display_name),
                    markdown_value(f"{record['run_id']} / {record['sample_id']}"),
                    markdown_value(record["oem_family"]),
                    markdown_value(record["android_api"]),
                    markdown_value(record["build_mode"]),
                    markdown_value(service),
                    markdown_value(record["scenario"]),
                    markdown_value(record["surface"]),
                    markdown_value(action),
                    markdown_value(expected_actual),
                    markdown_value(record["grant_state"]),
                    transition(record, "admin_active_before", "admin_active_after"),
                    transition(record, "accessibility_enabled_before", "accessibility_enabled_after"),
                    transition(record, "service_running_before", "service_running_after"),
                    markdown_value(record["app_present_after"]),
                    markdown_value(record.get("recovery_within_seconds")),
                    markdown_value(record["result"]),
                )
            )
            + " |"
        )
    if not records:
        lines.append("| — | — | — | — | — | — | No promoted Android records | — | — | — | — | — | — | — | — | — | pending |")
    return lines


def render_android_retest_queue(device_register: dict[str, Any]) -> list[str]:
    devices = [
        device
        for device in device_register.get("devices", [])
        if isinstance(device, dict) and device.get("evidence_status") != "valid_evidence"
    ]
    lines = [
        "## Android device retest queue (not evidence)",
        "",
        "These device records are planning metadata only. They do not contribute",
        "to Android samples, groups, OEM coverage, scenario coverage, or pass rates.",
        "A blank result means that no prior informal outcome has been promoted.",
        "",
        "| Device | OEM | Source | Service | Android API | Build | Status | Result | Retest required |",
        "|---|---|---|---|---:|---|---|---|---|",
    ]
    for device in sorted(devices, key=lambda item: str(item.get("device_alias", ""))):
        lines.append(
            "| "
            + " | ".join(
                (
                    markdown_value(device.get("display_name")),
                    markdown_value(device.get("oem_family")),
                    markdown_value(device.get("source")),
                    markdown_value(device.get("service")),
                    markdown_value(device.get("android_api")),
                    markdown_value(device.get("build_mode")),
                    markdown_value(device.get("evidence_status")),
                    "—",
                    markdown_value(device.get("retest_required")),
                )
            )
            + " |"
        )
    if not devices:
        lines.append("| — | — | — | — | — | — | No devices queued | — | — |")
    return lines


def render_flutter_report(
    android: dict[str, Any],
    latency: dict[str, Any],
    checks: list[dict[str, Any]],
    android_records: list[dict[str, Any]],
    device_register: dict[str, Any],
) -> str:
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
    sections.extend(render_android_evidence_details(android_records, device_register))
    sections.extend(["", ""])
    sections.extend(render_android_retest_queue(device_register))
    sections.extend([
        "",
        "## Android testing context",
        "",
        "Service and cross-OEM interpretation are maintained in",
        "[`docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).",
        "",
    ])
    sections.extend(render_windows_e2e_section(checks))
    sections.extend(["", ""])
    sections.extend(render_check_section(checks, {"testing_flutter_unit", "client_python_contract_unit", "flutter_pattern_interrupt_unit", "android_instrumented_runtime", "windows_extension_model_e2e"}, "flutter_component_checks"))
    return render_report("Gamblock-AI Flutter / Android Report", "This report covers Flutter client checks and Android Research runtime evidence.", sections)


def render_windows_e2e_section(checks: list[dict[str, Any]]) -> list[str]:
    check = next((item for item in checks if item.get("name") == "windows_extension_model_e2e"), None)
    if check is None:
        return [
            "## Windows extension–model runtime",
            "",
            "| Status | Browser | Build | Scenarios | Passed | Reason |",
            "|---|---|---|---:|---:|---|",
            "| pending | — | — | — | — | Requires an approved Windows runner |",
        ]
    return [
        "## Windows extension–model runtime",
        "",
        "| Status | Browser | Build | Scenarios | Passed | Reason | Model version | Ruleset version | Intervention samples |",
        "|---|---|---|---:|---:|---|---|---|---:|",
        "| "
        + " | ".join(
            markdown_value(check.get(key))
            for key in (
                "status",
                "browser_family",
                "build_mode",
                "scenario_total",
                "scenario_passed",
                "reason",
                "model_version",
                "ruleset_version",
                "intervention_samples",
            )
        )
        + " |",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
        *(
            f"| {label} | {markdown_value(check.get(key))} |"
            for label, key in (
                ("Model asset", "model_sha256"),
                ("Rules asset", "rules_sha256"),
                ("Fixture set", "fixtures_sha256"),
                ("Source ONNX", "source_onnx_sha256"),
            )
        ),
        "",
        "Artifact identity is aggregate-safe; raw URL, DOM, token, screenshot, and browser log data are never published.",
    ]


def render_component_report(title: str, description: str, checks: list[dict[str, Any]], names: set[str], fallback_name: str) -> str:
    return render_report(title, description, render_check_section(checks, names, fallback_name))


def render_model_report(
    projection: dict[str, Any],
    grouped: dict[str, Any],
    checks: list[dict[str, Any]],
) -> str:
    grouped_aggregate = grouped.get("aggregate", {})
    ablations = grouped_aggregate.get("ablations", {})
    slices = grouped_aggregate.get("slices", {})
    camouflage = grouped_aggregate.get("camouflage", {})
    threshold_sensitivity = grouped_aggregate.get("threshold_sensitivity", {})
    calibration = grouped_aggregate.get("calibration", {})
    offline_speed = grouped_aggregate.get("offline_speed", {})
    repeated_cv = grouped_aggregate.get("repeated_grouped_cv", {})
    leakage_audit = grouped_aggregate.get("leakage_audit", {})
    split_integrity = grouped_aggregate.get("split_integrity", {})
    visuals = grouped_aggregate.get("visuals", {})
    scope_exclusions = grouped_aggregate.get("scope_exclusions", {})
    limitations = grouped_aggregate.get("limitations", {})
    sections = [
        "## Runtime projection",
        "",
        "| Status | Accuracy | Precision | Recall | F1 | False-positive rate |",
        "|---|---:|---:|---:|---:|---:|",
        f"| {projection.get('status', 'pending')} | {projection.get('aggregate', {}).get('accuracy', 'not generated')} | {projection.get('aggregate', {}).get('precision', 'not generated')} | {projection.get('aggregate', {}).get('recall', 'not generated')} | {projection.get('aggregate', {}).get('f1_score', 'not generated')} | {projection.get('aggregate', {}).get('false_positive_rate', 'not generated')} |",
        "",
        "## Text-and-domain grouped candidate",
        "",
        "| Status | Evidence maturity | Test rows | Accuracy | Precision | Recall | F1 | FPR | Numeric gate | Split audit | ONNX parity |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|",
        f"| {grouped.get('status', 'pending')} | {grouped_aggregate.get('evidence_maturity', 'not generated')} | {grouped_aggregate.get('samples', 'not generated')} | {grouped_aggregate.get('accuracy', 'not generated')} | {grouped_aggregate.get('precision', 'not generated')} | {grouped_aggregate.get('recall', 'not generated')} | {grouped_aggregate.get('f1_score', 'not generated')} | {grouped_aggregate.get('false_positive_rate', 'not generated')} | {grouped_aggregate.get('numeric_gate_passed', 'not generated')} | {grouped_aggregate.get('split_audit_passed', 'not generated')} | {grouped_aggregate.get('onnx_parity', 'not generated')} |",
        "",
        "The text-and-domain grouped candidate is a separate research artifact. It does",
        "not replace the active client model automatically.",
        "",
        "## Text-and-domain grouped ablations",
        "",
        "| Variant | Samples | Accuracy | Precision | Recall | F1 | FPR | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    if ablations:
        for name, metrics in sorted(ablations.items()):
            sections.append(
                f"| {name} | {metrics.get('samples', '—')} | {metrics.get('accuracy', '—')} | "
                f"{metrics.get('precision', '—')} | {metrics.get('recall', '—')} | "
                f"{metrics.get('f1_score', '—')} | {metrics.get('false_positive_rate', '—')} | "
                f"{metrics.get('numeric_gate_passed', '—')} |"
            )
    else:
        sections.append("| — | — | — | — | — | — | — | pending |")
    sections.extend([
        "",
        "## Camouflage robustness",
        "",
        "Variants are generated in memory from the frozen grouped final-test rows;",
        "positive-class variants also support train-only augmentation, and no",
        "camouflage dataset is persisted.",
        "",
        "| Variant | Samples | Accuracy | Precision | Recall | F1 | FPR | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    camouflage_variants = camouflage.get("variants", {})
    if camouflage_variants:
        for name, metrics in sorted(camouflage_variants.items()):
            sections.append(
                f"| {name} | {markdown_value(metrics.get('samples'))} | "
                f"{markdown_value(metrics.get('accuracy'))} | {markdown_value(metrics.get('precision'))} | "
                f"{markdown_value(metrics.get('recall'))} | {markdown_value(metrics.get('f1_score'))} | "
                f"{markdown_value(metrics.get('false_positive_rate'))} | "
                f"{markdown_value(metrics.get('numeric_gate_passed'))} |"
            )
    else:
        sections.append("| — | — | — | — | — | — | — | pending |")
    sections.extend([
        "",
        "## Threshold sensitivity",
        "",
        "| Threshold | Precision | Recall | F1 | FPR | Selected |",
        "|---:|---:|---:|---:|---:|---|",
    ])
    threshold_results = threshold_sensitivity.get("results", [])
    if threshold_results:
        for result in threshold_results:
            sections.append(
                f"| {markdown_value(result.get('threshold'))} | {markdown_value(result.get('precision'))} | "
                f"{markdown_value(result.get('recall'))} | {markdown_value(result.get('f1_score'))} | "
                f"{markdown_value(result.get('false_positive_rate'))} | {markdown_value(result.get('selected'))} |"
            )
    else:
        sections.append("| — | — | — | — | — | pending |")
    sections.extend([
        "",
        "## Calibration",
        "",
        "| Status | Samples | Brier score | Expected calibration error |",
        "|---|---:|---:|---:|",
        f"| {markdown_value(calibration.get('status'))} | {markdown_value(calibration.get('samples'))} | "
        f"{markdown_value(calibration.get('brier_score'))} | {markdown_value(calibration.get('expected_calibration_error'))} |",
        "",
        "## Repeated grouped validation",
        "",
        "| Status | Folds per repetition | Repetitions | Evaluations | Gate pass rate | Mean accuracy | Mean precision | Mean recall | Mean F1 | Mean FPR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    cv_summary = repeated_cv.get("summary", {})
    cv_mean = cv_summary.get("mean", {})
    sections.append(
        f"| {markdown_value(cv_summary.get('status'))} | {markdown_value(repeated_cv.get('folds'))} | "
        f"{markdown_value(repeated_cv.get('repetitions'))} | {markdown_value(repeated_cv.get('total_evaluations'))} | "
        f"{markdown_value(cv_summary.get('numeric_gate_pass_rate'))} | {markdown_value(cv_mean.get('accuracy'))} | "
        f"{markdown_value(cv_mean.get('precision'))} | {markdown_value(cv_mean.get('recall'))} | "
        f"{markdown_value(cv_mean.get('f1_score'))} | {markdown_value(cv_mean.get('false_positive_rate'))} |"
    )
    sections.extend([
        "",
        "## Duplicate and leakage audit",
        "",
        "| Field | Duplicate groups | Duplicate rows | Cross-split groups |",
        "|---|---:|---:|---:|",
    ])
    audit_fields = [name for name, details in leakage_audit.items() if isinstance(details, dict)]
    if audit_fields:
        for name in sorted(audit_fields):
            details = leakage_audit[name]
            sections.append(
                f"| {name} | {markdown_value(details.get('groups_with_duplicates'))} | "
                f"{markdown_value(details.get('duplicate_rows'))} | "
                f"{markdown_value(details.get('cross_split_duplicate_groups'))} |"
            )
        sections.append(f"Overall audit passed: **{markdown_value(leakage_audit.get('audit_passed'))}**.")
    else:
        sections.append("| — | — | — | pending |")
    sections.extend([
        "",
        "## Split integrity audit",
        "",
        "| Status | Clean rows | Train rows | Test rows | Excluded rows | Failed checks |",
        "|---|---:|---:|---:|---:|---|",
    ])
    if split_integrity:
        counts = split_integrity.get("counts", {})
        failed_checks = ", ".join(split_integrity.get("failed_checks", [])) or "none"
        sections.append(
            f"| {markdown_value(split_integrity.get('status'))} | "
            f"{markdown_value(counts.get('clean_rows'))} | "
            f"{markdown_value(counts.get('train_rows'))} | "
            f"{markdown_value(counts.get('test_rows'))} | "
            f"{markdown_value(counts.get('actual_excluded_rows'))} | "
            f"{markdown_value(failed_checks)} |"
        )
    else:
        sections.append("| pending | — | — | — | — | not generated |")
    sections.extend([
        "",
        "## Offline inference speed",
        "",
        "| Status | Samples/run | Runs | Mean ms | P50 ms | P95 ms | Max ms | Mean ms/sample |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| {markdown_value(offline_speed.get('status'))} | {markdown_value(offline_speed.get('samples_per_run'))} | "
        f"{markdown_value(offline_speed.get('runs'))} | {markdown_value(offline_speed.get('mean_ms'))} | "
        f"{markdown_value(offline_speed.get('p50_ms'))} | {markdown_value(offline_speed.get('p95_ms'))} | "
        f"{markdown_value(offline_speed.get('max_ms'))} | {markdown_value(offline_speed.get('mean_ms_per_sample'))} |",
        "",
        "Scope: offline prediction on the evaluation host; browser, UI, and device latency are excluded.",
        "",
        "## Visual artifacts",
        "",
        "| Artifact | Status | Size (bytes) | SHA-256 recorded |",
        "|---|---|---:|---|",
    ])
    visual_files = visuals.get("files", {})
    if visual_files:
        for name, artifact in sorted(visual_files.items()):
            sections.append(
                f"| {name} | {markdown_value(visuals.get('status'))} | "
                f"{markdown_value(artifact.get('bytes'))} | {markdown_value(bool(artifact.get('sha256')))} |"
            )
    else:
        sections.append("| — | pending | — | — |")
    sections.extend([
        "",
        "## Scope exclusions",
        "",
    ])
    if scope_exclusions:
        sections.extend(f"- {name}: {reason}" for name, reason in sorted(scope_exclusions.items()))
    else:
        sections.append("- none recorded")
    sections.extend([
        "",
        "## Text-and-domain grouped slices",
        "",
        "| Slice | Samples | Status | Accuracy | Precision | Recall | F1 | FPR |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ])
    if slices:
        for name, details in sorted(slices.items()):
            metrics = details.get("metrics", {})
            sections.append(
                f"| {name} | {details.get('samples', '—')} | {metrics.get('status', '—')} | "
                f"{metrics.get('accuracy', '—')} | {metrics.get('precision', '—')} | "
                f"{metrics.get('recall', '—')} | {metrics.get('f1_score', '—')} | "
                f"{metrics.get('false_positive_rate', '—')} |"
            )
    else:
        sections.append("| — | — | pending | — | — | — | — | — |")
    sections.extend([
        "",
        "## Text-and-domain grouped limitations",
        "",
    ])
    if limitations:
        sections.extend(f"- {name}: {reason}" for name, reason in sorted(limitations.items()))
    else:
        sections.append("- pending: grouped replay was not requested")
    sections.extend(render_check_section(checks, {"model_tooling_unit"}, "model_tooling_unit"))
    return render_report(
        "Gamblock-AI Model Report",
        "This report covers offline deployment projection and text-and-domain grouped candidate evaluation only.",
        sections,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=TESTING_ROOT)
    parser.add_argument("--run-model-replay", action="store_true")
    parser.add_argument("--run-model-tests", action="store_true")
    parser.add_argument("--run-code-tests", action="store_true")
    parser.add_argument(
        "--component",
        action="append",
        choices=sorted(COMPONENT_REPORT_KEYS),
        help="Limit --run-code-tests and report generation to the selected component(s).",
    )
    parser.add_argument("--include-flutter", action="store_true")
    parser.add_argument("--include-windows-e2e", action="store_true")
    args = parser.parse_args()

    if args.component and not (args.run_code_tests or args.run_model_tests):
        parser.error("--component requires --run-code-tests or --run-model-tests")

    workspace_root = args.workspace_root.resolve()
    android_records, android_errors, android_ledger_exists = read_android_evidence()
    if android_errors:
        android_records = []
    android = read_android_summary()
    latency = read_latency_summary()
    device_register = read_device_register()
    if args.run_model_replay:
        projection, grouped = run_model_replay(workspace_root)
    else:
        projection = pending("runtime_projection", "Not requested; use --run-model-replay explicitly.")
        grouped = pending("domain_grouped_model", "Not requested; use --run-model-replay explicitly.")
    checks = run_code_checks(workspace_root, args.include_flutter, args.component, args.include_windows_e2e) if args.run_code_tests else [
        pending("component_checks", "Not requested; use --run-code-tests explicitly."),
    ]
    model_checks = [check for check in checks if check.get("name") == "model_tooling_unit"]
    if args.run_model_tests:
        model_checks = [run_model_tests(workspace_root)]
    elif not model_checks:
        model_checks = [pending("model_tooling_unit", "Not requested; use --run-model-tests explicitly.")]
    selected_reports = report_keys_for_components(args.component)
    reports: dict[str, str] = {}
    if "flutter" in selected_reports:
        reports["flutter"] = render_flutter_report(android, latency, checks, android_records, device_register)
    if "golang" in selected_reports:
        reports["golang"] = render_component_report("Gamblock-AI Golang Report", "This report covers the Go backend component checks.", checks, COMPONENT_CHECK_NAMES["backend"], "backend_unit")
    if "next" in selected_reports:
        reports["next"] = render_component_report("Gamblock-AI Next.js Report", "This report covers the Next.js website component checks.", checks, COMPONENT_CHECK_NAMES["website"], "website_unit")
    if "browser-extention" in selected_reports:
        reports["browser-extention"] = render_component_report("Gamblock-AI Browser Extention Report", "This report covers the passive browser extension component checks.", checks, {"extension_unit"}, "extension_unit")
    if "model" in selected_reports:
        reports["model"] = render_model_report(projection, grouped, model_checks)
    outputs: dict[str, str] = {}
    for technology, content in reports.items():
        output = args.output_dir / REPORT_PATHS[technology]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        outputs[technology] = str(output)
    print(
        json.dumps(
            {
                "outputs": outputs,
                "android_ledger_exists": android_ledger_exists,
                "android_samples": android.get("sample_count", 0),
                "android_retest_devices": sum(
                    device.get("evidence_status") != "valid_evidence"
                    for device in device_register.get("devices", [])
                    if isinstance(device, dict)
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
