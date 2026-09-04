# Gamblock-AI Testing Repository Rules

Context version: `2026-09-04.4`

This repository owns cross-repository test orchestration and public evidence
for Gamblock-AI. Product source code and production unit tests remain in their
component repositories; this repository owns the reproducible evaluation
workflow, privacy-safe evidence ledger, and one canonical report per
technology. The agent's final handoff also requires a test receipt; the
receipt is not a second report and is not committed by default.

## Source of truth

- `flutter/config/device-matrix.json` defines required Android device and
  scenario coverage.
- `<technology>/evidence/ledger/` contains public, aggregate-only evidence for
  that technology.
- Each technology's `<technology>/report.md` is its only human-readable
  canonical report; `docs/testing-index.md` is a link-only index.
- `docs/ai/` explains the workflow and current capability boundaries.
- The umbrella `../context/progress-targets.md` is the versioned target
  registry. `docs/config/targets.json` remains the active v5 machine
  configuration; proposed future targets must not be copied into it early.
- `docs/ai/pkm-usability-testing.md` defines the future structured task and
  SUS protocol; it contains no participant results or raw study material.
- Model replay is the exception to the runtime-ledger layout: its validated,
  aggregate-only evidence is stored under `model/evidence/aggregate/` and
  its allowlisted aggregate charts under `model/evidence/visuals/`.
  The canonical model report also exposes split-manifest integrity status and
  keeps repeated grouped validation labeled as fixed-candidate stability.

## Directory ownership

- `flutter/` owns Flutter/Android anti-uninstall, Android tamper, and Phase 4
  latency harnesses plus their tests.
- `golang/`, `next/`, and `browser-extention/` own the test entrypoint documentation for
  the Go backend, Next.js website, and browser extension respectively. Their
  source and production tests remain in the component repositories.
- `model/` documents model-test scope without mirroring model source code.
  Permanent aggregate evidence and approved aggregate charts belong under
  `model/evidence/`; ignored raw snapshots belong under `model/private/`.
- `docs/tools/` owns the cross-system runner, public-evidence validator,
  runtime projection, context validator, and orchestration tests.

Do not create a second report for the same technology in another folder, the
umbrella, or a generated PDF/JSON artifact. A validator may emit temporary JSON
to stdout or an ignored temporary directory, but each committed
`<technology>/report.md` remains the sole canonical report for that technology.

## Non-negotiable privacy boundaries

- Classification and browsing inference remain on-device.
- Never publish URLs, domains, DOM text, browsing history, keystrokes, or
  participant data.
- Screenshots and other raw visual evidence never leave the device. Public
  evidence may contain only a boolean availability flag and a SHA-256 digest of
  a locally reviewed artifact; never publish the image, filename, or path.
  The model-only charts in `model/evidence/visuals/` are a narrow exception:
  they are generated solely from aggregate metrics, contain no sample-level
  content, and are permitted only at the exact allowlisted paths enforced by
  `docs/tools/verify_public_evidence.py`. They are not screenshots or raw
  visual evidence.
- Never publish device serials, credentials, tokens, account identifiers, or
  raw ADB/logcat output.
- Test-only Android anti-uninstall coverage uses supported Device Admin and
  Accessibility behavior. It never uses critical-process APIs or bypasses OS
  consent dialogs.

## Working with component repositories

The runner accepts `--workspace-root` and never assumes a machine-specific
absolute path. Under the umbrella, sibling repositories are expected at the
paths declared by `../repos.yaml`. In a standalone clone, pass a workspace
directory containing the required sibling checkouts explicitly.

Keep component unit tests, lint rules, and production fixtures in their owning
repositories. This repository may invoke them and record only aggregate status,
duration, and output hashes.

## Mandatory test handoff

Requests to “cek”, “periksa”, “review”, “audit”, or summarize existing tests
are read-only audits. Inspect source tests, runner configuration, existing
reports/evidence, repository status, and runbooks without invoking tests,
builds, packaging, model replay, device/VM procedures, or report regeneration.
The status in an existing report is recorded status, not proof of a fresh run.
Only an explicit request to run/execute/test/validate/re-evaluate or record new
evidence authorizes execution, and the scope must not be broadened implicitly.

For every explicit test, evaluation, or re-evaluation request:

1. Run the technology-specific command or runtime procedure described by the
   relevant README/runbook.
2. Run `docs/tools/run_evaluation.py` with the required flag so the matching
   `<technology>/report.md` is regenerated. Model replay uses
   `--run-model-replay`; component checks use `--run-code-tests`.
3. For runtime evidence, validate and promote only the allowlisted ledger
   records. Never copy raw output into the public repository.
4. Inspect `git status` and `git diff` in both the component and testing
   repositories. Preserve unrelated changes.
5. Run the context and public-evidence validators before publication.
6. Provide the required receipt described in
   [`docs/ai/testing-run-receipt.md`](docs/ai/testing-run-receipt.md).

If synchronization cannot happen because a checkout, device, dependency, or
environment is unavailable, the report must remain `pending` or `blocked` and
the receipt must name the exact blocker. A direct source-repository test with
no report synchronization is not a completed evidence run.

## Default verification

Run the context validator and public-evidence checks by default:

```sh
./docs/tools/verify-ai-context.sh
python3 docs/tools/verify_public_evidence.py
```

Tests, builds, Firebase reservations, and device lifecycle actions require an
explicit request for the current task. Firebase workflows are manual and must
not run automatically on push because they may consume quota.

## Publication boundary

The repository is public. Only validated files under technology-owned
`evidence/ledger/` folders, the matching canonical reports, and the
allowlisted model aggregate evidence under `model/evidence/` may be committed
as test results. Local staging files belong under ignored `<technology>/private/`
or an external temporary directory. Model prediction tables, URLs, domains,
DOM text, screenshots, APKs, device exports, and generated build outputs never
belong in the public evidence paths.
