param(
    [ValidateSet('all','BIZ-001','BIZ-002','BIZ-003','BIZ-004','BIZ-005','BIZ-006','BIZ-007')]
    [string[]]$Case = @('all'),
    [switch]$List,
    [switch]$Headless,
    [string]$PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$savedPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path $root '.tools/qa-addons') + [IO.Path]::PathSeparator + $savedPythonPath
    if (-not $List) {
        $health = Invoke-WebRequest 'http://127.0.0.1:17357/' -UseBasicParsing -TimeoutSec 10
        if ($health.StatusCode -ne 200) { throw 'Start the local Flutter web server on port 17357 first (see docs/playwright-business-e2e.md).' }
    }
    $arguments = @((Join-Path $PSScriptRoot 'business_e2e.py'))
    foreach ($caseId in $Case) { $arguments += @('--case', $caseId) }
    if ($List) { $arguments += '--list' }
    if ($Headless) { $arguments += '--headless' }
    & $PythonExe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Business E2E failed. Read the sanitized report under reports/playwright/business-e2e.' }
} finally { $env:PYTHONPATH = $savedPythonPath }
