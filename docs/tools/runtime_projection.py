#!/usr/bin/env python3
"""Evaluate the deployed Windows extension-to-client Hybrid-v2 projection.

The evaluator consumes checked-in test HTML only locally, then emits aggregate
metrics and artifact hashes. Raw URLs, DOM snapshots, and dataset row IDs are
never written to its output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


TESTING_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = TESTING_ROOT.parent
MODEL_ROOT = WORKSPACE_ROOT / "gamblock-ai-model"
APP_ROOT = WORKSPACE_ROOT / "gamblock_ai_apps"
TARGETS_PATH = TESTING_ROOT / "docs/config/targets.json"


def configure_workspace(
    workspace_root: Path,
    targets_path: Path | None = None,
) -> None:
    """Point the evaluator at an umbrella or standalone sibling workspace."""

    global WORKSPACE_ROOT, MODEL_ROOT, APP_ROOT, TARGETS_PATH
    WORKSPACE_ROOT = workspace_root.resolve()
    MODEL_ROOT = WORKSPACE_ROOT / "gamblock-ai-model"
    APP_ROOT = WORKSPACE_ROOT / "gamblock_ai_apps"
    TARGETS_PATH = (
        targets_path.resolve()
        if targets_path is not None
        else TESTING_ROOT / "docs/config/targets.json"
    )
    try:
        configuration = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"target configuration could not be read: {TARGETS_PATH}: {error}") from error
TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")
RULE_SEPARATOR_RE = re.compile(r"[^a-z0-9_]+")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configured_detection_gates() -> dict[str, dict[str, float]]:
    value = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    detection = value["detection"]
    return {
        name: {key: float(threshold) for key, threshold in thresholds.items()}
        for name, thresholds in detection.items()
    }


def evaluate_gates(metrics: dict[str, float]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, thresholds in configured_detection_gates().items():
        checks = {
            "accuracy": metrics["accuracy"] >= thresholds["accuracy_min"],
            "precision": metrics["precision"] >= thresholds["precision_min"],
            "recall": metrics["recall"] >= thresholds["recall_min"],
            "f1_score": metrics["f1_score"] >= thresholds["f1_score_min"],
            "false_positive_rate": metrics["false_positive_rate"] <= thresholds["false_positive_rate_max"],
        }
        result[name] = {
            "criteria": thresholds,
            "checks": checks,
            "passed": all(checks.values()),
        }
    return result


def artifact_contract(model_path: Path, rules_path: Path, model: dict[str, Any]) -> dict[str, Any]:
    """Describe the actual serialized Hybrid artifacts used by this evaluator.

    This is an artifact-integrity check, not a physical Android/Windows runtime
    observation. Runtime coverage remains a separate client-runtime contract.
    """

    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))["hybrid_artifact"]
    source_onnx = MODEL_ROOT / "models/gamblock_logistic_regression.onnx"
    source_onnx_sha256 = sha256(source_onnx) if source_onnx.is_file() else None
    declared_source_onnx_sha256 = model.get("source_onnx_sha256")
    combined_bytes = model_path.stat().st_size + rules_path.stat().st_size
    max_combined_bytes = int(targets["max_combined_bytes_exclusive"])
    return {
        "runtime_format": targets["runtime_format"],
        "runtime_artifact_count": 2,
        "model_bytes": model_path.stat().st_size,
        "rules_bytes": rules_path.stat().st_size,
        "combined_bytes": combined_bytes,
        "max_combined_bytes_exclusive": max_combined_bytes,
        "size_passed": combined_bytes < max_combined_bytes,
        "declared_source_onnx_sha256": declared_source_onnx_sha256,
        "source_onnx_sha256": source_onnx_sha256,
        "source_onnx_present": source_onnx_sha256 is not None,
        "source_onnx_matches_declared_hash": (
            source_onnx_sha256 is not None and source_onnx_sha256 == declared_source_onnx_sha256
        ),
        "required_runtime_platforms": targets["required_platforms"],
        "runtime_platform_coverage_observed": [],
        "runtime_platform_coverage_complete": False,
        "scope": "offline artifact integrity only; physical runtime coverage is not asserted",
    }


def truncate_utf8(value: str, maximum_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return value
    result: list[str] = []
    used = 0
    for character in value:
        size = len(character.encode("utf-8"))
        if used + size > maximum_bytes:
            break
        result.append(character)
        used += size
    return "".join(result)


class ExtensionDOMExtractor(HTMLParser):
    """Small local equivalent of the passive extension's DOM extractor."""

    tracked_tags = {"title", "h1", "h2", "h3", "a"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, list[str]]] = []
        self.active: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() in self.tracked_tags:
            block = (tag.lower(), [])
            self.blocks.append(block)
            self.active.append(block)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.active) - 1, -1, -1):
            if self.active[index][0] == tag.lower():
                del self.active[index]
                return

    def handle_data(self, data: str) -> None:
        for _, text in self.active:
            text.append(data)

    def snapshot(self) -> tuple[str, list[str], list[str]]:
        title = ""
        headings: list[str] = []
        anchors: list[str] = []
        for tag, pieces in self.blocks:
            value = "".join(pieces).strip()
            if not value:
                continue
            if tag == "title" and not title:
                title = value
            elif tag in {"h1", "h2", "h3"} and len(headings) < 10:
                headings.append(value)
            elif tag == "a" and len(value) < 200 and len(anchors) < 50:
                anchors.append(value)
        return title, headings, anchors


