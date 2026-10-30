$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
$pwshPath = (Get-Command pwsh -ErrorAction Stop).Source
$mavenCommand = Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath = if ($mavenCommand) { $mavenCommand.Source } else { 'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd' }
$reference = Join-Path $projectRoot 'ml\models\candidates\microservice-sessions-v1'
if (-not (Test-Path -LiteralPath (Join-Path $reference 'frozen.json'))) { throw 'Prior frozen per-account study is required.' }
$suffix = [guid]::NewGuid().ToString('N').Substring(0,12)
$dataRoot = Join-Path $projectRoot "ml\data\processed\routed-study-$suffix"
$capture = Join-Path $dataRoot 'capture'
$controls = Join-Path $dataRoot 'controls'
$prepared = Join-Path $dataRoot 'prepared'
$study = Join-Path $projectRoot "ml\models\candidates\microservice-sessions-routed-$suffix"
$commonArgs = @('-q','-ntp','-pl','backend/auth-service','-am','test','-Dtest=RoutedSessionCollectionTests',
    '-Dsurefire.failIfNoSpecifiedTests=false',"-Drouted.collector.python=$pythonPath",
    "-Drouted.collector.root=$projectRoot","-Drouted.collector.pwsh=$pwshPath")
Push-Location $projectRoot
try {
    & $mavenPath @commonArgs "-Drouted.collector.output=$capture"
    if ($LASTEXITCODE -ne 0) { throw 'Routed collection failed; no training started.' }
    & $mavenPath @commonArgs "-Drouted.collector.output=$controls" '-Drouted.controls-only=true'
    if ($LASTEXITCODE -ne 0) { throw 'Concurrent authentication/rate controls failed; no training started.' }
    & $pythonPath 'ml/data/prepare_routed_sessions.py' --source $capture --output $prepared
    if ($LASTEXITCODE -ne 0) { throw 'Gateway/label join validation failed.' }
    & $pythonPath 'ml/training/study_routed_sessions.py' train --data $prepared --output $study --reference $reference
    if ($LASTEXITCODE -ne 0) { throw 'Training/freeze failed; reserved test not evaluated.' }
    & $pythonPath 'ml/training/study_routed_sessions.py' evaluate --data $prepared --output $study --reference $reference
    if ($LASTEXITCODE -ne 0) { throw 'One-shot evaluation failed. Preserve the marker; do not remove it to retune.' }
    Write-Host "Routed lab study completed: $study"
    Write-Host 'No model promoted. No automatic AI response enabled. Outcomes may be negative.'
} finally { Pop-Location }
