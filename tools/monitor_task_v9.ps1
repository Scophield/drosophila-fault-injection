param([string]$Output = 'audit/acceptance-v9/resource-samples.jsonl')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$destination = Join-Path $root $Output
if (Test-Path -LiteralPath $destination) { throw 'Choose a new resource log; do not overwrite' }
$deadline = [DateTime]::UtcNow.AddHours(8)
while ([DateTime]::UtcNow -lt $deadline) {
    $campaigns = @()
    foreach ($campaign in @('task-v9-test', 'task-v9-stress')) {
        $active = Join-Path $root "runs/$campaign/active.json"
        if (!(Test-Path -LiteralPath $active)) { continue }
        $configuration = Get-Content -LiteralPath $active -Raw | ConvertFrom-Json
        $workers = @()
        foreach ($workerId in $configuration.pids) {
            $process = Get-Process -Id $workerId -ErrorAction SilentlyContinue
            if ($null -eq $process -or $process.ProcessName -ne 'python') { continue }
            $workers += [ordered]@{pid=$process.Id; start_utc=$process.StartTime.ToUniversalTime().ToString('o'); cpu_seconds=$process.TotalProcessorTime.TotalSeconds; working_set_bytes=$process.WorkingSet64; process_peak_working_set_bytes=$process.PeakWorkingSet64; threads=$process.Threads.Count}
        }
        $count = @(Get-ChildItem -LiteralPath (Join-Path $root "runs/$campaign/episodes") -Filter '*.json' -File).Count
        $campaigns += [ordered]@{campaign=$campaign; episodes=$count; workers=$workers}
    }
    $record = [ordered]@{utc=[DateTime]::UtcNow.ToString('o'); campaigns=$campaigns; note='45-second process samples, started after core launch; CPU values are cumulative, worker peaks are per-process OS peaks, not a simultaneous campaign peak.'}
    $line = $record | ConvertTo-Json -Depth 8 -Compress
    Add-Content -LiteralPath $destination -Value $line -Encoding utf8
    Write-Output $line
    if (Test-Path -LiteralPath (Join-Path $root 'audit/acceptance-v9/measurements-complete.json')) { break }
    Start-Sleep -Seconds 45
}
