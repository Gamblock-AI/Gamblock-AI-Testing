# Gamblock-AI Testing

Cross-repository evaluation and privacy-safe runtime evidence for Gamblock-AI.
The repository covers model evaluation, passive runtime/latency evidence, Android
Research anti-uninstall behavior, and aggregate component verification.

Each technology owns one canonical aggregate report. The link-only index is
[`docs/testing-index.md`](docs/testing-index.md); JSONL files under a technology's
`evidence/ledger/` folder are source records, not alternate reports. Component
repositories link here instead of copying test results.

## Layout

| Path | Responsibility |
|---|---|
| `docs/config/targets.json` | Active v5 machine-readable detection/artifact/latency gates |
| `../context/progress-targets.md` | Versioned target registry; proposed v6 targets do not affect the v5 runner |
| `docs/testing-index.md` | Link-only index of canonical reports |
| `docs/tools/` | Cross-system runner, validators, and tooling tests |
| `flutter/` | Flutter/Android anti-uninstall and latency tooling/tests |
| `golang/` | Go backend test entrypoint and scope |
| `next/` | Next.js website test entrypoint and scope |
| `browser-extention/` | Browser extension test entrypoint and scope |
| `model/` | Model test entrypoint and scope |
| `model/evidence/aggregate/` | Model aggregate JSON evidence |
| `model/evidence/visuals/` | Allowlisted aggregate-generated model charts |
| `<technology>/report.md` | One canonical report per technology |
| `flutter/config/` and `flutter/evidence/` | Android matrix and public records |
| `docs/ai/` | AI context, Android/Firebase service context, and runbooks |

## Run from the umbrella

```sh
python3 gamblock-ai-testing/docs/tools/run_evaluation.py --workspace-root .
python3 gamblock-ai-testing/docs/tools/verify_public_evidence.py
```

The evaluation runner records missing physical-device and Windows evidence as
`pending`; it never upgrades documentation-only claims to runtime proof.

The report-version boundary and target lifecycle are maintained in the
umbrella's [`context/progress-targets.md`](../context/progress-targets.md).
Keep the v5 configuration active until a future report version explicitly
activates its approved targets.

For model evidence, use the explicit evaluation and unit-test flags:

```sh
python3 gamblock-ai-testing/docs/tools/run_evaluation.py \
  --workspace-root . --run-model-replay --run-model-tests
```

This regenerates the model report with runtime projection and separate
domain-grouped candidate evidence. The grouped
candidate report includes aggregate robustness, ablation, calibration,
threshold, leakage, repeated-validation, speed, and visual-artifact results.
All permanent model outputs are stored below `model/evidence/`; raw prediction
tables used as replay input remain only in the ignored `model/private/` staging
area. The grouped candidate is not an automatic replacement for the active
client artifact. The generated result distinguishes the 90%/5% developmental
gate from the stricter 95%/2% PKM v5 acceptance gate, and records the active
serialized Hybrid artifact's size/provenance contract. Device-runtime is an
explicit exclusion of this model progress run.

For every explicit test or evaluation, the agent must regenerate the matching
technology report, inspect the resulting diff, run the validators, and provide
a test receipt. The receipt must list public files added/modified and their
aggregate-safe contents, private/local artifacts and whether they were
deleted, plus validation, commit, and push status. It is a handoff record, not
an additional report. See
[`docs/ai/testing-run-receipt.md`](docs/ai/testing-run-receipt.md).

## Android anti-uninstall

Use the Research flavor only on a disposable emulator, cloud device, or loaner
device. The complete matrix, Firebase Device Streaming guidance, manual system
UI workflow, cross-OEM problem context, Firebase service context, and evidence promotion rules are in
[`docs/ai/android-anti-uninstall-testing.md`](docs/ai/android-anti-uninstall-testing.md).

The runner does not reserve a Firebase device automatically. A Firebase or
Android Studio session must be started manually after the matrix has been
reviewed, and its local evidence must be promoted through the allowlist
validator before publication.

## Progress-report usability study

The existing nine-student activity is retained as off-repository formative
feedback, not a quantitative usability result. The planned controlled task and
Indonesian SUS protocol is in
[`docs/ai/pkm-usability-testing.md`](docs/ai/pkm-usability-testing.md); it
requires governance confirmation before recruitment and permits no public raw
participant material.

## Public evidence policy

Public records and reports contain only anonymized labels, outcomes, supported
state flags, durations, metrics, and hashes. URLs, DOM, browsing history,
screenshots, serials, credentials, participant information, and raw logs remain
local and are rejected by the validator.
