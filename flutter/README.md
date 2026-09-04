# Flutter / Android testing

This folder contains testing-repository tooling for the Flutter client and its
Android Research anti-uninstall behavior. The production client and its
production tests remain in `../gamblock_ai_apps/` in the umbrella workspace.

Android device runs are manual and disposable. Use the runbook in
[`../docs/ai/android-anti-uninstall-testing.md`](../docs/ai/android-anti-uninstall-testing.md)
for the anti-uninstall matrix and Firebase Device Streaming workflow. Use the
shared [new-device checklist](../docs/ai/android-device-run-checklist.md)
before any anti-uninstall or latency run, and the dedicated
[Phase 4 latency runbook](../docs/ai/android-phase4-latency-testing.md) for
Research release timing. The cross-OEM problem and current device/service
provenance are documented in
[`../docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).

Key commands, run from this repository root:

```sh
./flutter/scripts/run-android-tamper-matrix.sh preflight --device SERIAL \
  --package com.gamblock.gamblock_ai_apps.research
python3 flutter/scripts/validate_android_tamper_report.py private/android-tamper.jsonl
```

Only validated aggregate records may be promoted to the shared
`flutter/evidence/ledger/`. Public ledgers are grouped by the safe
`device_alias` used in each record:

```text
flutter/evidence/ledger/<device_alias>/android-tamper.jsonl
flutter/evidence/ledger/<device_alias>/phase4-latency.jsonl
```

Raw device output remains local. Keep one device alias per folder and do not
use display names, serial numbers, or other machine-specific identifiers as
folder names. The promoter merges new runs atomically into the existing
device file and rejects duplicate `sample_id` values or a folder/record alias
mismatch; never overwrite a ledger manually.

## Phase 4 latency promotion

The public Phase 4 ledger accepts only the allowlisted aggregate timing schema.
Promote a locally validated export without copying visual evidence or browsing
data:

```sh
python3 flutter/scripts/promote_evidence.py phase4-latency \
  --input flutter/private/phase4-latency.jsonl \
  --output flutter/evidence/ledger/DEVICE_ALIAS/phase4-latency.jsonl
```

The latency contract deliberately has three levels. The **feasibility** gate
accepts one homogeneous group with at least 30 successful samples, no failure,
and p95 below 200 ms. The selected report version's progress-demo checkpoint
is smaller and matches the demonstration artifact: `researchRelease` on
Android + Chrome, scenario `warm_foreground_online`, with the same
30-sample/no-failure/p95 requirements. For v5 this is the **PKM v5
progress-demo**; a later active report selects its matching versioned gate.
The **final-readiness** gate remains Android/Windows ×
Chrome/Edge/Opera × profile/release under the same per-cell criteria. Debug
builds are diagnostic only and cannot satisfy the progress-demo or final gate.

A source-side Android measurement is not canonical runtime evidence until its
privacy-safe aggregate records are promoted and validated. The canonical
report renders all three checkpoints separately. The device register remains
anti-uninstall-scoped, so a latency-only pass does not remove a device from
the anti-uninstall retest queue.

## Future structured usability study

The nine-student formative activity remains off-repository feedback, not a SUS
result. The planned task + SUS study, governance prerequisite, and data
boundary are in [`../docs/ai/pkm-usability-testing.md`](../docs/ai/pkm-usability-testing.md).

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
