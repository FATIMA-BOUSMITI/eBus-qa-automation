param(
    [Parameter(Mandatory=$true)][string]$ConnectAddress,
    [string]$PairAddress
)
$ErrorActionPreference = 'Stop'
$adb = Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe'
function Assert-LanEndpoint([string]$Endpoint) {
    if ($Endpoint -notmatch '^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$') { throw 'Expected phone IPv4:port from Wireless debugging.' }
    $addressText = $Matches[1]
    $port = [int]$Matches[2]
    $address = $null
    if (-not [System.Net.IPAddress]::TryParse($addressText, [ref]$address) -or $port -lt 1 -or $port -gt 65535) { throw 'Invalid phone address/port.' }
    $bytes = $address.GetAddressBytes()
    # Accept the explicit phone address, including shared/VPN network ranges.
    # Never discover or scan other hosts.
    if ($bytes[0] -eq 0 -or $bytes[0] -eq 127 -or $bytes[0] -ge 224 -or $addressText -eq '255.255.255.255') { throw 'Use the unicast IPv4 address displayed by your phone.' }
}
Assert-LanEndpoint $ConnectAddress
if ($PairAddress) {
    Assert-LanEndpoint $PairAddress
    # ADB prompts for the temporary code. Never save it or put it in arguments.
    & $adb pair $PairAddress
    if ($LASTEXITCODE -ne 0) { throw 'Pairing failed. Keep the pairing dialog open and retry with its current address/code.' }
}
& $adb connect $ConnectAddress
if ($LASTEXITCODE -ne 0) { throw 'Wi-Fi connection failed.' }
$state = & $adb -s $ConnectAddress get-state
if ($LASTEXITCODE -ne 0 -or $state -notcontains 'device') { throw 'Phone is not online. Use the main Wireless debugging port, not the pairing port.' }
& $adb devices -l
Write-Host "Connected. Appium device serial: $ConnectAddress"
