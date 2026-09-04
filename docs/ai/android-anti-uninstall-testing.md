# Android Research anti-uninstall testing

This runbook is the single operational source for Android anti-uninstall
testing. It applies only to the Research flavor. The Play flavor intentionally
does not include Settings, package-installer, or launcher removal monitoring.
The cross-OEM problem, Firebase Test Lab service context, and current device
status are documented in [`android-anti-uninstall-context.md`](android-anti-uninstall-context.md).
Safe device/provenance metadata is maintained in
[`flutter/config/device-register.json`](../../flutter/config/device-register.json).
Before a new handset or Firebase session, follow the shared
[Android device run checklist](android-device-run-checklist.md).

## Test contract

Each device run must establish a healthy baseline before one system action is
performed. Record one scenario at a time, then validate the resulting JSONL.
Never infer a pass from a screenshot or a written narrative alone.

Required scenario families:

- passive App Info and another-app controls must produce `no_tamper`;
- Launcher, Settings, and Package Installer uninstall attempts must preserve
  the app and active administrator when no valid removal grant exists;
- Accessibility disable and clear-data actions must remain distinguishable from
  uninstall;
- process kill, force-stop, and reboot must be recorded as recovery scenarios;
- valid-grant removal is the only normal removal path;
- invalid, expired, or wrong-device grants must not authorize removal.

The required OEM families and scenario list are versioned in
[`flutter/config/device-matrix.json`](../../flutter/config/device-matrix.json). A missing
scenario is `pending`, never `passed`.

## Reproducible device workflow

Use this sequence for every new handset or Firebase session. The commands use
`SERIAL` as a local shell placeholder; never copy the real serial into a
receipt, ledger, screenshot, or report.

### 1. Verify the exact release artifact

Use the signed Research **release** APK that will be demonstrated. Before
installing, record the following in a private receipt and verify them locally:

- package: `com.gamblock.gamblock_ai_apps.research`;
- version name and build number;
- `debuggable=false`;
- APK SHA-256 and signing-certificate fingerprint; and
- source commit or immutable release tag.

For example, with Android SDK tools available:

```sh
apksigner verify --verbose --print-certs RESEARCH_APK
apkanalyzer manifest application-id RESEARCH_APK
apkanalyzer manifest version-name RESEARCH_APK
apkanalyzer manifest version-code RESEARCH_APK
apkanalyzer manifest debuggable RESEARCH_APK
sha256sum RESEARCH_APK
```

Install an approved update with `adb install -r RESEARCH_APK`. Do not use
`adb uninstall` as setup, do not downgrade with `-d`, and do not replace a
release APK with a debug/profile APK during the same run.

### 2. Establish and capture a healthy baseline

1. Use a disposable device and a synthetic fixture; do not use participant
   accounts or real browsing content.
2. Open the Research app and approve Device Admin and Accessibility through the
   Android system UI. Android does not permit the app to silently re-enable
   Accessibility.
3. Run `preflight` and continue only when the package, Device Admin,
   Accessibility service, and `:protection` process are all healthy.
4. Run `capture-before` with a new `run_id`, `sample_id`, device alias, OEM
   family, Android API, and `--build-mode release`.

The baseline must be captured immediately before the single scenario action.
If any baseline flag is false, repair the setup and capture a new baseline;
do not reinterpret an unhealthy run as a tamper result.

### 3. Perform exactly one system-UI scenario

Do not automate coordinates or assume that an OEM uses AOSP labels. Follow the
visible labels on the device and record the actual surface and action.

For the Redmi/Xiaomi Settings scenario, the complete single action is:

1. Open Settings → Apps → Gamblock-AI Research app info.
2. Tap **Uninstal**.
3. If MIUI opens **Aplikasi admin perangkat**, select
   **Nonaktifkan & uninstal**.
4. If Package Installer asks for confirmation, confirm only this Gamblock
   removal when the disposable-device run explicitly authorizes it.
5. Observe whether the package, Device Admin, Accessibility, and protection
   process remain present.

