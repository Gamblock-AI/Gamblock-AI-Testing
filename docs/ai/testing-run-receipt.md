# Testing run receipt

This document defines the mandatory handoff for an explicit test, evaluation,
or re-evaluation request. It does not create another testing summary. The
technology report remains the only canonical human-readable result:

```text
<technology>/report.md
```

## Completion rule

A test is complete only when the matching report in
`gamblock-ai-testing/` has been regenerated through the testing runner, or
when the report remains `pending`/`blocked` with the exact synchronization
reason stated. A direct command in a component repository is not sufficient.

The agent must inspect both repositories before handoff:

```sh
git status --short
git diff --stat
```

Run these from the umbrella and from `gamblock-ai-testing/`, while preserving
unrelated changes. The agent must not commit or push automatically unless the
user has authorized that action.

## Required final-response format

```text
Test receipt
- Run ID/sample:
- Technology and scope:
- Command or runtime procedure:
- Status: passed | failed | partial | pending | blocked
- Source repository commit(s):

Testing repository changes
- Public files added/modified: <paths, or none>
- Public data added: <aggregate metrics/labels/statuses, or none>
- Private/local artifacts created: <paths or external temp class, or none>
- Private data description: <safe description, or none>
- Private artifact retention: deleted | remains local | not applicable

Validation and publication
- Context validator:
- Public-evidence validator:
- Testing-repository commit:
- Push status:
```

The public-file list must include the canonical report and any promoted
technology ledger that changed. For Android runtime evidence, name the
per-device ledger path under `flutter/evidence/ledger/<device_alias>/` and
state whether it was appended to an existing device file. It must not include raw URLs, domains, DOM,
browsing history, screenshots, ADB/logcat traces, serial numbers, credentials,
participant data, or raw command output.

For a new Android device, keep the release-artifact provenance (source commit,
APK version and digest, signing-certificate fingerprint, Android API, and
browser version) in the private/local portion of the receipt. Only the
allowlisted aggregate labels, outcomes, timings, state flags, and approved
hashes may enter the public ledger.

Private artifacts may be described by their path class and purpose, but their
contents must not be pasted into the response. Temporary model replay outputs
are normally external temporary files and should be reported as deleted after
the runner exits. Android screenshots and device traces remain local and are
reported as retained or deleted without exposing their filename, path, or
contents publicly.

If no file changed because the regenerated aggregate result is identical,
write `none (report regenerated; no content diff)` rather than claiming that
the repository was not checked. If the runner could not be invoked, write the
exact blocker and leave the affected report pending or blocked.
