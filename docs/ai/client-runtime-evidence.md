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

The case folders are therefore the smallest reportable unit. Every required
case folder must contain both `summary.json` and `samples.jsonl`; a missing
platform, browser, case folder, or file is a missing required matrix cell and
keeps the corresponding evaluation `pending`.

## File contract

Each case folder must contain the two aggregate-safe files declared by the
target configuration:

- `summary.json`: counts, metrics, expected/actual outcome totals, build and
  artifact identity, and validation status for that cell;
- `samples.jsonl`: opaque sample labels and allowlisted expected/actual class or
  outcome fields needed to reproduce the aggregate counts.

Both files use schema version `1`. The summary is the current aggregate for
one cell and must contain these fields:

```text
schema_version, test, platform, browser (browser test only), case,
device_alias, build_mode, product_flavor, artifact, run_id, sample_count,
status
```

The model summary additionally contains `expected_class` and
`correct_sample_count`, `evaluation_scope`, and the exact `components` list
required by the active Hybrid target; the browser summary additionally contains
`expected_outcome` and `passed_sample_count`. The sample JSONL records must
contain the same cell/build identity plus `sample_id`, `result`, and either
`expected_class`/`actual_class` or `expected_outcome`/`actual_outcome`.

The validator requires exactly the configured number of samples in each cell:
50 per class for the balanced model evaluation and 5 per class per browser for
the browser regression. A cell has one opaque `run_id`, unique `sample_id`
values, and one safe `device_alias`; duplicate IDs, mixed runs, extra fields,
wrong artifact identities, and invalid outcomes fail validation. An empty or
short sample file remains `pending`; a complete cell with incorrect outcomes
is `failed`. The model status is computed from all samples and its 90%/5% gate,
not trusted from a summary field. The browser status is computed from the
allow/intervention assertions, also not trusted from a summary field.

Multiple runs do not create another directory dimension. A new run replaces
the current cell aggregate only after validation; historical raw runs remain
private. If a future test requires another dimension, add it first to the
active target configuration and this document.

The balanced model test evaluates the full deployed local Hybrid artifact
(rules, URL features, DOM/text features, and serialized Logistic Regression)
in the Research Android and Windows release artifacts. It is a runtime gate
and is intentionally separate from offline model replay evidence under
`model/evidence/`.

## Privacy boundary

Public files may never contain URLs, domains, raw DOM/text, screenshots,
browsing history, credentials, tokens, device serials, raw ADB/logcat output,
or browser logs. Raw runtime exports remain under the ignored technology
`private/` area or an external temporary directory until an evidence promoter
and validator have reduced them to the allowlisted aggregate schema.

The five-browser lists are required evaluation candidates, not a claim that
each browser is already supported by the product. A browser remains unverified
until its complete cell passes; product support gaps must be recorded as a
runtime failure or an explicit implementation gap, never inferred from the
matrix declaration.

These folders are not alternate reports. The single canonical result remains
[`flutter/report.md`](../../flutter/report.md), which summarizes all valid
platform/browser/case folders.
