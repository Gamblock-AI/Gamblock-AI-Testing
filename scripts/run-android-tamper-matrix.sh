#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  run-android-tamper-matrix.sh preflight --device SERIAL [--package PACKAGE]
  run-android-tamper-matrix.sh capture-before --device SERIAL --state FILE \
    --run-id ID --sample-id ID --device-alias ALIAS --oem-family FAMILY --android-api API \
    --build-mode MODE
  run-android-tamper-matrix.sh record-after --device SERIAL --state FILE --output FILE \
    --scenario SCENARIO --surface SURFACE --action ACTION \
    --observed-action ACTION --expected-outcome OUTCOME --actual-outcome OUTCOME \
    --result RESULT --grant-state STATE --evidence-reference REF [--failure-code CODE]
  run-android-tamper-matrix.sh process-kill|force-stop|reboot --device SERIAL \
    --output FILE --run-id ID --sample-id ID --device-alias ALIAS --oem-family FAMILY \
    --android-api API --build-mode MODE --acknowledge-disposable-device

The manual workflow is: capture-before, perform one system-UI action, then
record-after. Reports contain only allowlisted device labels and state flags.
EOF
}

command_name="${1:-}"
if [[ -z "$command_name" ]]; then usage; exit 2; fi
shift

serial=""
package_name="com.gamblock.gamblock_ai_apps.research"
state_file="private/android-tamper-state.json"
output_file="private/android-tamper.jsonl"
run_id=""; sample_id=""; device_alias=""; oem_family=""; android_api=""; build_mode="profile"
scenario=""; surface=""; action=""; observed_action=""
expected_outcome=""; actual_outcome=""; result=""; grant_state="none"
evidence_reference=""; failure_code=""; recovery_seconds=""; acknowledged="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) serial="${2:-}"; shift 2 ;;
    --package) package_name="${2:-}"; shift 2 ;;
    --state) state_file="${2:-}"; shift 2 ;;
    --output) output_file="${2:-}"; shift 2 ;;
    --run-id) run_id="${2:-}"; shift 2 ;;
    --sample-id) sample_id="${2:-}"; shift 2 ;;
    --device-alias) device_alias="${2:-}"; shift 2 ;;
    --oem-family) oem_family="${2:-}"; shift 2 ;;
    --android-api) android_api="${2:-}"; shift 2 ;;
    --build-mode) build_mode="${2:-}"; shift 2 ;;
    --scenario) scenario="${2:-}"; shift 2 ;;
    --surface) surface="${2:-}"; shift 2 ;;
    --action) action="${2:-}"; shift 2 ;;
    --observed-action) observed_action="${2:-}"; shift 2 ;;
    --expected-outcome) expected_outcome="${2:-}"; shift 2 ;;
    --actual-outcome) actual_outcome="${2:-}"; shift 2 ;;
    --result) result="${2:-}"; shift 2 ;;
    --grant-state) grant_state="${2:-}"; shift 2 ;;
    --evidence-reference) evidence_reference="${2:-}"; shift 2 ;;
    --failure-code) failure_code="${2:-}"; shift 2 ;;
    --recovery-within-seconds) recovery_seconds="${2:-}"; shift 2 ;;
    --acknowledge-disposable-device) acknowledged="true"; shift ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$serial" ]]; then echo "--device is required" >&2; exit 2; fi
adb_cmd=(adb -s "$serial")
package_component="${package_name}/.ProtectionDeviceAdminReceiver"
package_component_full="${package_name}/com.gamblock.gamblock_ai_apps.ProtectionDeviceAdminReceiver"

die() { echo "$*" >&2; exit 2; }

require_label() {
  local name="$1" value="$2"
  [[ "$value" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || die "$name must be an ASCII label of 1-64 characters"
}

require_enum() {
  local name="$1" value="$2" choices="$3"
  case " $choices " in
    *" $value "*) ;;
    *) die "$name must be one of:$choices" ;;
  esac
}

require_common_identity() {
  require_label "--run-id" "$run_id"
  require_label "--sample-id" "$sample_id"
  require_label "--device-alias" "$device_alias"
  require_enum "--oem-family" "$oem_family" " aosp samsung xiaomi_redmi oppo_realme vivo other"
  [[ "$android_api" =~ ^[0-9]+$ && "$android_api" -ge 21 && "$android_api" -le 99 ]] ||
    die "--android-api must be an integer between 21 and 99"
  require_enum "--build-mode" "$build_mode" " debug profile release"
}

require_device() {
  "${adb_cmd[@]}" get-state >/dev/null 2>&1 || die "ADB device is not ready: $serial"
}

app_present() {
  "${adb_cmd[@]}" shell pm path "$package_name" 2>/dev/null | tr -d '\r' | grep -Fq 'package:'
}