The expected outcome with `grant_state=none` is `blocked`: the package and
administrator remain active. If MIUI reaches the package-installer confirmation
and the package is removed, record `actual_outcome=failed` and
`failure_code=removal_not_blocked`; never relabel that observation as a pass.
Canceling the dialog is a different observation and must be recorded with its
actual outcome.

Launcher, Package Installer, Accessibility-disable, clear-data, force-stop,
process-kill, and reboot are separate scenarios. Capture and record each one
individually; do not combine several actions into one sample. Lifecycle
commands require `--acknowledge-disposable-device`.

### 4. Record, validate, and promote

Immediately after the action, run `record-after` using the labels actually
observed. Keep expected and actual outcomes separate:

```sh
./flutter/scripts/run-android-tamper-matrix.sh record-after \
  --device SERIAL \
  --state flutter/private/DEVICE-settings.state.json \
  --output flutter/private/android-tamper.jsonl \
  --scenario settings_uninstall \
  --surface settings \
  --action uninstall \
  --observed-action uninstall \
  --expected-outcome blocked \
  --actual-outcome ACTUAL_OUTCOME \
  --result RESULT \
  --grant-state none \
  --evidence-reference DEVICE_settings_uninstall_01
```

Then validate the private export and promote only the allowlisted aggregate
record into the matching device folder. A failed or incomplete record is
valuable evidence and must not be deleted to make the matrix look complete.

### 5. Restore the device before ending the run

If the test removed the package, reinstall the same verified Research release
APK and manually re-activate Device Admin and Accessibility. Run `preflight`
again and confirm all four health checks are true. Do not clear data or change
settings in other applications. Keep APKs, UI dumps, ADB output, and raw logs
outside the repository according to the private run receipt.

### Redmi 12C lesson retained for future devices

On Redmi 12C, both the original and v1.6.6 retest followed the MIUI
**Nonaktifkan & uninstal** path and removed the package after confirmation.
The code records the deactivation attempt, but a standard APK cannot veto the
OS-level administrator deactivation. This is a platform limitation, not a
setup step to bypass. Other OEMs must be tested and reported independently.

## Firebase Device Streaming workflow

Firebase Device Streaming is an optional interactive source of remote physical
devices. It is not started by any repository script.

1. Review the matrix and reserve one device manually in Android Studio's
   Remote Devices window.
2. Use a Research APK and a disposable session. Do not use a participant's
   account or personal device state.
3. Confirm the device is connected through ADB and run `preflight`.
4. Capture the baseline, perform exactly one documented system action, and
   record the after-state.
5. Keep screenshots/ADB traces local. If visual evidence is needed, compute a
   SHA-256 digest locally; publish only the digest and availability metadata.
6. Return/erase the device when finished. Never run all devices concurrently
   without an explicit quota decision.

Consult the official Android and Firebase documentation for the current device
catalog, reservation behavior, access roles, and pricing. Catalog availability
and quotas can change; do not hardcode them into evidence.

The optional Firebase CLI MCP can assist with read-only project/catalog
inspection when configured by the operator. It is not a replacement for
Android Studio Device Streaming, ADB, or the manual system-UI workflow. No
Firebase credential, project secret, or MCP configuration is committed here.

## Cost-controlled remote execution

Remote device time is a scarce, billable execution resource. Prepare and
validate everything that does not require an OEM system UI before reserving a
device:

1. Run local unit/contract checks, verify the signed Research release APK, and
   freeze the source tag, checksum, run IDs, scenario list, and operator notes.
2. Select one representative device for each missing OEM family. Do not open a
   separate remote session for every scenario or every similar handset unless
   the first result shows an OS/version-specific difference.
3. Reserve/activate the remote device only after the previous steps are ready.
   Start a visible session timer, run `preflight`, and execute only the planned
   scenarios in that one session.
4. Release the remote device as soon as the after-state is captured. Validate,
   promote, regenerate the report, and edit documentation locally after the
   session has ended.

