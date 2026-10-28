param(
    [switch]$Inspect,
    [switch]$Headless,
    [string]$PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    [string]$FrontendBuildPath = 'C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front\build\web'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path -LiteralPath (Join-Path $FrontendBuildPath 'main.dart.js'))) { throw 'Flutter web build missing' }
if (-not (Select-String -LiteralPath (Join-Path $FrontendBuildPath 'main.dart.js') -Pattern 'https://ebus-backend-ao2u.onrender.com' -SimpleMatch -Quiet)) { throw 'Unexpected compiled backend origin' }
if (-not (Test-Path -LiteralPath (Join-Path $root '.tools/mobile-credentials.json'))) { throw 'Existing account credentials file missing' }
try {
    $response = Invoke-WebRequest 'http://127.0.0.1:17357/' -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -ne 200) { throw 'Frontend unavailable' }
} catch {
    $server = Start-Process -FilePath $PythonExe -ArgumentList @('-m','http.server','17357','--bind','127.0.0.1','--directory',$FrontendBuildPath) -WindowStyle Hidden -PassThru
    $server.Id | Set-Content -LiteralPath (Join-Path $root '.tools/ui-server.pid')
}
$savedPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path $root '.tools/qa-addons') + [IO.Path]::PathSeparator + $savedPythonPath
    $arguments = @((Join-Path $PSScriptRoot 'line_lifecycle.py'))
    if ($Inspect) { $arguments += '--inspect' }
    if ($Headless) { $arguments += '--headless' }
    & $PythonExe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Real-backend line E2E failed; see the sanitized summary under reports/playwright/line-lifecycle.' }
} finally { $env:PYTHONPATH = $savedPythonPath }
