$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Project Python environment is missing.' }
$mavenCommand = Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath = if ($mavenCommand) { $mavenCommand.Source } else {
    'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd'
}
if (-not (Test-Path -LiteralPath $mavenPath)) { throw 'Maven is missing; add mvn.cmd to PATH.' }
$runName = 'microservice-sessions-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
$dataPath = Join-Path $projectRoot "ml\data\processed\$runName"
$studyPath = Join-Path $projectRoot "ml\models\candidates\$runName"
$mavenArgs = @('-q', '-ntp', '-pl', 'backend/auth-service', '-am', 'test',
    '-Dtest=SessionTrafficCollectionTests', '-Dsurefire.failIfNoSpecifiedTests=false',
    "-Dsession.collector.python=$pythonPath", "-Dsession.collector.root=$projectRoot",
    "-Dsession.collector.output=$dataPath")
Push-Location $projectRoot
try {
    & $mavenPath @mavenArgs
    if ($LASTEXITCODE -ne 0) { throw 'Traffic collection failed. Partial evidence was preserved; no training started.' }
    & $pythonPath 'ml/training/train_microservice_sessions.py' --data $dataPath --output $studyPath
    if ($LASTEXITCODE -ne 0) { throw 'Model freeze failed. Reserved test was not evaluated.' }
    & $pythonPath 'ml/training/evaluate_microservice_sessions.py' --data $dataPath --study $studyPath
    if ($LASTEXITCODE -ne 0) { throw 'Frozen evaluation failed. Do not remove its one-shot marker to retry or tune.' }
    Write-Host "Study evidence: $studyPath"
    Write-Host 'Controlled local lab only. No model deployed and no automatic response enabled.'
} finally {
    Pop-Location
}
