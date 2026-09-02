import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "validate_android_tamper_report.py"
SPEC = importlib.util.spec_from_file_location("validate_android_tamper_report", SCRIPT)
REPORT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(REPORT)


def sample(**overrides):
    value = {
        "schema_version": 2,
        "report_kind": "android_tamper_run",
        "run_id": "run_1",
        "sample_id": "sample_1",
        "device_alias": "redmi_baseline",
        "oem_family": "xiaomi_redmi",
        "android_api": 34,
        "flavor": "research",
        "build_mode": "profile",
        "scenario": "settings_uninstall",
        "surface": "settings",
        "action": "uninstall",
        "observed_action": "uninstall",
        "expected_outcome": "blocked",
        "actual_outcome": "blocked",
        "result": "passed",
        "grant_state": "none",
        "admin_active_before": True,
        "admin_active_after": True,
        "accessibility_enabled_before": True,
        "accessibility_enabled_after": True,
        "service_running_before": True,
        "service_running_after": True,
        "app_present_after": True,
        "evidence_reference": "settings_uninstall_blocked",
        "visual_evidence_present": False,
    }
    value.update(overrides)
    return value


class AndroidTamperReportTest(unittest.TestCase):
    def test_valid_unapproved_removal_record(self):
        self.assertEqual(REPORT.validate_record(sample(), "evidence", 1), [])

    def test_rejects_browsing_fields(self):
        errors = REPORT.validate_record(sample(url="https://never-record.invalid"), "evidence", 1)
        self.assertTrue(any("privacy allowlist" in error for error in errors))

    def test_rejects_url_in_device_label(self):
        errors = REPORT.validate_record(
            sample(device_alias="https://never-record.invalid"),
            "evidence",
            1,
        )
        self.assertTrue(any("ASCII label" in error for error in errors))

    def test_rejects_valid_grant_for_invalid_scenario(self):
        errors = REPORT.validate_record(
            sample(scenario="invalid_grant_removal", grant_state="valid"),
            "evidence",
            1,
        )
        self.assertTrue(any("grant_state=valid" in error for error in errors))

    def test_valid_grant_requires_actual_removal(self):
        errors = REPORT.validate_record(
            sample(
                scenario="valid_grant_removal",
                surface="settings",
                action="uninstall",
                observed_action="uninstall",
                expected_outcome="allowed",
                actual_outcome="allowed",
                grant_state="valid",
                app_present_after=True,
            ),
            "evidence",
            1,
        )
        self.assertTrue(any("admin transition" in error for error in errors))

    def test_unapproved_removal_requires_device_admin_baseline(self):
        errors = REPORT.validate_record(sample(admin_active_before=False), "evidence", 1)
        self.assertTrue(any("admin_active_before=true" in error for error in errors))

    def test_passive_app_info_requires_no_tamper(self):
        errors = REPORT.validate_record(
            sample(
                scenario="app_info_passive",
                surface="app_info",
                action="none",
                observed_action="uninstall",
                expected_outcome="no_tamper",
                actual_outcome="warned",
            ),
            "evidence",
            1,
        )
        self.assertTrue(any("no_tamper" in error for error in errors))

    def test_summary_is_aggregate_only(self):
        result = REPORT.summarize([sample()])
        self.assertTrue(result["passed"])
        self.assertNotIn("sample_id", result["groups"][0])
        self.assertNotIn("evidence_reference", result["groups"][0])

    def test_rejects_invalid_visual_hash(self):
        errors = REPORT.validate_record(
            sample(visual_evidence_present=True, visual_evidence_sha256="not-a-hash"),
            "evidence",
            1,
        )
        self.assertTrue(any("SHA-256" in error for error in errors))

    def test_accepts_visual_hash_without_image(self):
        errors = REPORT.validate_record(
            sample(
                visual_evidence_present=True,
                visual_evidence_sha256="a" * 64,
            ),
            "evidence",
            1,
        )
        self.assertEqual(errors, [])

    def test_load_records_rejects_duplicate_sample_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "tamper.jsonl"
            path.write_text(
                "\n".join(json.dumps(sample(sample_id="same")) for _ in range(2)) + "\n",
                encoding="utf-8",
            )
            records, errors = REPORT.load_records([path])
        self.assertEqual(len(records), 1)
        self.assertTrue(any("duplicate sample_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
