# Testing Repository AI Context

Context version: `2026-09-04.4`

This repository is the canonical owner of Gamblock-AI cross-repository test
orchestration and public evidence. It does not own product runtime code.

## Capability status

| Area | State | Evidence boundary |
|---|---|---|
| Model evaluation | Implemented tooling | Deployment projection and domain-grouped evidence expose separate `developmental_checkpoint` (90%/5%) and `pkm_progress_v5` (95%/2%) gates; offline/projection evidence only, not physical browser, Android, or Windows proof. |
| Model evidence storage | Implemented | Permanent aggregate JSON is stored under `model/evidence/aggregate/` and allowlisted aggregate-generated charts under `model/evidence/visuals/`; raw replay inputs remain in ignored `model/private/`. |
| Phase 4 latency validation | Implemented tooling | Requires privacy-safe JSONL and renders separate feasibility, PKM v5 `researchRelease` Android/Chrome progress-demo, and retained Android/Windows final-readiness gates. |
| Structured usability + SUS | Planned protocol | Requires campus/authority confirmation before recruitment; only approved aggregates may later be disclosed. |
| Android anti-uninstall matrix | Harness implemented; OEM runtime coverage pending | Manual system UI and lifecycle actions are recorded only after explicit device execution. Valid evidence and the retest queue are rendered separately. |
| Windows extension–model runtime | Harness implemented; VM runtime pending | Chrome Release smoke test covers the real extension, authenticated loopback service, current Hybrid-v2 artifact, and intervention path. It requires an interactive Windows VM and is recorded in the Flutter report. |
| Component verification | Orchestrated | Component repositories remain owners of their unit tests and lint checks; the website check includes the complete Vitest and Playwright E2E suites. |
| Per-technology reports | Implemented | Each technology owns only `<technology>/report.md`; `docs/testing-index.md` is link-only. Every explicit run also requires a final test receipt, without creating another report. |

## Required context

1. `AGENTS.md` — repository rules and privacy boundary.
2. `README.md` — onboarding and commands.
3. `docs/ai/android-anti-uninstall-testing.md` — device matrix and runbook.
4. `docs/ai/android-anti-uninstall-context.md` — cross-OEM problem and service context.
5. `docs/ai/testing-run-receipt.md` — mandatory test handoff fields.
6. `docs/ai/pkm-usability-testing.md` — planned task and SUS study boundary.
7. `docs/ai/manifest.yaml` — context version and validation contract.
7. `flutter/config/device-matrix.json` — Android coverage requirements.
8. `flutter/config/device-register.json` — safe device/provenance register.
9. `docs/config/targets.json` — active v5 machine-readable gates.
10. `../context/progress-targets.md` — umbrella target registry and report-version boundary.

The test implementation is separated by system: `flutter/`, `golang/`,
`next/`, `browser-extention/`, and `windows/` describe or contain system-specific checks;
`docs/tools/` is the only place that combines their aggregate statuses. It
writes each technology report directly and does not write a global summary.
For model evaluation, the same runner also writes permanent aggregate evidence
and approved charts only to `model/evidence/`; it never writes retained
model results back into the model source repository.

## Required test handoff

### Read-only audit semantics

“Cek”, “periksa”, “review”, and “audit” mean inspect-only: read test source,
configuration, workflows, existing reports/evidence, repository status, and
runbooks, then summarize recorded coverage and pending gaps. Do not invoke a
test command, build, package check, model replay, device/VM procedure, or
`run_evaluation.py` for such a request. Existing report statuses must be
identified as recorded and may be stale.

Execution or report regeneration requires an explicit request to run/execute,
test, validate, re-evaluate, or record new evidence. Do not broaden an
explicitly named scope to other technologies.

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
