# Public runtime evidence ledger

Runtime evidence is grouped by the safe `device_alias` recorded in each
aggregate JSONL record. Keep one folder per device:

```text
<device_alias>/android-tamper.jsonl
<device_alias>/phase4-latency.jsonl
```

Use the exact ASCII alias from the public device register and keep it
immutable after evidence is published. If the same model appears more than
once, use a unique suffix such as `_local_01` or `_firebase_01` rather than
merging unrelated devices. A folder may contain both ledger kinds when the
same device runs both anti-uninstall and Phase 4 latency procedures. Each
device file may contain multiple runs; keep `run_id` unique for each batch and
`sample_id` unique across all device folders. Do not create one-run subfolders:
the report generator discovers the two ledger filenames directly below each
device folder and renders one aggregate technology report.

The device register is currently scoped to Android Research anti-uninstall
provenance. A latency-only result, such as the Redmi 12C release run, does not
automatically change that device's anti-uninstall `pending_retest` status.

Only validator-approved aggregate fields belong here. Never add raw URLs,
domains, DOM text, browsing history, screenshots, device serials, credentials,
or raw ADB/logcat output. Stage raw exports under the technology's ignored
`private/` directory or an external temporary directory, validate them, then
promote them to the matching device folder. The promoter merges with an
existing device ledger atomically; it rejects duplicate samples, mixed device
aliases, and root-level output. Never use shell redirection or manually
overwrite an existing ledger.

The pending Flutter browser-support evaluation does not use this device ledger.
Its evidence is grouped by platform, browser, and case under
[`../client-runtime`](../client-runtime) according to
[`../../../docs/ai/client-runtime-evidence.md`](../../../docs/ai/client-runtime-evidence.md).
