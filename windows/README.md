# Cross-platform browser support regression

This contract verifies the local browser-to-protection chain on one required
Android device. A Windows VM may provide optional, non-gating coverage:

```text
passive extension/browser -> authenticated localhost WebSocket
-> platform protection authority -> local model decision
```

The regression uses synthetic pages and aggregate-safe outcomes. It never
visits a real gambling site and never sends browsing data to the backend or a
cloud provider.

## Evaluation matrix

| Platform | Device | Browsers | Per-browser fixtures |
|---|---:|---|---:|
| Android | 1 physical device | Chrome, Edge, Brave, Firefox | 5 non-gambling + 5 gambling |
| Windows | 1 interactive VM | Chrome, Edge, Brave, Opera, Firefox | 5 non-gambling + 5 gambling |

Android is required; Windows is optional and non-gating. Expected outcomes are
`allow` for non-gambling fixtures and `intervention` for gambling fixtures.
These are evaluation candidates, not a claim that all configured browsers are
currently supported by the native monitor. This contract
is separate from the multi-OEM Android anti-uninstall matrix and from latency
measurement.

## Prerequisites

- optional Windows 11 x64 VM with an interactive desktop session;
- optional administrator PowerShell;
- optional Node.js 20+;
- optional five configured Windows browser candidates installed and identifiable by
  executable/channel (`chrome`, `edge`, `brave`, `opera`, and `firefox`);
- optional `GamblockAIProtection` Windows service installed from the current app
  bundle and able to load the current protection assets;
- required Android device with the four configured Android browsers installed;
- the model, app, extension, and testing checkouts at the workspace paths.

The existing Playwright helper is a Chrome-only development harness and is not
yet sufficient to satisfy this cross-platform browser contract. Playwright's bundled
Chromium/Firefox engines are not evidence for branded Chrome, Edge, Brave, or
Opera; the future runner must launch and record only the configured browser
identity. A multi-browser runner, including the Firefox adapter, is still
pending.

## Current status

The canonical status is determined by the required Android cells. Windows is
reported separately when optional evidence is available and does not gate the
Android result. Do not mark this test passed from the existing Chrome-only
smoke test or from source-level checks alone.

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

After the required Android run, and optionally after a Windows run, synchronize
the aggregate result through the normal testing handoff. The canonical result
belongs in `flutter/report.md`; no raw runtime output belongs in the public
repository. The case evidence must use
the platform/browser/case folders defined in
[`../docs/ai/client-runtime-evidence.md`](../docs/ai/client-runtime-evidence.md).
