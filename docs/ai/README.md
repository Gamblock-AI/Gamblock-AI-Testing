# Testing Repository AI Context

Context version: `2026-09-02.5`

This repository is the canonical owner of Gamblock-AI cross-repository test
orchestration and public evidence. It does not own product runtime code.

## Capability status

| Area | State | Evidence boundary |
|---|---|---|
| Model and runtime replay | Implemented tooling | Offline/projection evidence only; it is not physical browser, Android, or Windows proof. |
| Phase 4 latency validation | Implemented tooling | Requires privacy-safe JSONL and the configured p95/sample gate. |
| Android anti-uninstall matrix | Harness implemented; OEM runtime coverage pending | Manual system UI and lifecycle actions are recorded only after explicit device execution. Valid evidence and the retest queue are rendered separately. |
| Component verification | Orchestrated | Component repositories remain owners of their unit tests and lint checks. |
| Per-technology reports | Implemented | Each technology owns only `<technology>/report.md`; `docs/testing-index.md` is link-only. Every explicit run also requires a final test receipt, without creating another report. |

## Required context

1. `AGENTS.md` — repository rules and privacy boundary.
2. `README.md` — onboarding and commands.
3. `docs/ai/android-anti-uninstall-testing.md` — device matrix and runbook.
4. `docs/ai/android-anti-uninstall-context.md` — cross-OEM problem and service context.
5. `docs/ai/testing-run-receipt.md` — mandatory test handoff fields.
6. `docs/ai/manifest.yaml` — context version and validation contract.
7. `flutter/config/device-matrix.json` — Android coverage requirements.
8. `flutter/config/device-register.json` — safe device/provenance register.
9. `docs/config/targets.json` — shared detection and latency targets.

The test implementation is separated by system: `flutter/`, `golang/`,
`next/`, and `browser-extention/` describe or contain system-specific checks;
`docs/tools/` is the only place that combines their aggregate statuses. It
writes each technology report directly and does not write a global summary.

## Required test handoff

An explicit test/evaluation request is complete only after the matching
technology report is regenerated, or the report is left `pending`/`blocked`
with the exact reason documented in the handoff. See
[`testing-run-receipt.md`](testing-run-receipt.md) for the mandatory receipt
fields. The receipt is delivered by the agent and is not a second committed
summary.

## Evidence ownership

Component documentation may state implementation status and link to its
technology report, but must not copy run-specific tables or numbers. The
umbrella stores context and the submodule pointer; this repository stores each
technology's ledger and report.

## Verification

```sh
./docs/tools/verify-ai-context.sh
python3 docs/tools/verify_public_evidence.py
```

Do not run Firebase reservations, builds, or device lifecycle commands as part
of ordinary documentation or static verification.
