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
- Redmi 12C (`redmi_12c_local_01`) now has a validated Phase 4 latency run and
  a partial Android Research release anti-uninstall ledger. Launcher and
  Package Installer uninstall attempts were blocked, Accessibility disable and
  clear-data were recorded as expected degraded states, and process-kill,
  force-stop (after an explicit relaunch), and reboot all recovered the
  protection process. The Settings uninstall attempt removed the package after
  MIUI deactivated Device Admin (`removal_not_blocked`). The failure is retained
  as evidence; it is not converted into a pass. The two Settings records are
  classified as an Android/OEM platform limitation, not as an unresolved
  Flutter code defect: ordinary Android applications cannot veto the
  user-initiated Device Admin deactivation in the MIUI Settings flow. The
  `redmi_settings_uninstall_fix_01` name identifies a follow-up evidence run;
  it does not claim that a code fix succeeded. Valid/invalid grant scenarios
  are still pending because no backend-issued grant/account flow was available
  during this run, so the device remains in the anti-uninstall retest queue.
- Samsung Galaxy A14 had a device-reservation attempt that did not complete.
  It is an operational setup note only, not a test result.
- Samsung, Xiaomi/Redmi, OPPO/Realme, and Vivo coverage remains incomplete
  until validated device/scenario records exist.

## Scope limitation: standard Android Research APK

Anti-uninstall in the Research APK is deliberately best-effort within the
authority Android grants to an ordinary application. Device Administrator
prevents removal while it is active, but an Android/OEM Settings flow may ask
the user to deactivate the administrator and then continue to the package
installer. `DeviceAdminReceiver.onDisableRequested` can display a warning and
record the attempt, but it cannot reject the OS-level deactivation. The
Accessibility service can detect labels and request Back/Home, yet it cannot
override Settings or the package installer, and an OEM can stop the protection
process during this transition.

The Redmi 12C release evidence is an explicit example: the Settings flow
reached “Nonaktifkan & uninstal” and the package was removed after confirmation.
The failed result is retained as evidence and labeled as an Android/OEM
platform limitation in the generated report, not as a code-fix backlog item.
The prototype therefore claims detection, warning, audit, recovery, and
approved-grant removal—not guaranteed uninstall prevention across all OEMs.
Device Owner/MDM/kiosk provisioning would be a separate managed-device scope
and is not part of the current APK test contract.

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
