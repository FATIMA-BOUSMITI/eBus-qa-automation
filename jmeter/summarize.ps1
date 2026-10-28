param([Parameter(Mandatory=$true)][string]$ResultsDirectory)
$ErrorActionPreference = 'Stop'
$samples = @(Import-Csv (Join-Path $ResultsDirectory 'samples.jtl'))
if (-not $samples.Count) { throw 'No measured samples' }
$elapsed = @($samples | ForEach-Object { [double]$_.elapsed } | Sort-Object)
function Percentile([double]$fraction) { $elapsed[[Math]::Max(0, [Math]::Ceiling($elapsed.Count * $fraction)-1)] }
$first = ($samples | ForEach-Object { [double]$_.timeStamp } | Measure-Object -Minimum).Minimum
$last = ($samples | ForEach-Object { [double]$_.timeStamp+[double]$_.elapsed } | Measure-Object -Maximum).Maximum
$failed = @($samples | Where-Object success -ne 'true').Count
$durationSeconds = ($last-$first)/1000
$summary = [ordered]@{
    timestamp = [DateTime]::UtcNow.ToString('o')
    sampleCount = $samples.Count
    failedSamples = $failed
    errorRatePercent = [Math]::Round(100*$failed/$samples.Count, 2)
    meanMs = [Math]::Round(($elapsed | Measure-Object -Average).Average, 2)
    p90Ms = Percentile 0.90
    p95Ms = Percentile 0.95
    p99Ms = Percentile 0.99
    measuredDurationSeconds = [Math]::Round($durationSeconds, 3)
    throughputPerSecond = $(if ($durationSeconds -gt 0) { [Math]::Round($samples.Count/$durationSeconds, 3) } else { $null })
    percentileMethod = 'Nearest rank across measured HTTP samples'
    limitation = 'One-user smoke only, seven heterogeneous samples; not a load baseline or capacity estimate.'
}
$summary | ConvertTo-Json | Set-Content (Join-Path $ResultsDirectory 'summary.json') -Encoding UTF8
$summary | ConvertTo-Json
