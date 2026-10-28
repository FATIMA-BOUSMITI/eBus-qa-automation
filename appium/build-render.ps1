param(
    [string]$FlutterExe = "$env:USERPROFILE\Downloads\flutter_windows_3.47.8-stable\flutter\bin\flutter.bat",
    [string]$Source = 'C:\Users\fatouma\Downloads\eBus_front\eBus_front\eBus_front',
    [ValidateSet('android-arm','android-arm64')][string]$TargetPlatform = 'android-arm',
    [switch]$Resume
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $root '.tools/mobile-render-source'
if (-not (Test-Path -LiteralPath $FlutterExe)) { throw 'Flutter SDK executable not found.' }
if ((Test-Path -LiteralPath $destination) -and -not $Resume) { throw 'Render build directory exists. Use -Resume to continue the prepared build.' }
if ($Resume -and -not (Test-Path -LiteralPath $destination)) { throw 'No prepared Render build to resume.' }
$sdk = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
if (-not $Resume) {
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($entry in @('lib','assets','android','pubspec.yaml','pubspec.lock','.metadata')) {
    $item = Join-Path $Source $entry
    if (Test-Path -LiteralPath $item) { Copy-Item -LiteralPath $item -Destination $destination -Recurse }
}
$sdk = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
$flutterRoot = Split-Path (Split-Path (Resolve-Path -LiteralPath $FlutterExe).Path -Parent) -Parent
$utf8 = New-Object System.Text.UTF8Encoding($false)
$properties = @("sdk.dir=$($sdk.Replace('\','/'))", "flutter.sdk=$($flutterRoot.Replace('\','/'))") -join "`n"
[System.IO.File]::WriteAllText((Join-Path $destination 'android/local.properties'), $properties, $utf8)
# A separate package preserves the existing phone app even when signing keys differ.
$gradle = Join-Path $destination 'android/app/build.gradle.kts'
$gradleText = [System.IO.File]::ReadAllText($gradle)
if (-not $gradleText.Contains('    buildTypes {')) { throw 'Expected Android buildTypes block not found.' }
$gradleText = $gradleText.Replace('    buildTypes {', "    buildTypes {`n        debug {`n            applicationIdSuffix = `".render`"`n        }")
# main.dart initializes Firebase explicitly with the existing FirebaseOptions.
# Omit automatic Android resource generation for this separate debug package;
# do not invent a Firebase client registration or alter google-services.json.
$gradleText = $gradleText.Replace('    id("com.google.gms.google-services")', '')
[System.IO.File]::WriteAllText($gradle, $gradleText, $utf8)
$manifest = Join-Path $destination 'android/app/src/main/AndroidManifest.xml'
$manifestText = [System.IO.File]::ReadAllText($manifest).Replace('android:label="eBus"','android:label="eBus Render"')
[System.IO.File]::WriteAllText($manifest, $manifestText, $utf8)
# Avoid the original 8 GB JVM heap on this workstation and unnecessary Gradle docs.
$gradleProperties = Join-Path $destination 'android/gradle.properties'
$gradlePropertiesText = [System.IO.File]::ReadAllText($gradleProperties)
$gradlePropertiesText = [regex]::Replace($gradlePropertiesText, '(?m)^org\.gradle\.jvmargs=.*$', 'org.gradle.jvmargs=-Xmx2G -XX:MaxMetaspaceSize=768m -XX:ReservedCodeCacheSize=256m')
$gradlePropertiesText += "`norg.gradle.workers.max=2`n"
[System.IO.File]::WriteAllText($gradleProperties, $gradlePropertiesText, $utf8)
$wrapper = Join-Path $destination 'android/gradle/wrapper/gradle-wrapper.properties'
[System.IO.File]::WriteAllText($wrapper, ([System.IO.File]::ReadAllText($wrapper).Replace('gradle-8.14-all.zip','gradle-8.14-bin.zip')), $utf8)
}
if (-not ([System.IO.File]::ReadAllText((Join-Path $destination 'android/app/build.gradle.kts'))).Contains('applicationIdSuffix = ".render"')) { throw 'Prepared source is not the isolated Render package.' }
$env:ANDROID_HOME = $sdk
Push-Location $destination
try {
    if (-not $Resume -or -not (Test-Path -LiteralPath '.dart_tool/package_config.json')) {
        & $FlutterExe pub get
        if ($LASTEXITCODE -ne 0) { throw 'Flutter dependency resolution failed.' }
    }
    & $FlutterExe build apk --debug --no-pub --target-platform $TargetPlatform '--dart-define=API_BASE_URL=https://ebus-backend-ao2u.onrender.com'
    if ($LASTEXITCODE -ne 0) { throw 'Render APK build failed.' }
} finally { Pop-Location }
$apk = Join-Path $destination 'build/app/outputs/flutter-apk/app-debug.apk'
@{ apk=$apk; api_url='https://ebus-backend-ao2u.onrender.com'; package='com.example.smart_bus.render'; target_platform=$TargetPlatform; sha256=(Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLower(); built_utc=[DateTime]::UtcNow.ToString('o') } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root '.tools/mobile-render-build.json') -Encoding utf8
Write-Host 'Render APK and SHA256 manifest created. Original frontend and installed local app preserved.'
