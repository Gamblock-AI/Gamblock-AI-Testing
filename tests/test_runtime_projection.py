from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
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


if __name__ == "__main__":
    unittest.main()
