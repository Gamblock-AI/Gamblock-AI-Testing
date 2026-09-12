# Windows controlled-removal testing

This runbook covers removal resistance for the per-machine Windows pilot MSI.
It is separate from browser-support regression and does not create runtime
evidence until an operator explicitly executes and records a VM run.

## Preconditions

- Use a disposable Windows 11 x64 VM with the current signed pilot MSI.
- Install per-machine and confirm `GamblockAIProtection` runs as LocalSystem
  with SCM recovery enabled.
- Use a participant account in the standard Users group. Keep administrator
  credentials with the pilot operator or accountability authority.
- Use synthetic accounts and never retain tokens, credentials, or machine logs
  in public evidence.

## Scenarios

Record each scenario independently from a restored healthy baseline:

1. Standard-user Apps & Features removal requests elevation and cannot proceed
   without administrator credentials.
2. Standard-user SCM stop, configuration change, and service deletion are
   denied; terminating the user-session agent is recovered by LocalSystem.
3. SCM service failure invokes the configured restart recovery.
4. A partner-approved `uninstall_detected` grant launches the registered system
   `msiexec` removal and consumes the grant exactly once.
5. A two-admin `emergency_access` grant follows the same controlled-removal
   path after explicit user confirmation.
6. Missing, expired, wrong-device, wrong-action, and consumed grants return
   `not_authorized` and do not launch removal.
7. Missing ProductCode or trusted system `msiexec` returns
   `installer_unavailable`; process launch failure returns `launch_failed`.
8. An administrator can still perform a clean direct uninstall, repair, and
   upgrade as the documented break-glass authority.

## Evidence boundary

Source inspection or lint does not pass these scenarios. A retained result
must identify the source commit, MSI identity, VM/OS alias, user privilege,
service before/after state, grant category, structured removal result, and
package presence. Public output contains only these allowlisted outcomes;
screenshots, Event Viewer exports, installer logs, and credentials remain
private/local and are deleted according to the run receipt.
