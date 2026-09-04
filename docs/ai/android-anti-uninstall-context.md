# Android anti-uninstall cross-OEM context

This document captures the initial research problem and the execution context
for Android anti-uninstall testing. It does not replace the generated Flutter
report or the validated evidence ledger.

## Initial problem

The Research flavor behaved acceptably on the owner's Redmi 12C during the
initial observation, but student trials on different Android brands exposed
different bugs. Anti-uninstall behavior depends on OEM system UI, package
installer labels, Device Admin handling, Accessibility lifecycle behavior,
background-process policy, and reboot/force-stop recovery. A successful run on
one OEM must therefore not be generalized to another OEM.

The test objective is to establish reproducible behavior for each supported
system surface and lifecycle scenario while distinguishing an actual product
failure from an OS action that the application is not allowed to resist.

## Evidence and device status

Only validated records in the per-device
`flutter/evidence/ledger/<device_alias>/android-tamper.jsonl` ledgers are
anti-uninstall runtime evidence. The generated
[`flutter/report.md`](../../flutter/report.md) renders the detailed scenario
results from that ledger.

The public device register at
[`flutter/config/device-register.json`](../../flutter/config/device-register.json)
contains safe device and provenance metadata. Its `pending_retest` entries
are not evidence and do not contribute to coverage, sample counts, or pass
rates. The register is currently scoped to anti-uninstall provenance; a
latency-only run does not change an entry's anti-uninstall status. Use the
[shared Android device run checklist](android-device-run-checklist.md) for
alias selection, release-artifact provenance, and cleanup.

Current interpretation:

- Google Pixel 9 Pro Remote is the only device with valid **anti-uninstall**
  evidence. Its seven scenario records and observed outcomes are detailed in
  `flutter/report.md`.
- Redmi 12C (`redmi_12c_local_01`) now has a validated Phase 4 latency run for
  the Research release in the per-device
  `flutter/evidence/ledger/<device_alias>/phase4-latency.jsonl` ledger and is
  documented in `flutter/report.md`. This proves only the Android/Chrome/release latency
  group and the user-visible Pattern Interrupt demonstration. The device is
  still in the anti-uninstall retest queue because no complete Android
  tamper-scenario ledger has been promoted for it.
- Samsung Galaxy A14 had a device-reservation attempt that did not complete.
  It is an operational setup note only, not a test result.
- Samsung, Xiaomi/Redmi, OPPO/Realme, and Vivo coverage remains incomplete
  until validated device/scenario records exist.

## Firebase Test Lab service context

The remote Pixel session uses **Firebase Test Lab — Android Device Streaming**
through Android Studio's **Remote Devices** window. Android Device Streaming
provides interactive access to Test Lab devices in Google's secure data
centers, allowing manual system-UI actions such as Settings, Launcher, and
Package Installer flows. See the [official Android Device Streaming guide](https://firebase.google.com/docs/test-lab/android/android-device-streaming?hl=en).

This is an interactive remote-device session, not an automated Test Lab
instrumentation, Robo, or Game Loop matrix. Repository scripts do not reserve
devices, click system UI, or run cost-bearing cloud sessions automatically.
The operator reviews the matrix, reserves one disposable session, performs
one scenario at a time, and returns/erases the device afterward.

Quota and billing are project-level and can change. Before a session, consult
the [official Test Lab usage, quotas, and pricing documentation](https://firebase.google.com/docs/test-lab/usage-quotas-pricing)
and record the service/provenance metadata without committing credentials,
project secrets, device serials, or cloud console exports. Access roles are
documented in the [official IAM permissions reference](https://firebase.google.com/docs/test-lab/android/iam-permissions-reference).

The Redmi 12C retest is a local physical-device run and must be labeled as
such. It must not be presented as Firebase evidence.

## Recording contract

For each device/scenario:

1. establish a healthy baseline;
2. perform exactly one documented system action;
3. record the after-state using the Android tamper schema;
4. validate the local JSONL export;
5. promote only allowlisted aggregate fields to the public ledger; and
6. regenerate `flutter/report.md`.

Screenshots, ADB traces, logcat output, URLs, domains, browsing history,
credentials, participant data, and device serials remain local and are never
copied to the public repository. A missing or informal observation remains
`pending` or `pending_retest`, never `passed`.

## Interpretation limits

The current Pixel evidence demonstrates behavior only for its recorded AOSP
system context. It does not establish compatibility for Xiaomi/Redmi,
Samsung, OPPO/Realme, or Vivo. OEM coverage must be expanded through the
matrix in [`flutter/config/device-matrix.json`](../../flutter/config/device-matrix.json)
and reviewed one device/scenario cell at a time.
