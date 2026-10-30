$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Project Python environment is missing.' }
$mavenCommand = Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath = if ($mavenCommand) { $mavenCommand.Source } else {
    'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd'
}
if (-not (Test-Path -LiteralPath $mavenPath)) { throw 'Maven is missing; add mvn.cmd to PATH.' }
$runSuffix = [guid]::NewGuid().ToString('N').Substring(0, 12)
$outputPath = Join-Path $projectRoot "ml\artifacts\microservice-http-lab-$runSuffix.json"
$mavenArgs = @('-q', '-ntp', '-pl', 'backend/auth-service', '-am', 'test',
    '-Dtest=LabTrafficCollectionTests', '-Dsurefire.failIfNoSpecifiedTests=false',
    "-Dlab.collector.python=$pythonPath", "-Dlab.collector.root=$projectRoot",
    "-Dlab.collector.output=$outputPath")
Push-Location $projectRoot
try {
    & $mavenPath @mavenArgs
    if ($LASTEXITCODE -ne 0) { throw "Local collection failed; Maven exit code $LASTEXITCODE" }
    if (-not (Test-Path -LiteralPath $outputPath)) { throw 'Measurement artifact was not produced.' }
    Write-Host "Measured local HTTP observations saved: $outputPath"
    Write-Host 'Isolated test server stopped. No MySQL password or production account was used.'
} finally {
    Pop-Location
}