admin_active() {
  local policy_dump
  policy_dump="$("${adb_cmd[@]}" shell dumpsys device_policy 2>/dev/null | tr -d '\r')"
  [[ "$policy_dump" == *"$package_component"* || "$policy_dump" == *"$package_component_full"* ]]
}

accessibility_enabled() {
  "${adb_cmd[@]}" shell settings get secure enabled_accessibility_services 2>/dev/null |
    tr -d '\r' | grep -Fq "$package_name"
}

service_running() {
  [[ -n "$("${adb_cmd[@]}" shell pidof "${package_name}:protection" 2>/dev/null | tr -d '\r\n ' )" ]]
}

bool_json() { if "$1"; then echo true; else echo false; fi; }

capture_snapshot() {
  local destination="$1"
  local admin_value accessibility_value service_value app_value
  admin_value="$(bool_json admin_active)"
  accessibility_value="$(bool_json accessibility_enabled)"
  service_value="$(bool_json service_running)"
  app_value="$(bool_json app_present)"
  mkdir -p "$(dirname "$destination")"
  python3 - "$destination" "$run_id" "$sample_id" "$device_alias" "$oem_family" "$android_api" \
    "$build_mode" "$admin_value" "$accessibility_value" "$service_value" "$app_value" <<'PY'
import json
import pathlib
import sys

path, run_id, sample_id, device_alias, oem_family, android_api, build_mode, admin, accessibility, service, app = sys.argv[1:]
boolean = lambda value: value == "true"
payload = {
    "schema_version": 2,
    "run_id": run_id,
    "sample_id": sample_id,
    "device_alias": device_alias,
    "oem_family": oem_family,
    "android_api": int(android_api),
    "flavor": "research",
    "build_mode": build_mode,
    "admin_active_before": boolean(admin),
    "accessibility_enabled_before": boolean(accessibility),
    "service_running_before": boolean(service),
    "app_present_before": boolean(app),
}
target = pathlib.Path(path)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
PY
}

validate_state_file() {
  [[ -s "$state_file" ]] || die "state file does not exist or is empty: $state_file"
  python3 - "$state_file" <<'PY'
import json
import sys
state = json.load(open(sys.argv[1], encoding="utf-8"))
required = {
    "schema_version", "run_id", "sample_id", "device_alias", "oem_family", "android_api",
    "flavor", "build_mode", "admin_active_before",
    "accessibility_enabled_before", "service_running_before", "app_present_before",
}
if state.get("schema_version") != 1 or state.get("flavor") != "research" or not required <= state.keys():
    raise SystemExit("state file is not a valid Research baseline")
PY
}

write_record_from_state() {
  local destination="$1"
  local admin_value accessibility_value service_value app_value
  admin_value="$(bool_json admin_active)"
  accessibility_value="$(bool_json accessibility_enabled)"
  service_value="$(bool_json service_running)"
  app_value="$(bool_json app_present)"
  [[ -n "$failure_code" || "$result" != "failed" ]] || die "--failure-code is required when --result=failed"
  mkdir -p "$(dirname "$destination")"
  python3 - "$state_file" "$destination" "$scenario" "$surface" "$action" \
    "$observed_action" "$expected_outcome" "$actual_outcome" "$result" "$grant_state" \
    "$evidence_reference" "$failure_code" "$recovery_seconds" "$admin_value" \
    "$accessibility_value" "$service_value" "$app_value" <<'PY'
import json
import pathlib
import sys

(
    state_path, output_path, scenario, surface, action, observed_action,
    expected_outcome, actual_outcome, result, grant_state, evidence_reference,
    failure_code, recovery_seconds, admin_after, accessibility_after,
    service_after, app_after,
) = sys.argv[1:]
state = json.loads(pathlib.Path(state_path).read_text(encoding="utf-8"))
record = {
    "schema_version": 2,
    "report_kind": "android_tamper_run",
    "run_id": state["run_id"],
    "sample_id": state["sample_id"],
    "device_alias": state["device_alias"],
    "oem_family": state["oem_family"],
    "android_api": state["android_api"],
    "flavor": state["flavor"],
    "build_mode": state["build_mode"],
    "scenario": scenario,
    "surface": surface,
    "action": action,
    "observed_action": observed_action,
    "expected_outcome": expected_outcome,
    "actual_outcome": actual_outcome,
    "result": result,
    "grant_state": grant_state,
    "admin_active_before": state["admin_active_before"],
    "admin_active_after": admin_after == "true",
    "accessibility_enabled_before": state["accessibility_enabled_before"],
    "accessibility_enabled_after": accessibility_after == "true",
    "service_running_before": state["service_running_before"],
    "service_running_after": service_after == "true",
    "app_present_after": app_after == "true",
    "evidence_reference": evidence_reference,
    "visual_evidence_present": False,
}
if recovery_seconds:
    record["recovery_within_seconds"] = float(recovery_seconds)
if failure_code:
    record["failure_code"] = failure_code
with pathlib.Path(output_path).open("a", encoding="utf-8") as output:
    output.write(json.dumps(record, sort_keys=True) + "\n")
PY
}

