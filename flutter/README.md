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

The latency contract has two levels. The **feasibility** gate accepts one
homogeneous group with at least 30 successful samples, no failure, and p95
below 200 ms. The current progress-demo checkpoint is smaller and matches the
demonstration artifact: `researchRelease` on Android + Chrome, scenario
`warm_foreground_online`, with the same 30-sample/no-failure/p95 requirements.
The former final-readiness latency gate has been replaced by the two client
runtime contracts below. Debug builds are diagnostic only and cannot satisfy
the progress-demo gate.

A source-side Android measurement is not canonical runtime evidence until its
privacy-safe aggregate records are promoted and validated. The canonical
report renders all three checkpoints separately. The device register remains
anti-uninstall-scoped, so a latency-only pass does not change a device's
anti-uninstall provenance status in the device register.

## Future structured usability study

The nine-student formative activity remains off-repository feedback, not a SUS
result. The planned task + SUS study, governance prerequisite, and data
boundary are in [`../docs/ai/pkm-usability-testing.md`](../docs/ai/pkm-usability-testing.md).

## Flutter local model balanced evaluation

This pending contract evaluates the local classifier independently on Android
and Windows Research release builds with 50 gambling and 50 non-gambling
fixtures per platform. Accuracy, precision, recall, and F1 must each be at
least 90%, with false-positive rate at most 5%. Existing latency samples do
not satisfy this test.

## Cross-platform browser support regression

This pending contract uses one Android device and one Windows VM. Android covers
Chrome, Edge, Samsung Internet, Brave, and Firefox; Windows covers Chrome,
Edge, Brave, Opera, and Firefox. Each browser runs 5 non-gambling and 5
gambling fixtures, expecting `allow` and `intervention` respectively.

The existing Chrome-only Windows helper is not sufficient evidence for this
matrix. Runtime evidence remains `pending` until both platform matrices are
executed and synchronized. When evidence is produced, store it under the
platform/browser/case layout defined in
[`../docs/ai/client-runtime-evidence.md`](../docs/ai/client-runtime-evidence.md);
do not mix it into the anti-uninstall device ledgers.
