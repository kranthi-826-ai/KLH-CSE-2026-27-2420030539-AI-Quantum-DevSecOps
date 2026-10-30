param([Parameter(Mandatory=$true)][string]$RunDirectory)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$artifactRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'ml\artifacts')).TrimEnd('\') + '\'
$runPath = (Resolve-Path -LiteralPath $RunDirectory).Path
if (-not $runPath.StartsWith($artifactRoot, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $runPath -Leaf) -notmatch '^live-stack-[0-9a-f]{32}$') { throw 'Select an exact live-stack run directory under this project ml/artifacts.' }
$records = Get-Content -LiteralPath (Join-Path $runPath 'processes.json') -Raw | ConvertFrom-Json
$allowed = @('ai-security-service','discovery-server','security-monitoring-service','auth-service','adaptive-policy-engine','business-service','api-gateway')
$targets = @()
foreach ($record in $records) {
    if ($record.name -notin $allowed) { throw 'Unknown service in process manifest.' }
    $process = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
    if (-not $process) { continue }
    $command = (Get-CimInstance Win32_Process -Filter "ProcessId=$($record.pid)").CommandLine
    $sameStart = [Math]::Abs(($process.StartTime.ToUniversalTime() - ([datetime]$record.startedUtc).ToUniversalTime()).TotalMilliseconds) -le 2
    $expectedCommand = if ($record.name -eq 'ai-security-service') { '*AI-PQC-Security*ml*.venv*python*uvicorn*' } else { '*AI-PQC-Security*' + $record.name + '*SNAPSHOT.jar*' }
    if (-not $sameStart -or $command -notlike $expectedCommand) { throw "Process ownership changed for $($record.name); no targets have been stopped." }
    $targets += $process
}
foreach ($target in $targets) { Stop-Process -Id $target.Id }
Write-Output "Stopped $($targets.Count) verified processes from this run. MySQL and unrelated programs are untouched."
