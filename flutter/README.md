# Flutter / Android testing

This folder contains testing-repository tooling for the Flutter client and its
Android Research anti-uninstall behavior. The production client and its
production tests remain in `../gamblock_ai_apps/` in the umbrella workspace.

Android device runs are manual and disposable. Use the runbook in
[`../docs/ai/android-anti-uninstall-testing.md`](../docs/ai/android-anti-uninstall-testing.md)
for the matrix, Firebase Device Streaming workflow, privacy boundary, and
evidence promotion rules.

Key commands, run from this repository root:

```sh
./flutter/scripts/run-android-tamper-matrix.sh preflight --device SERIAL \
  --package com.gamblock.gamblock_ai_apps.research
python3 flutter/scripts/validate_android_tamper_report.py private/android-tamper.jsonl
```

Only validated aggregate records may be promoted to the shared
`evidence/ledger/`; raw device output remains local.
