# Android Research Phase 4 latency testing

This runbook is the operational source for the Research-release Phase 4
latency measurement. It is separate from the Android anti-uninstall matrix;
use the shared [new-device checklist](android-device-run-checklist.md) for
registration, release-artifact provenance, promotion, and cleanup.

The cross-OEM status and evidence interpretation are documented in
[android-anti-uninstall-context.md](android-anti-uninstall-context.md).

## Research release Phase 4 latency run

This procedure records the official `input_to_visible_ms` metric for a
non-debuggable Research release. It is separate from the anti-uninstall
matrix above. The progress-demo scope is one homogeneous group: Android,
Chrome, Research release, and `warm_foreground_online`.

### Preconditions

1. Install the intended Research release APK and record its version, package,
   and signing-certificate fingerprint locally. Do not publish a device
   serial, keystore password, or raw installation output.
2. Confirm Device Admin and the Gamblock Accessibility Service are enabled.
3. Use a disposable/synthetic page containing only test fixtures. Do not use
   a participant account or real browsing content.
4. Prepare a temporary instrumentation helper signed by the same Research
   certificate as the target APK. Use an interactive keystore prompt; never
   put the password in a command, script, log, or documentation.

The helper contract is fixed for repeat runs: package
`com.gamblock.phase4probe`, instrumentation
`com.gamblock.phase4probe/.ProbeInstrumentation`, and target package
`com.gamblock.gamblock_ai_apps.research`. Its `enable` mode creates the
device-local recorder configuration, `export` returns only the Phase 4
allowlist fields, and `disable` removes the configuration. Verify that the
helper and target APK have the same certificate before installing it; a
different certificate cannot be used as a probe for the release package.

### Required order

Run the following order exactly. Instrumentation starts in the target process
and can make the Accessibility service process stop; that is expected and is
not evidence that the APK is broken.

1. Enable a fresh recorder configuration with the signed helper:

   ```sh
   adb -s SERIAL shell am instrument -w -r -e mode enable \
     com.gamblock.phase4probe/.ProbeInstrumentation
   ```

   The helper must write an allowlisted configuration with the run ID,
   device alias, scenario, browser family, and `build_mode=release`, and clear
   any previous latency file.

2. Rebind the Gamblock Accessibility Service (toggle it off and on in
   Settings, or use an equivalent operator-approved device procedure).
3. Run `preflight` and continue only when the package, Device Admin,
   Accessibility, and protection process are all healthy.
4. For each sample, return to Home, open the same synthetic fixture in Chrome,
   wait for the native Pattern Interrupt to become visible, wait through the
   seven-second countdown, and complete the intervention. A visible overlay
   that is not completed can leave the intervention active and prevent the
   next sample from being recorded.
5. Capture at least 30 fresh samples without invoking instrumentation during
   the batch. The official recorder, not a host-side window-overlay timer,
   supplies `input_to_visible_ms`.
6. After the batch, export through the signed helper. Do not use `run-as` on
   the non-debuggable Research APK; `run-as: package not debuggable` is an
   expected Android restriction, not a missing permission:

   ```sh
   adb -s SERIAL shell am instrument -w -r -e mode export \
     com.gamblock.phase4probe/.ProbeInstrumentation
   ```

   The helper must return only the Phase 4 allowlist fields. Never copy the
   target `latency.jsonl` raw file or any browser/page data. Build the local
   JSONL export from the sanitized instrumentation result if the helper
   cannot create an app-private output file.
7. Validate, promote, and regenerate the report from the testing repository:

   ```sh
   python3 flutter/scripts/phase4_latency_report.py PRIVATE/phase4-latency.jsonl \
     --minimum-samples 30 --target-ms 200 \
     --required-platform android --required-product-flavor research \
     --required-browser chrome --required-build-mode release \
     --required-scenario warm_foreground_online

   python3 flutter/scripts/promote_evidence.py phase4-latency \
     --input PRIVATE/phase4-latency.jsonl \
     --output flutter/evidence/ledger/DEVICE_ALIAS/phase4-latency.jsonl

   cd ..
   python3 gamblock-ai-testing/docs/tools/run_evaluation.py \
     --workspace-root . --run-code-tests --component flutter
   ```

   Promotion targets the device folder from the checklist. Existing records
   are merged atomically; duplicate `sample_id` values and a folder/record
   alias mismatch stop the command before publication.

   The last command uses the single active current report configuration.

### Failure recovery and cleanup

- `latency file missing`: verify the recorder configuration, release build
  mode, fresh intervention, and that Accessibility was rebound after enabling
  instrumentation.
- Fewer than 30 records: check that every visible intervention completed
  after the countdown; do not pad the ledger with host-side proxy timings.
- `run-as` rejection: keep using the same-certificate signed helper and its
  sanitized instrumentation result; do not make the product APK debuggable.
- After promotion, disable/clear the temporary recorder configuration,
  uninstall the helper, remove ADB reverse networking, stop the synthetic
  server, rebind Accessibility if instrumentation stopped it, and run
  `preflight` again. Leave the Research APK installed only if the operator
  wants the device ready for further work.

The permanent public ledger may contain only the Phase 4 allowlist and
aggregate labels. Temporary helper source/APK, synthetic fixtures, raw device
traces, screenshots, and credentials remain outside the repository and are
deleted or retained locally according to the run receipt.
