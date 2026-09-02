import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "phase4_latency_report.py"
SPEC = importlib.util.spec_from_file_location("phase4_latency_report", SCRIPT)
REPORT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(REPORT)


def sample(**overrides):
    value = {
        "schema_version": 3,
        "platform": "android",
        "run_id": "run_1",
        "sample_id": "sample_1",
        "device_alias": "pixel_1",
        "scenario": "warm_foreground_online",
        "browser_family": "chrome",
        "build_mode": "profile",
        "model_version": "model_1",
        "ruleset_version": "rules_1",
        "outcome": "visible",
        "presentation_path": "native",
        "block_succeeded": True,
        "input_to_visible_ms": 120.0,
    }
    value.update(overrides)
    return value


class Phase4LatencyReportTest(unittest.TestCase):
    def test_nearest_rank_percentiles(self):
        self.assertEqual(REPORT.percentile([1.0, 2.0, 3.0, 4.0], 0.95), 4.0)
        self.assertEqual(REPORT.percentile([1.0, 2.0, 3.0, 4.0], 0.50), 2.0)

    def test_gate_requires_complete_successful_group(self):
        rows = [sample(sample_id=f"sample_{index}") for index in range(30)]
        result = REPORT.report(rows, minimum_samples=30, target_ms=200.0)
        self.assertTrue(result["passed"])

        rows[-1] = sample(sample_id="failed", outcome="expired", block_succeeded=False)
        failed = REPORT.report(rows, minimum_samples=29, target_ms=200.0)
        self.assertFalse(failed["passed"])

    def test_rejects_browsing_fields(self):
        errors = REPORT.validate_record(sample(url="https://never-record.invalid"), "evidence", 1)
        self.assertTrue(any("privacy allowlist" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
