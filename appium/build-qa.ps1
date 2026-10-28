param(
    [Parameter(Mandatory=$true)][string]$FlutterExe,
    [string]$Source = 'C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $root '.tools/mobile-source'
if (-not (Test-Path -LiteralPath $FlutterExe)) { throw 'Flutter SDK executable not found.' }
if (Test-Path -LiteralPath $destination) { throw 'Build directory exists. Use the existing recorded build or move it aside before rebuilding.' }
New-Item -ItemType Directory -Path $destination -Force | Out-Null
# Copy only build inputs. Original Downloads files and app data are preserved.
foreach ($entry in @('lib','assets','android','pubspec.yaml','pubspec.lock','.metadata')) {
    $item = Join-Path $Source $entry
    if (Test-Path -LiteralPath $item) { Copy-Item -LiteralPath $item -Destination $destination -Recurse }
}
$sdk = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
$flutterRoot = Split-Path (Split-Path (Resolve-Path -LiteralPath $FlutterExe).Path -Parent) -Parent
$properties = @("sdk.dir=$($sdk.Replace('\','/'))", "flutter.sdk=$($flutterRoot.Replace('\','/'))") -join "`n"
[System.IO.File]::WriteAllText((Join-Path $destination 'android/local.properties'), $properties, (New-Object System.Text.UTF8Encoding($false)))
# Cleartext is permitted only in this isolated debug build for loopback QA.
$debugManifest = Join-Path $destination 'android/app/src/debug/AndroidManifest.xml'
@'
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <application android:usesCleartextTraffic="true" />
</manifest>
'@ | Set-Content -LiteralPath $debugManifest -Encoding utf8
Push-Location $destination
try {
    & $FlutterExe pub get
    if ($LASTEXITCODE -ne 0) { throw 'Flutter dependency resolution failed.' }
    & $FlutterExe build apk --debug '--dart-define=API_BASE_URL=http://127.0.0.1:18080'
    if ($LASTEXITCODE -ne 0) { throw 'QA APK build failed.' }
} finally { Pop-Location }
$apk = Join-Path $destination 'build/app/outputs/flutter-apk/app-debug.apk'
@{ apk=$apk; api_url='http://127.0.0.1:18080'; sha256=(Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLower(); built_utc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root '.tools/mobile-build.json') -Encoding utf8
Write-Host 'QA APK and SHA256 manifest created. Original frontend preserved.'
