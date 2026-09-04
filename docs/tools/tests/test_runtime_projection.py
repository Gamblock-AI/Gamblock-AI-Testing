from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import runtime_projection as projection


class RuntimeProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        artifact_dir = projection.APP_ROOT / "assets/protection"
        self.model = json.loads((artifact_dir / "gamblock-lr-v2.json").read_text())
        self.rules = json.loads((artifact_dir / "gamblock-rules-v2.json").read_text())

    def test_checked_in_contract_fixtures(self) -> None:
        fixtures = json.loads((projection.APP_ROOT / "assets/protection/hybrid-v2-fixtures.json").read_text())
        for fixture in fixtures:
            with self.subTest(fixture=fixture["name"]):
                snapshot = {
                    "url": fixture["url"],
                    "title": fixture["title"],
                    "headings": fixture["headings"],
                    "anchor_texts": fixture["anchorTexts"],
                    "has_dom_content": bool(fixture["title"] or fixture["headings"] or fixture["anchorTexts"]),
                }
                result = projection.classify(snapshot, self.model, self.rules)
                self.assertEqual(fixture["expected"], "block" if result["block"] else "allow")

    def test_extension_projection_applies_public_bounds(self) -> None:
        html = "<title> Judul </title><h1> Satu </h1><a> Tautan </a>"
        snapshot = projection.extract_extension_snapshot(html, "https://example.test/" + "a" * 3000)
        self.assertEqual("Judul", snapshot["title"])
        self.assertEqual(["Satu"], snapshot["headings"])
        self.assertEqual(["Tautan"], snapshot["anchor_texts"])
        self.assertEqual(2048, len(snapshot["url"]))

    def test_active_artifact_contract_uses_serialized_hybrid_assets(self) -> None:
        artifact_dir = projection.APP_ROOT / "assets/protection"
        contract = projection.artifact_contract(
            artifact_dir / "gamblock-lr-v2.json",
            artifact_dir / "gamblock-rules-v2.json",
            self.model,
        )
        self.assertEqual("serialized_hybrid_json", contract["runtime_format"])
        self.assertTrue(contract["size_passed"])
        self.assertTrue(contract["source_onnx_matches_declared_hash"])
        self.assertFalse(contract["runtime_platform_coverage_complete"])

    def test_metrics_expose_named_progress_gates(self) -> None:
        metrics = projection.metric_summary([1] * 95 + [0] * 5, [1] * 95 + [0] * 5)
        self.assertTrue(metrics["gates"]["developmental_checkpoint"]["passed"])
        self.assertTrue(metrics["gates"]["pkm_progress_v5"]["passed"])


if __name__ == "__main__":
    unittest.main()
