# Flutter / Android testing

This folder contains testing-repository tooling for the Flutter client and its
Android Research anti-uninstall behavior. The production client and its
production tests remain in `../gamblock_ai_apps/` in the umbrella workspace.

Android device runs are manual and disposable. Use the runbook in
[`../docs/ai/android-anti-uninstall-testing.md`](../docs/ai/android-anti-uninstall-testing.md)
for the matrix, Firebase Device Streaming workflow, privacy boundary, and
evidence promotion rules. The cross-OEM problem and current device/service
provenance are documented in
[`../docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).

Key commands, run from this repository root:

```sh
./flutter/scripts/run-android-tamper-matrix.sh preflight --device SERIAL \
  --package com.gamblock.gamblock_ai_apps.research
python3 flutter/scripts/validate_android_tamper_report.py private/android-tamper.jsonl
```

Only validated aggregate records may be promoted to the shared
`flutter/evidence/ledger/`; raw device output remains local.

## Windows extension–model runtime

The Windows client owns the classifier and intervention authority. The
cross-repository smoke test in `../windows/` loads the passive extension in
Chrome, pairs it with the installed Windows service, and verifies the current
Hybrid-v2 artifact. Run it only on an interactive Windows VM:

```powershell
cd ..
npm --prefix windows/e2e ci
npx --prefix windows/e2e playwright install chromium
python docs/tools/run_evaluation.py \
  --workspace-root C:\src\gamblock-ai \
  --run-code-tests --component flutter --include-windows-e2e
```

Without the Windows VM prerequisites, the canonical report remains `pending`.
