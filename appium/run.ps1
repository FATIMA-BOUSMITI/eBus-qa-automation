param(
    [switch]$DryRun,
    [switch]$RemoteInstalled,
    [switch]$Authenticated,
    [string]$Serial,
    [string]$TestPattern,
    [string]$RerunFailedFrom,
    [string]$PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$env:PYTHONPATH = Join-Path $root '.tools/mobile-addons'
$env:APPIUM_HOME = Join-Path $root '.tools/appium-home'
$env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
$suite = Join-Path $PSScriptRoot 'tests/android.robot'
$env:MOBILE_AUTHENTICATED = $(if ($Authenticated) { '1' } else { '0' })
if ($Authenticated) {
    $suite = Join-Path $PSScriptRoot 'tests/authenticated.robot'
    if (-not $DryRun) {
        $credentialsPath = Join-Path $root '.tools/mobile-credentials.json'
        if (-not (Test-Path -LiteralPath $credentialsPath)) { throw 'Missing .tools/mobile-credentials.json. See appium/README.md.' }
        $accounts = Get-Content -Raw -LiteralPath $credentialsPath | ConvertFrom-Json
        foreach ($alias in @('ACCOUNT1', 'ACCOUNT2', 'ACCOUNT3')) {
            $account = $accounts.$alias
            if (-not $account.email -or -not $account.password) { throw "Missing credentials for $alias" }
            [Environment]::SetEnvironmentVariable("EBUS_${alias}_EMAIL", $account.email, 'Process')
            [Environment]::SetEnvironmentVariable("EBUS_${alias}_PASSWORD", $account.password, 'Process')
        }
    }
}
$output = Join-Path $root ('reports/appium/' + $(if ($DryRun) { 'dry-run' } else { Get-Date -Format 'yyyyMMdd-HHmmss' }))
if ($DryRun) {
    & $PythonExe -m robot --dryrun --outputdir $output $suite
    if ($LASTEXITCODE -ne 0) { throw 'Robot static validation failed.' }
    return
}
$env:MOBILE_TARGET = $(if ($RemoteInstalled) { 'render-readonly' } else { 'local-qa' })
$env:MOBILE_BUILD_MANIFEST = Join-Path $root $(if ($RemoteInstalled) { '.tools/mobile-render-build.json' } else { '.tools/mobile-build.json' })
if (-not (Test-Path -LiteralPath $env:MOBILE_BUILD_MANIFEST)) {
    throw 'No recorded APK for the selected backend. Run build-render.ps1 or build-qa.ps1 first.'
}
$adb = Join-Path $env:ANDROID_HOME 'platform-tools/adb.exe'
$devices = & $adb devices
if ($LASTEXITCODE -ne 0) { throw 'ADB failed.' }
$online = @($devices | Where-Object { $_ -match '^\S+\s+device\s*$' } | ForEach-Object { ($_ -split '\s+')[0] })
if (-not $Serial -and $online.Count -eq 1) { $Serial = $online[0] }
if (-not $Serial -or $Serial -notin $online) { throw 'Select an online QA emulator/device with -Serial. See adb devices.' }
$env:ANDROID_SERIAL = $Serial
if ($RemoteInstalled) {
    # A PC probe is only warming: the phone can use a different network route.
    # The actual mobile startup/login and catalogue assertions remain mandatory.
    try {
        $httpCode = & curl.exe --ipv4 --silent --show-error --connect-timeout 10 --max-time 20 -o NUL -w '%{http_code}' 'https://ebus-backend-ao2u.onrender.com/api/health'
        if ($LASTEXITCODE -ne 0 -or $httpCode -ne '200') { Write-Warning 'PC health probe did not return 200. Device assertions will verify the mobile path.' }
    } catch { Write-Warning 'PC health probe unavailable. Device startup and data assertions remain mandatory.' }
} else {
    & $adb -s $Serial reverse tcp:18080 tcp:18080
    if ($LASTEXITCODE -ne 0) { throw 'Cannot forward the dedicated QA backend to Android.' }
    $health = Invoke-WebRequest 'http://127.0.0.1:18080/api/health' -UseBasicParsing -TimeoutSec 15
    if ($health.StatusCode -ne 200) { throw 'Local QA backend is unavailable.' }
}
$status = Invoke-RestMethod 'http://127.0.0.1:4723/status' -TimeoutSec 10
if (-not $status.value.ready) { throw 'Local Appium server is not ready.' }
$robotArguments = @('--outputdir', $output)
if ($TestPattern) { $robotArguments += @('--test', $TestPattern) }
if ($RerunFailedFrom) { $robotArguments += @('--rerunfailed', (Resolve-Path -LiteralPath $RerunFailedFrom).Path) }
$robotArguments += $suite
try {
    & $PythonExe -m robot @robotArguments
    if ($LASTEXITCODE -ne 0) { throw "Android tests failed. Review $output/report.html" }
} finally {
    if ($Authenticated) {
        foreach ($alias in @('ACCOUNT1', 'ACCOUNT2', 'ACCOUNT3')) {
            [Environment]::SetEnvironmentVariable("EBUS_${alias}_EMAIL", $null, 'Process')
            [Environment]::SetEnvironmentVariable("EBUS_${alias}_PASSWORD", $null, 'Process')
        }
    }
}
