[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$ServiceName = 'GamblockAIProtection',
    [string]$BrowserExecutable
)

$ErrorActionPreference = 'Stop'
# Legacy Chrome-only development smoke helper. It cannot populate the
# cross_platform_browser_support_regression evidence matrix.
$e2eRoot = Join-Path $PSScriptRoot 'e2e'
$runner = Join-Path $e2eRoot 'run.mjs'

function Write-Pending([string]$Reason) {
    @{ check = 'windows_extension_model_e2e'; status = 'pending'; reason_code = $Reason } |
        ConvertTo-Json -Compress
    exit 0
}

if (-not [Environment]::Is64BitOperatingSystem) {
    Write-Pending 'windows_64_bit_required'
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Pending 'administrator_required'
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Pending 'node_required'
}

if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    Write-Pending 'e2e_runner_missing'
}

$playwrightModule = Join-Path $e2eRoot 'node_modules\playwright'
if (-not (Test-Path -LiteralPath $playwrightModule -PathType Container)) {
    Write-Pending 'run_npm_ci_in_windows_e2e'
}

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -eq $service) {
    Write-Pending 'windows_service_not_installed'
}

$wasRunning = $service.Status -eq 'Running'
try {
    if (-not $wasRunning) {
        Start-Service -Name $ServiceName
        $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(20))
    }

    $arguments = @(
        $runner,
        '--workspace-root', $WorkspaceRoot,
        '--app-root', (Join-Path $WorkspaceRoot 'gamblock_ai_apps'),
        '--model-root', (Join-Path $WorkspaceRoot 'gamblock-ai-model'),
        '--extension-root', (Join-Path $WorkspaceRoot 'browser_extension'),
        '--service-name', $ServiceName
    )
    if (-not [string]::IsNullOrWhiteSpace($BrowserExecutable)) {
        $arguments += @('--browser-executable', $BrowserExecutable)
    }

    & node @arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        exit $exitCode
    }
}
finally {
    if (-not $wasRunning) {
        Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
    }
}
