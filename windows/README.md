# Cross-platform browser support regression

This contract verifies the local browser-to-protection chain on one Android
device and one Windows VM across the required evaluation-browser matrix:

```text
passive extension/browser -> authenticated localhost WebSocket
-> platform protection authority -> local model decision
```

The regression uses synthetic pages and aggregate-safe outcomes. It never
visits a real gambling site and never sends browsing data to the backend or a
cloud provider.

## Required evaluation matrix

| Platform | Device | Browsers | Per-browser fixtures |
|---|---:|---|---:|
| Android | 1 physical device | Chrome, Edge, Samsung Internet, Brave, Firefox | 5 non-gambling + 5 gambling |
| Windows | 1 interactive VM | Chrome, Edge, Brave, Opera, Firefox | 5 non-gambling + 5 gambling |

Expected outcomes are `allow` for non-gambling fixtures and `intervention` for
gambling fixtures. These are required evaluation candidates, not a claim that
all five browsers are currently supported by the native monitor. This contract
is separate from the multi-OEM Android anti-uninstall matrix and from latency
measurement.

## Prerequisites

- Windows 11 x64 VM with an interactive desktop session;
- administrator PowerShell;
- Node.js 20+;
- the five configured Windows browser candidates installed and identifiable by
  executable/channel (`chrome`, `edge`, `brave`, `opera`, and `firefox`);
- the `GamblockAIProtection` Windows service installed from the current app
  bundle and able to load the current protection assets;
- Android device with the five configured Android browsers installed;
- the model, app, extension, and testing checkouts at the workspace paths.

The existing Playwright helper is a Chrome-only development harness and is not
yet sufficient to satisfy this five-browser contract. Playwright's bundled
Chromium/Firefox engines are not evidence for branded Chrome, Edge, Brave, or
Opera; the future runner must launch and record only the configured browser
identity. A multi-browser runner, including the Firefox adapter, is still
pending.

## Current status

The canonical status is `pending`: no complete Android + Windows matrix has
been executed or promoted as public evidence. Do not mark this test passed from
the existing Chrome-only smoke test or from source-level checks.

When the multi-browser harness is available, install its dependencies from
`gamblock-ai-testing/windows/e2e/`:

```powershell
npm ci
npx playwright install chromium firefox
```

The command installs test engines only. It does not install the branded
browser candidates required by the matrix.

## Future run

The final run command will be documented when the multi-browser harness is
implemented. It must emit only aggregate browser/platform outcomes and must
not retain raw pages, URLs, DOM text, screenshots, tokens, or browser logs.

## Evidence handoff

After both platform runs, synchronize the aggregate result through the normal
testing handoff. The canonical result belongs in `flutter/report.md`; no raw
runtime output belongs in the public repository. The case evidence must use
the platform/browser/case folders defined in
[`../docs/ai/client-runtime-evidence.md`](../docs/ai/client-runtime-evidence.md).
