$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
$relative = "reports/jmeter/smoke-$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $workspace $relative) | Out-Null
& docker run --rm --mount "type=bind,source=$workspace,target=/workspace" ebus-qa-jmeter:local -n -t /workspace/jmeter/smoke.jmx -l "/workspace/$relative/samples.jtl" -j "/workspace/$relative/jmeter.log" -e -o "/workspace/$relative/dashboard" -Jhost=host.docker.internal -Jport=18080 -Jjmeter.save.saveservice.output_format=csv -Jjmeter.save.saveservice.response_data=false -Jjmeter.save.saveservice.samplerData=false -Jjmeter.save.saveservice.requestHeaders=false -Jjmeter.save.saveservice.responseHeaders=false
if ($LASTEXITCODE -ne 0) { throw 'JMeter process failed' }
$rows = @(Import-Csv (Join-Path $workspace "$relative/samples.jtl"))
if ($rows.Count -ne 7) { throw "Incomplete smoke: expected 7 HTTP samples, got $($rows.Count)" }
$failed = @($rows | Where-Object success -ne 'true')
Write-Output "JMeter samples=$($rows.Count), failed=$($failed.Count), output=$relative"
if ($failed.Count) { throw 'JMeter assertions failed' }
