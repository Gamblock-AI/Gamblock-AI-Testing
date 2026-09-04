# Gamblock-AI Flutter / Android Report

This is the canonical aggregate report for this technology. It is
generated from validated public evidence and aggregate command results.
Raw URL, domain, DOM, browsing history, screenshot, serial, credential,
participant, and raw log data are never included.

This report covers Flutter client checks and Android Research runtime evidence.

## Android anti-uninstall

| Status | Samples | Groups | OEM families | Scenarios | Coverage complete |
|---|---:|---:|---:|---:|---|
| failed | 17 | 17 | 2 | 10 | False |

## Phase 4 latency

The progress-report status is the `pkm_progress_v5_demo` checkpoint. Final readiness remains a separate retained gate.

| Checkpoint | Status | Scoped records | Groups | Passed groups | Coverage complete | Missing required cells |
|---|---|---:|---:|---:|---|---:|
| latency_feasibility | passed | 30 | 1 | 1 | True | 0 |
| pkm_progress_v5_demo | passed | 30 | 1 | 1 | True | 0 |
| final_readiness | pending | 30 | 1 | 1 | False | 11 |

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
| Redmi 12C | tamper_redmi12c_release_20260905 / redmi_setup_01 | xiaomi_redmi | 34 | release | local_physical_device | setup | none | none / none | no_tamper → no_tamper | none | true → true | true → true | true → true | true | — | passed |


## Android device retest queue (not evidence)

These device records are planning metadata only. They do not contribute
to Android samples, groups, OEM coverage, scenario coverage, or pass rates.
A blank result means that no prior informal outcome has been promoted.

| Device | OEM | Source | Service | Android API | Build | Status | Result | Retest required |
|---|---|---|---|---:|---|---|---|---|
| Redmi 12C | xiaomi_redmi | local_physical_device | local_physical_device | 34 | release | pending_retest | — | true |

## Android testing context

Service and cross-OEM interpretation are maintained in
[`docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).

## Windows extension–model runtime

| Status | Browser | Build | Scenarios | Passed | Reason | Model version | Ruleset version | Intervention samples |
|---|---|---|---:|---:|---|---|---|---:|
| pending | — | — | — | — | Use --include-windows-e2e on an approved Windows VM or runner. | — | — | — |

| Artifact | SHA-256 |
|---|---|
| Model asset | — |
| Rules asset | — |
| Fixture set | — |
| Source ONNX | — |

Artifact identity is aggregate-safe; raw URL, DOM, token, screenshot, and browser log data are never published.


## Component checks

| Check | Status |
|---|---|
| flutter_pattern_interrupt_unit | pending |
| testing_flutter_unit | passed |
| client_python_contract_unit | passed |
| android_instrumented_runtime | pending |
| windows_extension_model_e2e | pending |

## Interpretation limits

Offline evaluation is not physical browser, Android, or Windows runtime proof.
A missing matrix cell remains pending. This report contains aggregate-safe
results and validated scenario detail where applicable; source code and
component unit tests remain in their owners.
