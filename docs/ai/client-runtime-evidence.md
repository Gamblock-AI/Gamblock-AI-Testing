# Flutter client-runtime evidence layout

This document defines the public evidence folder contract for the two pending
Flutter client-runtime evaluations. It does not create evidence or change
their current `pending` status.

## Fixed dimensions

Evidence is separated by the dimensions that define the test cell. Directory
names must use the exact lowercase ASCII values from
[`docs/config/targets.json`](../config/targets.json):

- `platform`: `android` or `windows`;
- `browser`: the configured browser identifier, only for browser-support
  regression; and
- `case`: `gambling` or `non_gambling`.

Do not use display names, device serials, URLs, domains, or free-form names in
public paths. A device remains identified by the existing safe `device_alias`
inside aggregate records; it does not become a new test dimension.

## Directory layout

The balanced model evaluation uses one case folder below each platform:

```text
flutter/evidence/client-runtime/flutter_local_model_balanced_evaluation/
├── android/
│   ├── gambling/
│   │   ├── summary.json
│   │   └── samples.jsonl
│   └── non_gambling/
│       ├── summary.json
│       └── samples.jsonl
└── windows/
    ├── gambling/
    │   ├── summary.json
    │   └── samples.jsonl
    └── non_gambling/
        ├── summary.json
        └── samples.jsonl
```

The browser-support regression adds the browser dimension between platform and
case:

```text
flutter/evidence/client-runtime/cross_platform_browser_support_regression/
├── android/<browser>/<case>/{summary.json,samples.jsonl}
└── windows/<browser>/<case>/{summary.json,samples.jsonl}
```

The required browser directories are:

| Platform | Browser directories |
|---|---|
| Android | `chrome`, `edge`, `samsung_internet`, `brave`, `firefox` |
| Windows | `chrome`, `edge`, `brave`, `opera`, `firefox` |

The case folders are therefore the smallest reportable unit. A missing
platform, browser, or case folder is a missing required matrix cell and keeps
the corresponding evaluation `pending`.

## File contract

Each case folder may contain the two aggregate-safe files declared by the
target configuration:

- `summary.json`: counts, metrics, expected/actual outcome totals, build and
  artifact identity, and validation status for that cell;
- `samples.jsonl`: opaque sample labels and allowlisted expected/actual class or
  outcome fields needed to reproduce the aggregate counts.

Multiple runs remain records in these files with an opaque `run_id`; do not
create one-run directories or add an uncontracted directory dimension. If a
future test requires another dimension, add it first to the active target
configuration and this document.

## Privacy boundary

Public files may never contain URLs, domains, raw DOM/text, screenshots,
browsing history, credentials, tokens, device serials, raw ADB/logcat output,
or browser logs. Raw runtime exports remain under the ignored technology
`private/` area or an external temporary directory until an evidence promoter
and validator have reduced them to the allowlisted aggregate schema.

These folders are not alternate reports. The single canonical result remains
[`flutter/report.md`](../../flutter/report.md), which summarizes all valid
platform/browser/case folders.
