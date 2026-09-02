# Gamblock-AI Testing

Cross-repository evaluation and privacy-safe runtime evidence for Gamblock-AI.
The repository covers model replay, passive runtime/latency evidence, Android
Research anti-uninstall behavior, and aggregate component verification.

Each technology owns one canonical aggregate report. The link-only index is
[`docs/testing-index.md`](docs/testing-index.md); JSONL files under a technology's
`evidence/ledger/` folder are source records, not alternate reports. Component
repositories link here instead of copying test results.

## Layout

| Path | Responsibility |
|---|---|
| `docs/config/targets.json` | Shared detection and latency targets |
| `docs/testing-index.md` | Link-only index of canonical reports |
| `docs/tools/` | Cross-system runner, validators, and tooling tests |
| `flutter/` | Flutter/Android anti-uninstall and latency tooling/tests |
| `golang/` | Go backend test entrypoint and scope |
| `next/` | Next.js website test entrypoint and scope |
| `browser-extention/` | Browser extension test entrypoint and scope |
| `model/` | Model test entrypoint and scope |
| `<technology>/report.md` | One canonical report per technology |
| `flutter/config/` and `flutter/evidence/` | Android matrix and public records |
| `docs/ai/` | AI context and Android/Firebase runbook |

## Run from the umbrella

```sh
python3 gamblock-ai-testing/docs/tools/run_evaluation.py --workspace-root .
python3 gamblock-ai-testing/docs/tools/verify_public_evidence.py
```

The evaluation runner records missing physical-device and Windows evidence as
`pending`; it never upgrades documentation-only claims to runtime proof.

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
UI workflow, and evidence promotion rules are in
[`docs/ai/android-anti-uninstall-testing.md`](docs/ai/android-anti-uninstall-testing.md).

The runner does not reserve a Firebase device automatically. A Firebase or
Android Studio session must be started manually after the matrix has been
reviewed, and its local evidence must be promoted through the allowlist
validator before publication.

## Public evidence policy

Public records and reports contain only anonymized labels, outcomes, supported
state flags, durations, metrics, and hashes. URLs, DOM, browsing history,
screenshots, serials, credentials, participant information, and raw logs remain
local and are rejected by the validator.