validate_manual_record() {
  validate_state_file
  require_enum "--scenario" "$scenario" " setup app_info_passive launcher_uninstall settings_uninstall package_installer_uninstall disable_accessibility force_stop clear_data process_kill reboot valid_grant_removal invalid_grant_removal other_app_uninstall"
  require_enum "--surface" "$surface" " none launcher settings package_installer accessibility_settings app_info"
  require_enum "--action" "$action" " none uninstall disable_accessibility force_stop clear_data process_kill reboot"
  require_enum "--observed-action" "$observed_action" " none uninstall disable_accessibility force_stop clear_data"
  require_enum "--expected-outcome" "$expected_outcome" " blocked warned degraded recovered allowed no_tamper not_applicable"
  require_enum "--actual-outcome" "$actual_outcome" " blocked warned degraded recovered allowed no_tamper failed pending"
  require_enum "--result" "$result" " passed failed pending"
  require_enum "--grant-state" "$grant_state" " none valid invalid expired wrong_device"
  require_label "--evidence-reference" "$evidence_reference"
  [[ -z "$failure_code" ]] || require_label "--failure-code" "$failure_code"
  if [[ -n "$recovery_seconds" ]]; then
    [[ "$recovery_seconds" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "--recovery-within-seconds must be non-negative"
  fi
}

wait_for_pid() {
  local deadline=$((SECONDS + 30))
  while (( SECONDS < deadline )); do
    if service_running; then return 0; fi
    sleep 1
  done
  return 1
}

wait_for_device() {
  local deadline=$((SECONDS + 90))
  while (( SECONDS < deadline )); do
    if "${adb_cmd[@]}" get-state >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  return 1
}

run_lifecycle() {
  [[ "$acknowledged" == "true" ]] || die "$command_name requires --acknowledge-disposable-device"
  require_common_identity
  require_device
  app_present || die "Research package is not installed: $package_name"
  capture_snapshot "$state_file"
  local started=$SECONDS recovered="false" pid_before
  pid_before="$("${adb_cmd[@]}" shell pidof "${package_name}:protection" 2>/dev/null | tr -d '\r\n ' || true)"

  case "$command_name" in
    process-kill)
      [[ -n "$pid_before" ]] || die "protection process must be running before process-kill"
      "${adb_cmd[@]}" shell am kill "$package_name" >/dev/null
      if wait_for_pid; then recovered="true"; fi
      scenario="process_kill"; action="process_kill"; evidence_reference="process_kill_recovery"
      ;;
    force-stop)
      "${adb_cmd[@]}" shell am force-stop "$package_name" >/dev/null
      sleep 2
      local absent_after_force_stop="true"
      if service_running; then absent_after_force_stop="false"; fi
      "${adb_cmd[@]}" shell monkey -p "$package_name" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || true
      if wait_for_pid && [[ "$absent_after_force_stop" == "true" ]]; then recovered="true"; fi
      scenario="force_stop"; action="force_stop"; evidence_reference="force_stop_recovery"
      ;;
    reboot)
      "${adb_cmd[@]}" reboot >/dev/null
      wait_for_device || true
      if wait_for_pid; then recovered="true"; fi
      scenario="reboot"; action="reboot"; evidence_reference="reboot_recovery"
      ;;
  esac

  surface="none"; observed_action="none"; expected_outcome="recovered"
  actual_outcome="$( [[ "$recovered" == "true" ]] && echo recovered || echo failed )"
  result="$( [[ "$recovered" == "true" ]] && echo passed || echo failed )"
  if [[ "$result" == "failed" ]]; then failure_code="protection_not_recovered"; fi
  recovery_seconds=$((SECONDS - started))
  write_record_from_state "$output_file"
  echo "Android tamper evidence written to $output_file"
  [[ "$result" == "passed" ]]
}

case "$command_name" in
  preflight)
    require_device
    app_present || die "Research package is not installed: $package_name"
    printf '%s\n' \
      "ADB device: ready" \
      "Package: installed" \
      "Device Admin active: $(bool_json admin_active)" \
      "Accessibility enabled: $(bool_json accessibility_enabled)" \
      "Protection process running: $(bool_json service_running)"
    ;;
  capture-before)
    require_common_identity
    require_device
    app_present || die "Research package is not installed: $package_name"
    capture_snapshot "$state_file"
    echo "Baseline state written to $state_file"
    ;;
  record-after)
    require_device
    validate_manual_record
    write_record_from_state "$output_file"
    echo "Android tamper evidence written to $output_file"
    ;;
  process-kill|force-stop|reboot)
    run_lifecycle
    ;;
  *)
    echo "Unknown command: $command_name" >&2
    usage
    exit 2
    ;;
esac
