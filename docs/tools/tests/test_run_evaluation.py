import importlib.util
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
    def test_component_selection_targets_only_browser_extension(self):
        self.assertEqual(
            {"extension_unit"},
            RUNNER.check_names_for_components(["browser_extension"]),
        )
        self.assertEqual(
            {"browser-extention"},
            RUNNER.report_keys_for_components(["browser_extension"]),
        )

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

        self.assertEqual(["backend_unit"], [check["name"] for check in checks])
        run_command.assert_called_once()
        self.assertEqual("backend_unit", run_command.call_args.args[0])
        self.assertEqual(["make", "test"], run_command.call_args.args[1])
        self.assertEqual(ROOT.parent / "gamblock-ai-backend", run_command.call_args.args[2])

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
