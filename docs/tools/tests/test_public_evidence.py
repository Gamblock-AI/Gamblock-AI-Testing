import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[3]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


VALIDATOR = load("android_validator", ROOT / "flutter/scripts/validate_android_tamper_report.py")
PROMOTER = load("evidence_promoter", ROOT / "flutter/scripts/promote_evidence.py")
PUBLIC = load("public_evidence", ROOT / "docs/tools/verify_public_evidence.py")


def record(**overrides):
    value = {
        "schema_version": 1,
        "report_kind": "android_tamper_run",
        "run_id": "run_1",
        "sample_id": "sample_1",
        "device_alias": "pixel_baseline",
        "oem_family": "aosp",
        "android_api": 35,
        "flavor": "research",
        "build_mode": "debug",
        "scenario": "settings_uninstall",
        "surface": "settings",
        "action": "uninstall",
        "observed_action": "uninstall",
        "expected_outcome": "blocked",
        "actual_outcome": "warned",
        "result": "passed",
        "grant_state": "none",
        "admin_active_before": True,
        "admin_active_after": True,
        "accessibility_enabled_before": True,
        "accessibility_enabled_after": True,
        "service_running_before": True,
        "service_running_after": True,
        "app_present_after": True,
        "evidence_reference": "settings_guard",
    }
    value.update(overrides)
    return value


class PublicEvidenceTest(unittest.TestCase):
    def test_accepts_safe_device_register(self):
        value = {
            "schema_version": 1,
            "scope": "android_research_anti_uninstall",
            "devices": [
                {
                    "device_alias": "redmi_12c_local_01",
                    "display_name": "Redmi 12C",
                    "oem_family": "xiaomi_redmi",
                    "source": "local_physical_device",
                    "service": "local_physical_device",
                    "access_path": "local_adb",
                    "evidence_status": "pending_retest",
                    "android_api": None,
                    "build_mode": None,
                    "retest_required": True,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "device-register.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(PUBLIC.validate_device_register(path), [])

    def test_rejects_result_in_device_register(self):
        value = {
            "schema_version": 1,
            "scope": "android_research_anti_uninstall",
            "devices": [
                {
                    "device_alias": "redmi_12c_local_01",
                    "display_name": "Redmi 12C",
                    "oem_family": "xiaomi_redmi",
                    "source": "local_physical_device",
                    "service": "local_physical_device",
                    "access_path": "local_adb",
                    "evidence_status": "pending_retest",
                    "android_api": None,
                    "build_mode": None,
                    "retest_required": True,
                    "result": "passed",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "device-register.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            errors = PUBLIC.validate_device_register(path)
        self.assertTrue(any("unexpected fields" in error for error in errors))

    def test_rejects_mismatched_device_service(self):
        value = {
            "schema_version": 1,
            "scope": "android_research_anti_uninstall",
            "devices": [
                {
                    "device_alias": "pixel_9_pro_remote_01",
                    "display_name": "Google Pixel 9 Pro Remote",
                    "oem_family": "aosp",
                    "source": "firebase_test_lab",
                    "service": "local_physical_device",
                    "access_path": "android_studio_remote_devices",
                    "evidence_status": "valid_evidence",
                    "android_api": 35,
                    "build_mode": "debug",
                    "retest_required": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "device-register.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            errors = PUBLIC.validate_device_register(path)
        self.assertTrue(any("requires Android Device Streaming" in error for error in errors))

    def test_promoter_adds_only_visual_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = pathlib.Path(directory)
            visual = directory / "local.png"
            visual.write_bytes(b"local-only")
            promoted = PROMOTER.promote(
                [record()],
                {"sample_1": PROMOTER.sha256(visual)},
                VALIDATOR,
            )
        self.assertTrue(promoted[0]["visual_evidence_present"])
        self.assertEqual(len(promoted[0]["visual_evidence_sha256"]), 64)
        self.assertNotIn("path", json.dumps(promoted[0]).lower())

    def test_promoter_rejects_browsing_fields(self):
        with self.assertRaises(ValueError):
            PROMOTER.promote([record(url="https://never-record.invalid")], {}, VALIDATOR)

    def test_public_scanner_rejects_nested_screenshot(self):
        errors = PUBLIC.forbidden_nested_values({"evidence": {"screenshot": "raw"}})
        self.assertTrue(any("screenshot" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
