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


def model_target():
    return {
        "required_platforms": ["android"],
        "required_build_modes": ["release"],
        "samples_per_class_per_platform": 2,
        "classes": ["gambling", "non_gambling"],
        "accuracy_min": 0.5,
        "precision_min": 0.5,
        "recall_min": 0.5,
        "f1_score_min": 0.5,
        "false_positive_rate_max": 0.5,
        "evaluation_scope": "deployed_hybrid_artifact",
        "required_components": ["rules", "url_features", "dom_text_features", "logistic_regression"],
        "required_artifacts_by_platform": {
            "android": {"product_flavor": "research", "artifact": "researchRelease"},
        },
        "evidence": {
            "root": "flutter/evidence/client-runtime/flutter_local_model_balanced_evaluation",
        },
    }


def write_model_cell(root, case, actual_classes, run_id="run_1"):
    directory = root / "android" / case
    samples = []
    for index, actual_class in enumerate(actual_classes, 1):
        samples.append({
            "schema_version": 1,
            "test": "flutter_local_model_balanced_evaluation",
            "platform": "android",
            "case": case,
            "device_alias": "android_lab_01",
            "build_mode": "release",
            "product_flavor": "research",
            "artifact": "researchRelease",
            "run_id": run_id,
            "sample_id": f"{case}_{index}",
            "expected_class": case,
            "actual_class": actual_class,
            "result": "passed" if actual_class == case else "failed",
        })
    write_json(
        directory / "summary.json",
        {
            "schema_version": 1,
            "test": "flutter_local_model_balanced_evaluation",
            "platform": "android",
            "case": case,
            "device_alias": "android_lab_01",
            "build_mode": "release",
            "product_flavor": "research",
            "artifact": "researchRelease",
            "run_id": run_id,
            "sample_count": len(samples),
            "expected_class": case,
            "correct_sample_count": sum(sample["result"] == "passed" for sample in samples),
            "evaluation_scope": "deployed_hybrid_artifact",
            "components": ["rules", "url_features", "dom_text_features", "logistic_regression"],
            "status": "passed" if all(sample["result"] == "passed" for sample in samples) else "failed",
        },
    )
    (directory / "samples.jsonl").write_text(
        "".join(json.dumps(sample) + "\n" for sample in samples),
        encoding="utf-8",
    )


class ClientRuntimeEvidenceTest(unittest.TestCase):
    def test_missing_root_is_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MODULE.aggregate_client_runtime("flutter_local_model_balanced_evaluation", model_target(), pathlib.Path(directory))
        self.assertEqual("pending", result["status"])

    def test_complete_model_cells_are_aggregated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/flutter_local_model_balanced_evaluation"
            write_model_cell(root, "gambling", ["gambling", "gambling"])
            write_model_cell(root, "non_gambling", ["non_gambling", "non_gambling"])
            result = MODULE.aggregate_client_runtime(
                "flutter_local_model_balanced_evaluation",
                model_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("passed", result["status"])
        self.assertEqual(1.0, result["metrics"]["accuracy"])

    def test_incomplete_cell_remains_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / "flutter/evidence/client-runtime/flutter_local_model_balanced_evaluation"
            write_model_cell(root, "gambling", ["gambling"])
            write_model_cell(root, "non_gambling", ["non_gambling", "non_gambling"])
            result = MODULE.aggregate_client_runtime(
                "flutter_local_model_balanced_evaluation",
                model_target(),
                pathlib.Path(directory),
            )
        self.assertEqual("pending", result["status"])
        self.assertEqual(1, result["missing_cells"])

    def test_public_schema_rejects_browsing_fields(self):
        errors = MODULE._forbidden_values({"actual_class": "gambling", "url": "https://invalid.example"}, "sample")
        self.assertTrue(any("forbidden" in error or "URL-like" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
