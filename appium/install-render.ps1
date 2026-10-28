param([Parameter(Mandatory=$true)][string]$Serial)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$record = Get-Content -LiteralPath (Join-Path $root '.tools/mobile-render-build.json') -Raw | ConvertFrom-Json
if ($record.api_url -ne 'https://ebus-backend-ao2u.onrender.com' -or $record.package -ne 'com.example.smart_bus.render') { throw 'Unexpected APK target/package.' }
if ((Get-FileHash -LiteralPath $record.apk -Algorithm SHA256).Hash -ine $record.sha256) { throw 'Recorded APK checksum differs.' }
$sdk = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
$adb = Join-Path $sdk 'platform-tools/adb.exe'
$state = & $adb -s $Serial get-state
if ($LASTEXITCODE -ne 0 -or $state -notcontains 'device') { throw 'Redmi is offline. Reconnect Wireless debugging before installing; no install was attempted.' }
$buildTools = Get-ChildItem (Join-Path $sdk 'build-tools') -Directory | Sort-Object Name -Descending | Select-Object -First 1
$badging = & (Join-Path $buildTools.FullName 'aapt.exe') dump badging $record.apk
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect APK metadata.' }
$packageLine = $badging | Where-Object { $_ -match '^package:' } | Select-Object -First 1
if ($packageLine -notmatch "name='com\.example\.smart_bus\.render'") { throw 'APK is not the isolated Render package.' }
$activityLine = $badging | Where-Object { $_ -match '^launchable-activity:' } | Select-Object -First 1
if ($activityLine -notmatch "name='([^']+)'") { throw 'APK has no launchable activity.' }
$activity = $Matches[1]
$before = (& $adb -s $Serial shell pm path com.example.smart_bus) -join "`n"
& $adb -s $Serial install -r $record.apk
if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Original application will not be uninstalled or cleared.' }
& $adb -s $Serial shell am start -n "$($record.package)/$activity"
if ($LASTEXITCODE -ne 0) { throw 'Render app launch failed.' }
$after = (& $adb -s $Serial shell pm path com.example.smart_bus) -join "`n"
if ($before -ne $after) { throw 'Original app package path unexpectedly changed.' }
Write-Host 'eBus Render installed and launched. Original eBus package preserved.'