def extract_extension_snapshot(html: str, url: str) -> dict[str, Any]:
    parser = ExtensionDOMExtractor()
    parser.feed(html)
    parser.close()
    title, headings, anchors = parser.snapshot()
    # This mirrors extension background bounds followed by the client bounds.
    bounded_url = truncate_utf8(url, 2048)[:2048]
    bounded_title = truncate_utf8(title, 512).strip()[:512]
    bounded_headings = [truncate_utf8(value, 192).strip()[:256] for value in headings]
    bounded_anchors = [truncate_utf8(value, 160).strip()[:256] for value in anchors]
    bounded_headings = [value for value in bounded_headings if value][:32]
    bounded_anchors = [value for value in bounded_anchors if value][:64]
    return {
        "url": bounded_url,
        "title": bounded_title,
        "headings": bounded_headings,
        "anchor_texts": bounded_anchors,
        "has_dom_content": bool(bounded_title or bounded_headings or bounded_anchors),
    }


def normalize_for_rules(value: str) -> str:
    return RULE_SEPARATOR_RE.sub(" ", value.lower()).strip()


def contains_phrase(haystack: str, needle: str) -> bool:
    return bool(needle) and f" {needle} " in f" {haystack} "


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def url_feature_values(url: str, keyword_count: int) -> dict[str, float]:
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        scheme, hostname = "", ""
    labels = [label for label in hostname.split(".") if label]
    suffix = labels[-1] if labels else ""
    subdomain = ".".join(labels[:-2]) if len(labels) > 2 else ""
    return {
        "url_length": float(len(url)),
        "url_digit_count": float(sum(character.isdigit() for character in url)),
        "url_dot_count": float(url.count(".")),
        "url_slash_count": float(url.count("/")),
        "url_hyphen_count": float(url.count("-")),
        "url_question_count": float(url.count("?")),
        "url_equal_count": float(url.count("=")),
        "url_keyword_count": float(keyword_count),
        "url_has_number": 1.0 if any(character.isdigit() for character in url) else 0.0,
        "url_has_https": 1.0 if scheme == "https" else 0.0,
        "url_is_valid": 1.0 if scheme in {"http", "https"} and bool(hostname) else 0.0,
        "domain_length": float(len(hostname)),
        "subdomain_length": float(len(subdomain)),
        "suffix_length": float(len(suffix)),
    }


