import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[3]
SPEC = importlib.util.spec_from_file_location(
    "client_runtime_evidence",
    ROOT / "docs/tools/client_runtime_evidence.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def browser_target():
    return {
        "required_platforms": ["android"],
        "optional_platforms": ["windows"],
        "required_devices": {"android": 1},
        "optional_devices": {"windows": 1},
        "required_build_modes": ["release"],
        "samples_per_class_per_browser": 2,
        "classes": ["gambling", "non_gambling"],
        "required_browsers": {
            "android": ["chrome"],
            "windows": ["chrome"],
        },
        "expected_outcomes": {
            "gambling": "intervention",
            "non_gambling": "allow",
        },
        "required_artifacts_by_platform": {
            "android": {"product_flavor": "research", "artifact": "researchRelease"},
            "windows": {"product_flavor": "pilot", "artifact": "windows-pilot-release"},
        },
        "evidence": {
            "root": "flutter/evidence/client-runtime/cross_platform_browser_support_regression",
        },
    }


def write_browser_cell(root, platform, browser, case, actual_outcomes, run_id="run_1"):
    directory = root / platform / browser / case
    expected_outcome = "intervention" if case == "gambling" else "allow"
    device_alias = f"{platform}_lab_01"
    product_flavor = "research" if platform == "android" else "pilot"
    artifact = "researchRelease" if platform == "android" else "windows-pilot-release"
    samples = []
    for index, actual_outcome in enumerate(actual_outcomes, 1):
        samples.append(
            {
                "schema_version": 1,
                "test": "cross_platform_browser_support_regression",
                "platform": platform,
                "browser": browser,
                "case": case,
                "device_alias": device_alias,
                "build_mode": "release",
                "product_flavor": product_flavor,
                "artifact": artifact,
                "run_id": run_id,
                "sample_id": f"{platform}_{browser}_{case}_{index}",
                "expected_outcome": expected_outcome,
                "actual_outcome": actual_outcome,
                "result": "passed" if actual_outcome == expected_outcome else "failed",
            }
        )
    write_json(
        directory / "summary.json",
        {
            "schema_version": 1,
            "test": "cross_platform_browser_support_regression",
            "platform": platform,
            "browser": browser,
            "case": case,
            "device_alias": device_alias,
            "build_mode": "release",
            "product_flavor": product_flavor,
            "artifact": artifact,
            "run_id": run_id,
            "sample_count": len(samples),
            "expected_outcome": expected_outcome,
            "passed_sample_count": sum(sample["result"] == "passed" for sample in samples),
            "status": "passed" if all(sample["result"] == "passed" for sample in samples) else "failed",
        },
    )
    (directory / "samples.jsonl").write_text(
        "".join(json.dumps(sample) + "\n" for sample in samples),
        encoding="utf-8",
    )


class ClientRuntimeEvidenceTest(unittest.TestCase):
    def test_android_required_cells_pass_without_optional_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/cross_platform_browser_support_regression"
            write_browser_cell(root, "android", "chrome", "gambling", ["intervention", "intervention"])
            write_browser_cell(root, "android", "chrome", "non_gambling", ["allow", "allow"])
            result = MODULE.aggregate_client_runtime(
                "cross_platform_browser_support_regression",
                browser_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("passed", result["status"])
        self.assertEqual("not_run", result["optional_platforms"]["windows"]["status"])

    def test_optional_windows_cells_are_accepted_and_non_gating(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/cross_platform_browser_support_regression"
            write_browser_cell(root, "android", "chrome", "gambling", ["intervention", "intervention"])
            write_browser_cell(root, "android", "chrome", "non_gambling", ["allow", "allow"])
            write_browser_cell(root, "windows", "chrome", "gambling", ["intervention", "intervention"])
            write_browser_cell(root, "windows", "chrome", "non_gambling", ["allow", "allow"])
            result = MODULE.aggregate_client_runtime(
                "cross_platform_browser_support_regression",
                browser_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("passed", result["status"])
        self.assertEqual("passed", result["optional_platforms"]["windows"]["status"])

    def test_optional_windows_failure_does_not_downgrade_android(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/cross_platform_browser_support_regression"
            write_browser_cell(root, "android", "chrome", "gambling", ["intervention", "intervention"])
            write_browser_cell(root, "android", "chrome", "non_gambling", ["allow", "allow"])
            write_browser_cell(root, "windows", "chrome", "gambling", ["allow", "allow"])
            write_browser_cell(root, "windows", "chrome", "non_gambling", ["allow", "allow"])
            result = MODULE.aggregate_client_runtime(
                "cross_platform_browser_support_regression",
                browser_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("passed", result["status"])
        self.assertEqual("failed", result["optional_platforms"]["windows"]["status"])

    def test_incomplete_required_android_remains_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/cross_platform_browser_support_regression"
            write_browser_cell(root, "android", "chrome", "gambling", ["intervention"])
            write_browser_cell(root, "android", "chrome", "non_gambling", ["allow", "allow"])
            result = MODULE.aggregate_client_runtime(
                "cross_platform_browser_support_regression",
                browser_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("pending", result["status"])
        self.assertEqual(1, result["missing_cells"])

    def test_public_schema_rejects_browsing_fields(self):
        errors = MODULE._forbidden_values({"actual_outcome": "allow", "url": "https://invalid.example"}, "sample")
        self.assertTrue(any("forbidden" in error or "URL-like" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