> **IMPORTANT — penghematan biaya remote**
>
> Jangan melakukan build, memperbaiki kode, mengubah runbook, atau mencoba
> ulang prosedur secara eksploratif ketika Device Streaming sedang aktif.
> Siapkan APK, command, label UI, dan skenario terlebih dahulu. Tetapkan batas
> waktu manual per sesi dan hentikan sesi bila preflight gagal atau perangkat
> tidak stabil. Budget alert Google Cloud hanya memberi peringatan dan tidak
> otomatis membatasi tagihan.

At the preparation stage it is normal for `adb devices` to show no device (or
no ready device). This is not a test failure and must not trigger retries,
builds, or a Firebase reservation. Run `preflight`, `capture-before`, and
device actions only after the operator explicitly activates/reserves the
device and ADB reports it as ready.

Firebase distinguishes interactive Android Device Streaming from automated
Test Lab matrices. Streaming is appropriate only for OEM system-UI scenarios
that need manual interaction. App-contained checks should be moved to local
tests or automated Test Lab instrumentation/Robo where their semantics remain
valid. Review the current [Test Lab quotas and pricing](https://firebase.google.com/docs/test-lab/usage-quotas-pricing)
before every campaign: the documented allowance is 30 no-cost Device
Streaming minutes per project per month, followed by per-minute billing; the
automated physical/virtual-device quotas and rates are different. Pricing and
catalog availability can change.

## Local commands

From this repository, with the client checkout available as a sibling:

```sh
./flutter/scripts/run-android-tamper-matrix.sh preflight \
  --device SERIAL \
  --package com.gamblock.gamblock_ai_apps.research
```

The matrix script writes to a local staging path by default. Example manual
flow:

```sh
./flutter/scripts/run-android-tamper-matrix.sh capture-before \
  --device SERIAL \
  --state flutter/private/pixel-settings.state.json \
  --run-id tamper_pixel_2026_09 \
  --sample-id pixel_settings_uninstall_01 \
  --device-alias pixel_9_pro_remote_01 \
  --oem-family aosp \
  --android-api 35 \
  --build-mode debug

# Perform exactly one Settings/Launcher/Package Installer action manually.

./flutter/scripts/run-android-tamper-matrix.sh record-after \
  --device SERIAL \
  --state private/pixel-settings.state.json \
  --output flutter/private/android-tamper.jsonl \
  --scenario settings_uninstall \
  --surface settings \
  --action uninstall \
  --observed-action uninstall \
  --expected-outcome blocked \
  --actual-outcome warned \
  --result passed \
  --grant-state none \
  --evidence-reference settings_uninstall_guard_01
```

Process-kill, force-stop, and reboot commands require
`--acknowledge-disposable-device`. Do not invoke them on a personal or
participant device.

Validate and promote only aggregate records:

```sh
python3 flutter/scripts/validate_android_tamper_report.py flutter/private/android-tamper.jsonl
python3 flutter/scripts/promote_evidence.py android-tamper \
  --input flutter/private/android-tamper.jsonl \
  --output flutter/evidence/ledger/DEVICE_ALIAS/android-tamper.jsonl
```

The promoter rejects raw browsing/account fields, device serials, local paths,
images, duplicate samples, and malformed visual hashes. It never copies local
screenshots into the repository. It merges into an existing per-device ledger
without overwriting prior runs and rejects duplicate sample IDs or a folder
alias that does not match the records.

## Phase 4 latency

The Research release latency procedure is maintained separately in
[`android-phase4-latency-testing.md`](android-phase4-latency-testing.md). Use the
shared [new-device checklist](android-device-run-checklist.md) before starting
any latency or anti-uninstall run.

## Interpretation limits

The initial Pixel baseline is provisional and does not generalize to Samsung,
Xiaomi/Redmi, OPPO/Realme, or Vivo. OS-level force-stop behavior may be
unresistable; record the observed state rather than relabeling it as a pass.
Runtime evidence must be distinguished from source-code or offline replay
evidence in the canonical Flutter/Android report.