def classify(snapshot: dict[str, Any], model: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    document = " ".join(
        [snapshot["title"], *snapshot["headings"], *snapshot["anchor_texts"]]
    )
    tokens = TOKEN_RE.findall(document.lower())
    unigrams = Counter(tokens)
    bigrams = Counter(f"{left} {right}" for left, right in zip(tokens, tokens[1:]))
    normalized_url = normalize_for_rules(snapshot["url"])
    normalized_document = normalize_for_rules(document)
    keywords = [normalize_for_rules(keyword) for keyword in rules["keywords"]]
    url_keyword_count = sum(contains_phrase(normalized_url, keyword) for keyword in keywords)
    rule_input = f"{normalized_url} {normalized_document}".strip()
    rule_score = float(rules["match_score"]) if any(
        contains_phrase(rule_input, keyword) for keyword in keywords
    ) else 0.0

    linear = float(model["bias"])
    for token, count in unigrams.items():
        linear += float(model["unigram_weights"].get(token, 0.0)) * count
    for token, count in bigrams.items():
        linear += float(model["bigram_weights"].get(token, 0.0)) * count
    content_model_score = sigmoid(linear)
    feature_values = url_feature_values(snapshot["url"], url_keyword_count)
    for feature in model["url_features"]:
        value = feature_values.get(feature["name"], 0.0)
        linear += (value - float(feature["offset"])) * float(feature["scale"]) * float(feature["weight"])
    model_score = sigmoid(linear)
    hybrid_score = float(model["ml_weight"]) * model_score + float(model["rule_weight"]) * rule_score
    threshold = float(model["threshold"])
    block = hybrid_score >= threshold and (
        rule_score > 0.0 or (snapshot["has_dom_content"] and content_model_score >= threshold)
    )
    return {
        "block": block,
        "model_only_block": snapshot["has_dom_content"] and content_model_score >= threshold,
        "rule_only_block": rule_score > 0.0,
        "model_score": model_score,
        "content_model_score": content_model_score,
        "rule_score": rule_score,
        "hybrid_score": hybrid_score,
    }


def metric_summary(actual: list[int], predicted: list[bool]) -> dict[str, Any]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("metric inputs must be equal and non-empty")
    tp = sum(label == 1 and guess for label, guess in zip(actual, predicted))
    tn = sum(label == 0 and not guess for label, guess in zip(actual, predicted))
    fp = sum(label == 0 and guess for label, guess in zip(actual, predicted))
    fn = sum(label == 1 and not guess for label, guess in zip(actual, predicted))
    accuracy = (tp + tn) / len(actual)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    metrics = {
        "samples": len(actual),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_positive_rate": false_positive_rate,
    }
    metrics["gates"] = evaluate_gates(metrics)
    return metrics


def host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def build_report(
    model_path: Path | None = None,
    rules_path: Path | None = None,
    fixtures_path: Path | None = None,
) -> dict[str, Any]:
    target_configuration = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    target_id = str(
        target_configuration.get("detection_progress_target_id", "detection-progress")
    )
    model_path = model_path or APP_ROOT / "assets/protection/gamblock-lr-v2.json"
    rules_path = rules_path or APP_ROOT / "assets/protection/gamblock-rules-v2.json"
    fixtures_path = fixtures_path or APP_ROOT / "assets/protection/hybrid-v2-fixtures.json"
    test_path = MODEL_ROOT / "data/processed/splits/test.csv"
    train_path = MODEL_ROOT / "data/processed/splits/train.csv"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))

    fixture_passed = 0
    for fixture in fixtures:
        snapshot = {
            "url": fixture["url"][:2048],
            "title": fixture["title"][:512],
            "headings": fixture["headings"][:32],
            "anchor_texts": fixture["anchorTexts"][:64],
            "has_dom_content": bool(fixture["title"] or fixture["headings"] or fixture["anchorTexts"]),
        }
        decision = "block" if classify(snapshot, model, rules)["block"] else "allow"
        fixture_passed += decision == fixture["expected"]

    rows = read_csv(test_path)
    train_hosts = {host(row["url"]) for row in read_csv(train_path)} - {""}
    actual: list[int] = []
    deployed: list[bool] = []
    model_only: list[bool] = []
    rule_only: list[bool] = []
    isolated_actual: list[int] = []
    isolated_deployed: list[bool] = []
    missing_html = 0
    for row in rows:
        html_path = MODEL_ROOT / row["html_path"]
        try:
            html = html_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            missing_html += 1
            continue
        result = classify(extract_extension_snapshot(html, row["url"]), model, rules)
        label = int(row["label"])
        actual.append(label)
        deployed.append(result["block"])
        model_only.append(result["model_only_block"])
        rule_only.append(result["rule_only_block"])
        if host(row["url"]) not in train_hosts:
            isolated_actual.append(label)
            isolated_deployed.append(result["block"])

    if missing_html:
        raise RuntimeError(f"{missing_html} test HTML files are missing")
    return {
        "schema_version": 1,
        "report_kind": "deployed_hybrid_projection",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_configuration": {
            "progress_gate": "progress_gate",
            "target_id": target_id,
            "path_class": "current_testing_config",
        },
        "evidence_maturity": "provisional",
        "projection": {
            "route": "browser_extension DOM snapshot -> bounded loopback payload -> Windows Hybrid-v2",
            "scope": "offline replay of the frozen model test HTML; no device/browser timing or intervention runtime claim",
            "raw_url_or_dom_emitted": False,
            "participant_data_emitted": False,
        },
        "artifacts": {
            "model_version": model["version"],
            "ruleset_version": rules["version"],
            "model_sha256": sha256(model_path),
            "rules_sha256": sha256(rules_path),
            "fixtures_sha256": sha256(fixtures_path),
        },
        "artifact_contract": artifact_contract(model_path, rules_path, model),
        "fixture_contract": {
            "samples": len(fixtures),
            "passed": fixture_passed,
            "all_passed": fixture_passed == len(fixtures),
        },
        "evaluation": {
            "test_rows_declared": len(rows),
            "test_rows_evaluated": len(actual),
            "missing_html_rows": missing_html,
            "deployed_hybrid": metric_summary(actual, deployed),
            "model_only_content_gate": metric_summary(actual, model_only),
            "rule_only": metric_summary(actual, rule_only),
            "exact_host_isolated_deployed_hybrid": metric_summary(isolated_actual, isolated_deployed),
            "excluded_exact_host_overlap_rows": len(actual) - len(isolated_actual),
        },
        "limitations": [
            "The frozen split has exact hostname overlap between train and test and incomplete dataset provenance.",
            "The projection reproduces the extension-to-Windows bounded input contract, not Android accessibility extraction.",
            "Metrics are offline artifact evidence and do not prove browser, Windows service, blocking, or Pattern Interrupt runtime behavior.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--output", type=Path, default=TESTING_ROOT / "reports/.generated/runtime_projection.json")
    parser.add_argument("--model", type=Path, help="Candidate Hybrid-v2 JSON model; defaults to the app artifact.")
    parser.add_argument("--rules", type=Path, help="Candidate Hybrid-v2 JSON rules; defaults to the app artifact.")
    parser.add_argument("--fixtures", type=Path, help="Fixture JSON; defaults to the app fixture contract.")
    parser.add_argument(
        "--targets-config",
        type=Path,
        help="Target configuration; defaults to the active current config.",
    )
    args = parser.parse_args()
    configure_workspace(args.workspace_root, args.targets_config)
    report = build_report(args.model, args.rules, args.fixtures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "evaluated": report["evaluation"]["test_rows_evaluated"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
