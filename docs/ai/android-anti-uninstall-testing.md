# Android Research anti-uninstall testing

This runbook is the single operational source for Android anti-uninstall
testing. It applies only to the Research flavor. The Play flavor intentionally
does not include Settings, package-installer, or launcher removal monitoring.

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
[`config/device-matrix.json`](../../config/device-matrix.json). A missing
scenario is `pending`, never `passed`.

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
  --state private/pixel-settings.state.json \
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
  --output private/android-tamper.jsonl \
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
python3 flutter/scripts/validate_android_tamper_report.py private/android-tamper.jsonl
python3 flutter/scripts/promote_evidence.py android-tamper \
  --input private/android-tamper.jsonl \
  --output evidence/ledger/android-tamper.jsonl
```

The promoter rejects raw browsing/account fields, device serials, local paths,
images, duplicate samples, and malformed visual hashes. It never copies local
screenshots into the repository.

## Interpretation limits

The initial Pixel baseline is provisional and does not generalize to Samsung,
Xiaomi/Redmi, OPPO/Realme, or Vivo. OS-level force-stop behavior may be
unresistable; record the observed state rather than relabeling it as a pass.
Runtime evidence must be distinguished from source-code or offline replay
evidence in the canonical summary.
