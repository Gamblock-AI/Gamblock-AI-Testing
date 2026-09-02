import importlib.util
import pathlib
import unittest


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


if __name__ == "__main__":
    unittest.main()
