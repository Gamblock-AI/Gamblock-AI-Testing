[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'e2e\run.mjs'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    @{ check = 'windows_extension_model_e2e'; status = 'pending'; reason_code = 'node_required' } |
        ConvertTo-Json -Compress
    exit 0
}

# This legacy entrypoint intentionally does not open the protected service
# pipe. The Node script records the safe pending reason until an external
# UI/outcome observation harness replaces it.
& node $runner
exit $LASTEXITCODE
