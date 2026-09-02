# Gamblock-AI Flutter / Android Report

This is the canonical aggregate report for this technology. It is
generated from validated public evidence and aggregate command results.
Raw URL, domain, DOM, browsing history, screenshot, serial, credential,
participant, and raw log data are never included.

This report covers Flutter client checks and Android Research runtime evidence.

## Android anti-uninstall

| Status | Samples | Groups | OEM families | Scenarios | Coverage complete |
|---|---:|---:|---:|---:|---|
| partial | 7 | 7 | 1 | 7 | False |

## Phase 4 latency

| Status | Groups | Passed groups |
|---|---:|---:|
| pending | 0 | 0 |

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


## Android device retest queue (not evidence)

These device records are planning metadata only. They do not contribute
to Android samples, groups, OEM coverage, scenario coverage, or pass rates.
A blank result means that no prior informal outcome has been promoted.

| Device | OEM | Source | Service | Android API | Build | Status | Result | Retest required |
|---|---|---|---|---:|---|---|---|---|
| Redmi 12C | xiaomi_redmi | local_physical_device | local_physical_device | — | — | pending_retest | — | true |

## Android testing context

Service and cross-OEM interpretation are maintained in
[`docs/ai/android-anti-uninstall-context.md`](../docs/ai/android-anti-uninstall-context.md).

## Component checks

| Check | Status |
|---|---|
| flutter_component_checks | pending |

## Interpretation limits

Offline replay is not physical browser, Android, or Windows runtime proof.
A missing matrix cell remains pending. This report contains aggregate-safe
results and validated scenario detail where applicable; source code and
component unit tests remain in their owners.
