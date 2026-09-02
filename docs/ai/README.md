# Testing Repository AI Context

Context version: `2026-09-02.1`

This repository is the canonical owner of Gamblock-AI cross-repository test
orchestration and public evidence. It does not own product runtime code.

## Capability status

| Area | State | Evidence boundary |
|---|---|---|
| Model and runtime replay | Implemented tooling | Offline/projection evidence only; it is not physical browser, Android, or Windows proof. |
| Phase 4 latency validation | Implemented tooling | Requires privacy-safe JSONL and the configured p95/sample gate. |
| Android anti-uninstall matrix | Harness implemented; OEM runtime coverage pending | Manual system UI and lifecycle actions are recorded only after explicit device execution. |
| Component verification | Orchestrated | Component repositories remain owners of their unit tests and lint checks. |
| Canonical summary | Implemented | Only `reports/testing-summary.md` is authoritative. |

## Required context

1. `AGENTS.md` — repository rules and privacy boundary.
2. `README.md` — onboarding and commands.
3. `docs/ai/android-anti-uninstall-testing.md` — device matrix and runbook.
4. `docs/ai/manifest.yaml` — context version and validation contract.
5. `config/device-matrix.json` — coverage requirements.

## Evidence ownership

Component documentation may state implementation status and link to the
canonical summary, but must not copy run-specific tables or numbers. The
umbrella stores context and the submodule pointer; this repository stores the
ledger and summary.

## Verification

```sh
./scripts/verify-ai-context.sh
python3 scripts/verify_public_evidence.py
```

Do not run Firebase reservations, builds, or device lifecycle commands as part
of ordinary documentation or static verification.
