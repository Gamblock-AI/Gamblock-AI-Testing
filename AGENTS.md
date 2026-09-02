# Gamblock-AI Testing Repository Rules

Context version: `2026-09-02.3`

This repository owns cross-repository test orchestration and public evidence
for Gamblock-AI. Product source code and production unit tests remain in their
component repositories; this repository owns the reproducible evaluation
workflow, privacy-safe evidence ledger, and one canonical testing summary.

## Source of truth

- `flutter/config/device-matrix.json` defines required Android device and
  scenario coverage.
- `<technology>/evidence/ledger/` contains public, aggregate-only evidence for
  that technology.
- Each technology's `<technology>/report.md` is its only human-readable
  canonical report; `docs/testing-index.md` is a link-only index.
- `docs/ai/` explains the workflow and current capability boundaries.

## Directory ownership

- `flutter/` owns Flutter/Android anti-uninstall, Android tamper, and Phase 4
  latency harnesses plus their tests.
- `golang/`, `next/`, and `browser-extention/` own the test entrypoint documentation for
  the Go backend, Next.js website, and browser extension respectively. Their
  source and production tests remain in the component repositories.
- `model/` documents model-test scope without mirroring model source code.
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
`evidence/ledger/` folders and the matching canonical reports may be committed
as test results. Local staging files belong under ignored `<technology>/private/`
or an external temporary directory. Never commit secrets, raw screenshots,
APKs, device exports, or generated build outputs.
