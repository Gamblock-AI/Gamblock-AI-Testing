import importlib.util
import json
import os
import pathlib
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).parents[3]
RUNNER_PATH = ROOT / "docs/tools/run_evaluation.py"
SPEC = importlib.util.spec_from_file_location("run_evaluation", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def record(**overrides):
    value = {
        "run_id": "tamper_pixel_2026_09",
        "sample_id": "pixel_settings_01",
        "device_alias": "pixel_9_pro_remote_01",
        "oem_family": "aosp",
        "android_api": 35,
        "build_mode": "debug",
        "service_running_before": True,
        "service_running_after": True,
        "admin_active_before": True,
        "admin_active_after": True,
        "accessibility_enabled_before": True,
        "accessibility_enabled_after": True,
        "app_present_after": True,
        "scenario": "settings_uninstall",
        "surface": "settings",
        "action": "uninstall",
        "observed_action": "uninstall",
        "expected_outcome": "blocked",
        "actual_outcome": "warned",
        "grant_state": "none",
        "recovery_within_seconds": None,
        "result": "passed",
    }
    value.update(overrides)
    return value


class RunEvaluationReportTest(unittest.TestCase):
    def test_flutter_component_includes_windows_extension_model_e2e(self):
        self.assertIn(
            "windows_extension_model_e2e",
            RUNNER.check_names_for_components(["flutter"]),
        )

    def test_windows_runtime_is_pending_off_windows(self):
        result = RUNNER.run_windows_extension_model_e2e(ROOT.parent)

        self.assertEqual("windows_extension_model_e2e", result["name"])
        self.assertEqual("pending", result["status"])

    def test_windows_runtime_keeps_only_allowlisted_aggregate_fields(self):
        summary = {
            "check": "windows_extension_model_e2e",
            "status": "passed",
            "browser_family": "chrome",
            "build_mode": "release",
            "scenario_total": 7,
            "scenario_passed": 7,
            "model_version": "gamblock-lr-14012bec0479",
            "ruleset_version": "gamblock-rules-v2",
            "model_sha256": "a" * 64,
            "rules_sha256": "b" * 64,
            "fixtures_sha256": "c" * 64,
            "source_onnx_sha256": "d" * 64,
            "intervention_samples": 2,
            "raw_url_or_dom_emitted": False,
            "raw_dom": "must-not-be-retained",
        }
        command_result = {
            "name": "windows_extension_model_e2e",
            "status": "passed",
            "_captured_output": json.dumps(summary),
        }
        with mock.patch.object(RUNNER.sys, "platform", "win32"), mock.patch.object(
            RUNNER.shutil, "which", return_value="pwsh"
        ), mock.patch.object(RUNNER, "run_command", return_value=command_result):
            result = RUNNER.run_windows_extension_model_e2e(ROOT.parent)

        self.assertEqual("passed", result["status"])
        self.assertEqual(7, result["scenario_passed"])
        self.assertEqual("gamblock-lr-14012bec0479", result["model_version"])
        self.assertEqual("a" * 64, result["model_sha256"])
        self.assertEqual("d" * 64, result["source_onnx_sha256"])
        self.assertFalse(result["raw_url_or_dom_emitted"])
        self.assertNotIn("raw_dom", result)
        self.assertNotIn("_captured_output", result)

    def test_flutter_report_renders_windows_runtime_status(self):
        report = RUNNER.render_flutter_report(
            {"status": "pending"},
            {"status": "pending"},
            [{"name": "windows_extension_model_e2e", "status": "pending", "reason": "windows_required"}],
            [],
            {"devices": []},
        )

        self.assertIn("## Windows extension–model runtime", report)
        self.assertIn("| windows_extension_model_e2e | pending |", report)
        self.assertIn("windows_required", report)
        self.assertIn("raw URL, DOM, token, screenshot", report)

    def test_component_selection_targets_only_browser_extension(self):
        self.assertEqual(
            {"extension_unit"},
            RUNNER.check_names_for_components(["browser_extension"]),
        )
        self.assertEqual(
            {"browser-extention"},
            RUNNER.report_keys_for_components(["browser_extension"]),
        )

    def test_website_component_selection_includes_unit_and_e2e(self):
        self.assertEqual(
            {"website_unit", "website_e2e"},
            RUNNER.check_names_for_components(["website"]),
        )
        self.assertEqual({"next"}, RUNNER.report_keys_for_components(["website"]))

    def test_targeted_code_checks_run_only_browser_extension(self):
        with mock.patch.object(
            RUNNER,
            "run_command",
            return_value={"name": "extension_unit", "status": "passed"},
        ) as run_command:
            checks = RUNNER.run_code_checks(ROOT.parent, include_flutter=False, components=["browser_extension"])

        self.assertEqual(["extension_unit"], [check["name"] for check in checks])
        run_command.assert_called_once()
        self.assertEqual("extension_unit", run_command.call_args.args[0])
        self.assertEqual(ROOT.parent / "browser_extension", run_command.call_args.args[2])

    def test_targeted_backend_check_runs_full_backend_suite(self):
        with mock.patch.object(
            RUNNER,
            "run_command",
            return_value={"name": "backend_unit", "status": "passed"},
        ) as run_command:
            checks = RUNNER.run_code_checks(ROOT.parent, include_flutter=False, components=["backend"])

        self.assertEqual(["backend_unit", "backend_integration"], [check["name"] for check in checks])
        run_command.assert_called_once()
        self.assertEqual("backend_unit", run_command.call_args.args[0])
        self.assertEqual(["make", "test"], run_command.call_args.args[1])
        self.assertEqual(ROOT.parent / "gamblock-ai-backend", run_command.call_args.args[2])
        self.assertEqual("pending", checks[1]["status"])

    def test_targeted_backend_integration_runs_when_database_is_configured(self):
        with mock.patch.dict(os.environ, {"DATABASE_URL": "postgres://test"}, clear=False), mock.patch.object(
            RUNNER,
            "run_command",
            side_effect=[
                {"name": "backend_unit", "status": "passed"},
                {"name": "backend_integration", "status": "passed"},
            ],
        ) as run_command:
            checks = RUNNER.run_code_checks(ROOT.parent, include_flutter=False, components=["backend"])

        self.assertEqual(["backend_unit", "backend_integration"], [check["name"] for check in checks])
        self.assertEqual(2, run_command.call_count)
        self.assertEqual("backend_integration", run_command.call_args_list[1].args[0])
        self.assertEqual(["make", "test-integration"], run_command.call_args_list[1].args[1])

    def test_targeted_website_checks_run_unit_and_e2e(self):
        with mock.patch.object(
            RUNNER,
            "run_command",
            side_effect=[
                {"name": "website_unit", "status": "passed"},
                {"name": "website_e2e", "status": "passed"},
            ],
        ) as run_command:
            checks = RUNNER.run_code_checks(ROOT.parent, include_flutter=False, components=["website"])

        self.assertEqual(["website_unit", "website_e2e"], [check["name"] for check in checks])
        self.assertEqual(
            [
                mock.call(
                    "website_unit",
                    ["npm", "test"],
                    ROOT.parent / "gamblock-ai-website",
                    ROOT.parent,
                ),
                mock.call(
                    "website_e2e",
                    ["npm", "run", "e2e"],
                    ROOT.parent / "gamblock-ai-website",
                    ROOT.parent,
                ),
            ],
            run_command.call_args_list,
        )

    def test_website_report_renders_only_aggregate_check_status(self):
        report = RUNNER.render_component_report(
            "Gamblock-AI Next.js Report",
            "This report covers the Next.js website component checks.",
            [
                {
                    "name": "website_unit",
                    "status": "passed",
                    "output_sha256": "unit-hash",
                },
                {
                    "name": "website_e2e",
                    "status": "passed",
                    "output_sha256": "e2e-hash",
                    "output": "browser URL and account data must not appear",
                },
            ],
            RUNNER.COMPONENT_CHECK_NAMES["website"],
            "website_unit",
        )

        self.assertIn("| website_unit | passed |", report)
        self.assertIn("| website_e2e | passed |", report)
        self.assertNotIn("unit-hash", report)
        self.assertNotIn("e2e-hash", report)
        self.assertNotIn("browser URL and account data", report)

    def test_default_component_selection_preserves_all_reports(self):
        self.assertIsNone(RUNNER.check_names_for_components(None))
        self.assertEqual(set(RUNNER.REPORT_PATHS), RUNNER.report_keys_for_components(None))

    def test_model_evidence_paths_are_owned_by_testing_repository(self):
        self.assertEqual(RUNNER.MODEL_AGGREGATE_ROOT.parent, RUNNER.MODEL_EVIDENCE_ROOT)
        self.assertEqual(RUNNER.MODEL_VISUAL_ROOT.parent, RUNNER.MODEL_EVIDENCE_ROOT)
        self.assertEqual(RUNNER.MODEL_PRIVATE_ROOT.parent, RUNNER.TESTING_ROOT / "model")
        self.assertNotIn("gamblock-ai-model", str(RUNNER.MODEL_EVIDENCE_ROOT))

    def test_valid_evidence_and_retest_queue_are_separate(self):
        register = {
            "devices": [
                {
                    "device_alias": "pixel_9_pro_remote_01",
                    "display_name": "Google Pixel 9 Pro Remote",
                    "service": "firebase_test_lab_android_device_streaming",
                    "evidence_status": "valid_evidence",
                },
                {
                    "device_alias": "redmi_12c_local_01",
                    "display_name": "Redmi 12C",
                    "service": "local_physical_device",
                    "evidence_status": "pending_retest",
                    "retest_required": True,
                },
            ]
        }
        evidence = "\n".join(RUNNER.render_android_evidence_details([record()], register))
        queue = "\n".join(RUNNER.render_android_retest_queue(register))

        self.assertIn("Google Pixel 9 Pro Remote", evidence)
        self.assertIn("firebase_test_lab_android_device_streaming", evidence)
        self.assertNotIn("Redmi 12C", evidence)
        self.assertIn("Redmi 12C", queue)
        self.assertIn("pending_retest", queue)
        self.assertIn(" | — |", queue)

    def test_markdown_value_does_not_emit_empty_result_as_claim(self):
        self.assertEqual(RUNNER.markdown_value(None), "—")
        self.assertEqual(RUNNER.markdown_value("a|b"), "a\\|b")

    def test_model_report_renders_grouped_aggregate_sections(self):
        report = RUNNER.render_model_report(
            {"status": "passed", "aggregate": {"accuracy": 0.9}},
            {
                "status": "passed",
                "aggregate": {
                    "evidence_maturity": "provisional",
                    "samples": 10,
                    "accuracy": 0.9,
                    "precision": 0.9,
                    "recall": 0.8,
                    "f1_score": 0.85,
                    "false_positive_rate": 0.1,
                    "numeric_gate_passed": False,
                    "split_audit_passed": False,
                    "onnx_parity": "failed",
                    "ablations": {"rule_only": {"samples": 10, "status": "failed"}},
                    "slices": {"invalid_url": {"samples": 0, "metrics": {"status": "pending"}}},
                },
            },
            [{"name": "model_tooling_unit", "status": "passed"}],
        )
        self.assertNotIn("## Model replay", report)
        self.assertIn("## Text-and-domain grouped candidate", report)
        self.assertIn("## Text-and-domain grouped ablations", report)
        self.assertIn("rule_only", report)
        self.assertNotIn("time_shift", report)
        self.assertNotIn("https://", report)

    def test_model_report_renders_new_aggregate_evaluations(self):
        report = RUNNER.render_model_report(
            {"status": "passed"},
            {
                "status": "passed",
                "aggregate": {
                    "camouflage": {
                        "variants": {"case_variation": {"samples": 4, "accuracy": 1.0}}
                    },
                    "threshold_sensitivity": {
                        "results": [{"threshold": 0.55, "selected": True}]
                    },
                    "calibration": {"status": "reported", "samples": 4},
                    "repeated_grouped_cv": {
                        "folds": 5,
                        "repetitions": 3,
                        "total_evaluations": 15,
                        "summary": {"status": "failed", "mean": {}},
                    },
                    "leakage_audit": {"audit_passed": False},
                    "offline_speed": {"status": "reported", "runs": 5},
                    "visuals": {
                        "status": "created",
                        "files": {"confusion_matrix": {"bytes": 10, "sha256": "hash"}},
                    },
                    "scope_exclusions": {"runtime_device_evaluation": "out_of_scope"},
                },
            },
            [],
        )
        for section in (
            "## Camouflage robustness",
            "## Threshold sensitivity",
            "## Calibration",
            "## Repeated grouped validation",
            "## Duplicate and leakage audit",
            "## Offline inference speed",
            "## Visual artifacts",
            "## Scope exclusions",
        ):
            self.assertIn(section, report)
        self.assertIn("case_variation", report)
        self.assertNotIn("https://", report)


if __name__ == "__main__":
    unittest.main()
