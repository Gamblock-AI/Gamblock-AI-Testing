# Windows extension–model integration test

This runbook verifies the real local chain:

```text
Chrome + passive extension -> authenticated localhost WebSocket
-> Windows protection service -> current Hybrid-v2 artifacts -> intervention
```

The test uses synthetic pages served from `127.0.0.1`. It never visits a real
gambling site and never sends browsing data to the backend or a cloud provider.

## Prerequisites

- Windows 11 x64 VM with an interactive desktop session;
- administrator PowerShell;
- Node.js 20+;
- Chrome Stable;
- the `GamblockAIProtection` Windows service installed from the current app
  bundle and able to load the current protection assets;
- the model, app, extension, and testing checkouts at the workspace paths.

Install the E2E dependency once from `gamblock-ai-testing/windows/e2e/`:

```powershell
npm ci
npx playwright install chromium
```

## Run

From the testing repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\windows\run-extension-model-e2e.ps1 \
  -WorkspaceRoot C:\src\gamblock-ai
```

The script starts the installed service if needed, runs seven scenarios in
Chrome Release, and stops the service again when it was not running before the
test. The final line is one aggregate JSON object. Failure output contains only
an opaque reason code; raw pages, URLs, DOM text, screenshots, tokens, and
browser logs are not emitted or retained by the harness.

The test is intentionally a runtime smoke test, not the full Phase 4 latency
gate. The selected report version's progress checkpoint is the separate Android
`researchRelease` demo capture (v5 is the historical PKM v5 checkpoint); Windows
contributes to the retained final-readiness matrix, which requires the
separately validated minimum sample count for every configured
platform/browser/profile-or-release cell.

## Evidence handoff

Use the testing runner from the testing repository root after the Windows run:

```powershell
python docs/tools/run_evaluation.py \
  --workspace-root C:\src\gamblock-ai \
  --run-code-tests --component flutter --include-windows-e2e
```

On non-Windows hosts, the corresponding check remains `pending` with the exact
environment reason. The canonical aggregate result belongs in
`flutter/report.md`; no raw runtime output belongs in the public repository.
