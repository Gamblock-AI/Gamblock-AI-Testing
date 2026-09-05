# Gamblock-AI Flutter / Android Report

This is the canonical aggregate report for this technology. It is
generated from validated public evidence and aggregate command results.
Raw URL, domain, DOM, browsing history, screenshot, serial, credential,
participant, and raw log data are never included.

This report covers Flutter client checks and Android Research runtime evidence.

## Android anti-uninstall

| Status | Interpretation | Samples (all) | Release samples | Diagnostic samples | Release OEM families | Release scenarios | Release coverage complete |
|---|---|---:|---:|---:|---:|---:|---|
| failed | Android/OEM Settings limitation; not interpreted as a Flutter code defect. | 18 | 11 | 7 | 1 | 10 | False |

## Android anti-uninstall interpretation

The evidence status remains `failed` when the expected `blocked` outcome was not observed. A `removal_not_blocked` record on the OEM Settings surface is classified as an Android/OEM platform limitation, not as an unresolved Flutter code defect: Android permits the user/OEM Settings flow to deactivate Device Admin, and an ordinary application cannot veto that OS-level action.
Only `release` records count toward the acceptance device/scenario matrix. Debug or profile records remain diagnostic context and cannot complete release coverage or promote an acceptance claim.
The limitation is retained as evidence and must not be presented as a code-fix task. Launcher and Package Installer results remain separate system-surface observations.
Every anti-uninstall sample also records the Android runtime state needed to interpret the system action: native protection service, Device Admin, Accessibility, package presence, and recovery timing where applicable. These runtime checks are part of the anti-uninstall evidence and are not a separate component check.

## Phase 4 latency

The feasibility and progress-demo checkpoints remain latency evidence. The previous final-readiness latency gate is replaced by separate client runtime contracts below.

| Checkpoint | Status | Scoped records | Groups | Passed groups | Coverage complete | Missing required cells |
|---|---|---:|---:|---:|---|---:|
| latency_feasibility | passed | 30 | 1 | 1 | True | 0 |
| progress_demo | passed | 30 | 1 | 1 | True | 0 |

## Android device evidence detail

Only validated public ledger records appear in this table. The result
column is the evidence assertion status; expected and actual outcomes
remain separate so an observed warning can be distinguished from a
blocked uninstall assertion.

