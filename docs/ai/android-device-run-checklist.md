# Android device run checklist

Use this checklist before recording any new Android Research evidence. The
anti-uninstall matrix and the Phase 4 latency run have different metrics, but
they share device identity, release-artifact, privacy, and cleanup rules.

## Before connecting the device

- [ ] Choose the stable `device_alias` from
      [`flutter/config/device-register.json`](../../flutter/config/device-register.json).
      Use a safe ASCII label, never a serial number. A replacement handset or
      another Firebase session receives a new suffix.
- [ ] Add or review the device's display name, OEM family, source, service,
      Android API, and retest status in the device register. The register is
      anti-uninstall metadata; a latency-only result does not automatically
      change its anti-uninstall status.
- [ ] Use the Research **release** APK and Chrome for the current progress
      demonstration. Debug/profile builds are diagnostic and cannot satisfy
      the release progress gate.
- [ ] Record the run ID, source commit, APK version, APK SHA-256, signing
      certificate fingerprint, Android API, Chrome version, and operator notes
      in a private run receipt. Never publish passwords, serials, raw logs, or
      installation output.
- [ ] Use a disposable physical, cloud, or loaner device and a synthetic test
      fixture. Do not use participant accounts or real browsing content.

## Anti-uninstall execution

- [ ] Verify the exact signed Research release APK before installation:
      package, version/build, `debuggable=false`, SHA-256, signing certificate,
      and immutable source tag/commit.
- [ ] Update with `adb install -r`; never uninstall as setup, downgrade the
      package, or switch to a debug/profile APK during the run.
- [ ] Approve Device Admin and Accessibility manually through Android system
      UI, then run `preflight` until package, admin, Accessibility, and
      `:protection` process are all healthy.
- [ ] Run `capture-before` immediately before one scenario using fresh
      `run_id`/`sample_id` values and `--build-mode release`.
- [ ] Perform exactly one visible system action. Do not rely on AOSP labels or
      fixed coordinates; follow the OEM's displayed flow.
- [ ] For Redmi/Xiaomi Settings uninstall, record the complete chain:
      **Uninstal** → **Aplikasi admin perangkat** → **Nonaktifkan & uninstal**
      → Package Installer confirmation.
- [ ] With no grant, expect the package and administrator to remain active. If
      the user confirmation removes the package, record `failed` with
      `removal_not_blocked`; do not convert it to a warning-only pass.
- [ ] Run `record-after` immediately and preserve expected versus actual
      outcome, package state, admin state, Accessibility state, and process
      state.
- [ ] If removal occurred, reinstall the same verified release APK, manually
      restore Device Admin and Accessibility, and run `preflight` before
      finishing.

## During the run

- [ ] Run `preflight` and confirm the Research package, Device Admin,
      Accessibility service, and protection process are healthy.
- [ ] For anti-uninstall, execute one matrix scenario at a time and record
      the after-state with the tamper harness.
- [ ] For latency, use the signed instrumentation helper, rebind
      Accessibility after enabling it, complete each Pattern Interrupt, and
      capture at least 30 fresh samples without changing the fixture or
      invoking instrumentation during the batch.
- [ ] Keep `run_id` unique for each batch and `sample_id` unique across every
      device ledger. Never pad a run with host-side proxy timings.

## Promote and close the run

- [ ] Validate the private JSONL with the matching validator.
- [ ] Promote to exactly one device folder:

  ```text
  flutter/evidence/ledger/<device_alias>/android-tamper.jsonl
  flutter/evidence/ledger/<device_alias>/phase4-latency.jsonl
  ```

  The promoter merges new records with the existing device ledger and rejects
  duplicate samples or a folder/record alias mismatch. Never redirect output
  to the ledger root and never overwrite a ledger manually.
- [ ] Regenerate the canonical
      [`flutter/report.md`](../../flutter/report.md) through the cross-repository
      runner and confirm the device ledger and expected aggregate counts are
      represented in the report.
- [ ] Run the context and public-evidence validators. A direct component
      command without report synchronization is not a completed evidence run.
- [ ] Disable the temporary recorder, uninstall the helper, stop synthetic
      services, remove ADB reverse networking, rebind Accessibility if needed,
      and run `preflight` again.

## Public/private boundary

Public ledgers contain only validator-approved aggregate fields: safe labels,
outcomes, state flags, durations, metrics, and approved hashes. Screenshots,
URLs, domains, DOM text, browsing history, account data, device serials,
credentials, APKs, instrumentation source, and raw ADB/logcat output remain
private or temporary and are retained/deleted according to the run receipt.

The existing `redmi_12c_local_01` latency record is a latency result only; it
does not make that device's anti-uninstall matrix complete.
