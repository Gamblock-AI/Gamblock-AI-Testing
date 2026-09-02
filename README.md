# Gamblock-AI Testing

Cross-repository evaluation and privacy-safe runtime evidence for Gamblock-AI.
The repository covers model replay, passive runtime/latency evidence, Android
Research anti-uninstall behavior, and aggregate component verification.

The canonical result is [`reports/testing-summary.md`](reports/testing-summary.md).
The JSONL files under [`evidence/ledger/`](evidence/ledger/) are source records,
not a second summary. Component repositories link here instead of copying test
results.

## Layout

| Path | Responsibility |
|---|---|
| `config/device-matrix.json` | Required OEM/API/scenario coverage |
| `evidence/ledger/` | Public aggregate-only records |
| `reports/testing-summary.md` | Single canonical human summary |
| `scripts/` | Validators, runners, and evidence promotion |
| `tests/` | Tests for the evaluation tooling |
| `docs/ai/` | AI context and Android/Firebase runbook |

## Run from the umbrella

```sh
python3 gamblock-ai-testing/scripts/run_evaluation.py \
  --workspace-root . \
  --output gamblock-ai-testing/reports/testing-summary.md
python3 gamblock-ai-testing/scripts/verify_public_evidence.py
```

The evaluation runner records missing physical-device and Windows evidence as
`pending`; it never upgrades documentation-only claims to runtime proof.

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

Public records contain only anonymized labels, outcomes, supported state flags,
durations, and hashes. URLs, DOM, browsing history, screenshots, serials,
credentials, participant information, and raw logs remain local and are
rejected by CI.