| Device | Run / sample | OEM | API | Build | Service | Scenario | Surface | Action / observed | Expected → actual | Grant | Admin | Accessibility | Service state | App after | Recovery (s) | Result |
|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_app_info_passive_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | app_info_passive | app_info | none / none | no_tamper → no_tamper | none | true → true | true → true | true → true | true | — | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_disable_accessibility_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | disable_accessibility | accessibility_settings | disable_accessibility / disable_accessibility | degraded → degraded | none | true → true | true → false | true → true | true | — | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_force_stop_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | force_stop | none | force_stop / none | recovered → recovered | none | true → true | true → false | true → true | true | 6.0 | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_launcher_uninstall_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | launcher_uninstall | launcher | uninstall / uninstall | blocked → warned | none | true → true | true → true | true → true | true | — | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_package_installer_uninstall_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | package_installer_uninstall | package_installer | uninstall / uninstall | blocked → warned | none | true → true | true → true | true → true | true | — | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_process_kill_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | process_kill | none | process_kill / none | recovered → recovered | none | true → true | true → true | true → true | true | 1.0 | passed |
| Google Pixel 9 Pro Remote | tamper_pixel_2026_09 / pixel9pro_settings_uninstall_01 | aosp | 35 | debug | firebase_test_lab_android_device_streaming | settings_uninstall | settings | uninstall / uninstall | blocked → warned | none | true → true | true → true | true → true | true | — | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_app_info_passive_01 | xiaomi_redmi | 34 | release | local_physical_device | app_info_passive | app_info | none / none | no_tamper → no_tamper | none | true → true | true → true | true → true | true | — | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_clear_data_01 | xiaomi_redmi | 34 | release | local_physical_device | clear_data | app_info | clear_data / clear_data | degraded → degraded | none | true → true | true → false | true → false | true | 5.0 | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_disable_accessibility_01 | xiaomi_redmi | 34 | release | local_physical_device | disable_accessibility | accessibility_settings | disable_accessibility / disable_accessibility | degraded → degraded | none | true → true | true → false | true → true | true | — | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_force_stop_01 | xiaomi_redmi | 34 | release | local_physical_device | force_stop | none | force_stop / none | recovered → recovered | none | true → true | true → false | true → true | true | 11.0 | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_launcher_uninstall_01 | xiaomi_redmi | 34 | release | local_physical_device | launcher_uninstall | launcher | uninstall / uninstall | blocked → blocked | none | true → true | true → true | true → true | true | — | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_package_installer_uninstall_01 | xiaomi_redmi | 34 | release | local_physical_device | package_installer_uninstall | package_installer | uninstall / uninstall | blocked → blocked | none | true → true | true → true | true → true | true | — | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_process_kill_01 | xiaomi_redmi | 34 | release | local_physical_device | process_kill | none | process_kill / none | recovered → recovered | none | true → true | true → true | true → true | true | 3.0 | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_reboot_01 | xiaomi_redmi | 34 | release | local_physical_device | reboot | none | reboot / none | recovered → recovered | none | true → true | true → true | true → true | true | 53.0 | passed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_settings_uninstall_01 | xiaomi_redmi | 34 | release | local_physical_device | settings_uninstall | settings | uninstall / uninstall | blocked → failed | none | true → false | true → false | true → false | false | — | failed |
| Redmi 12C | tamper_redmi12c_release_20260905_fix / redmi_settings_uninstall_fix_01 | xiaomi_redmi | 34 | release | local_physical_device | settings_uninstall | settings | uninstall / uninstall | blocked → failed | none | true → false | true → false | true → false | false | — | failed |
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_setup_01 | xiaomi_redmi | 34 | release | local_physical_device | setup | none | none / none | no_tamper → no_tamper | none | true → true | true → true | true → true | true | — | passed |

## Android testing context

Service and cross-OEM interpretation are maintained in
[`docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).

## Flutter local model balanced evaluation

| Status | Platforms | Samples per platform | Build | Gate | Reason |
|---|---|---:|---|---|---|
| pending | Android + Windows | 50 gambling + 50 non-gambling | research release | accuracy, precision, recall, and F1 ≥90%; FPR ≤5% | No complete client-runtime evidence root exists. |

This is a balanced local-classifier evaluation contract. It is not satisfied by the existing 30-sample latency evidence.

## Cross-platform browser support regression

| Status | Android device | Windows VM | Android browsers | Windows browsers | Samples per browser | Expected result | Reason |
|---|---:|---:|---|---|---:|---|---|
| pending | 1 | 1 | Chrome, Edge, Samsung Internet, Brave, Firefox | Chrome, Edge, Brave, Opera, Firefox | 5 gambling + 5 non-gambling | non-gambling: allow; gambling: intervention | No complete client-runtime evidence root exists. |

Each browser is evaluated for allow on non-gambling fixtures and intervention on gambling fixtures. This is functional browser-support evidence, not latency evidence or anti-uninstall evidence.


## Component checks

| Check | Status |
|---|---|
| testing_flutter_unit | passed |
| client_python_contract_unit | passed |
| flutter_pattern_interrupt_unit | passed |

## Supplemental explicit verification

These checks were executed explicitly on 2026-09-05 and are recorded as
aggregate results only:

| Check | Status | Aggregate result |
|---|---|---|
| flutter_test_full | passed | `flutter test` completed with 116 tests passed |
| flutter_verify | passed | `./scripts/verify.sh` completed l10n parity validation and `flutter analyze` with no issues |

## Interpretation limits

Offline evaluation is not physical browser, Android, or Windows runtime proof.
A missing matrix cell remains pending. This report contains aggregate-safe
results and validated scenario detail where applicable; source code and
component unit tests remain in their owners.
