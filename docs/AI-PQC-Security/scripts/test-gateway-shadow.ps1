param([string]$ModelStudyPath)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
if (-not $ModelStudyPath) { $ModelStudyPath = Join-Path $projectRoot 'ml\models\candidates\microservice-sessions-v1' }
$ModelStudyPath = (Resolve-Path -LiteralPath $ModelStudyPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $ModelStudyPath 'frozen.json'))) { throw 'Frozen lab study is missing.' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Project Python environment is missing.' }
$mavenCommand = Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath = if ($mavenCommand) { $mavenCommand.Source } else {
    'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd'
}
if (-not (Test-Path -LiteralPath $mavenPath)) { throw 'Maven is missing; add mvn.cmd to PATH.' }
$runSuffix = [guid]::NewGuid().ToString('N').Substring(0, 12)
$sourcePath = Join-Path $projectRoot "ml\artifacts\gateway-shadow-$runSuffix.jsonl"
$resultPath = Join-Path $projectRoot "ml\artifacts\gateway-shadow-$runSuffix-assessments.json"
Push-Location $projectRoot
try {
    & $mavenPath -q -ntp -f 'backend/api-gateway/pom.xml' test '-Dtest=GatewayShadowHttpTests' "-Dshadow.test.output=$sourcePath"
    if ($LASTEXITCODE -ne 0) { throw 'Gateway HTTP shadow test failed; preserved partial evidence, no scoring attempted.' }
    & $pythonPath 'ml/training/score_gateway_shadow.py' --source $sourcePath --study $ModelStudyPath --output $resultPath
    if ($LASTEXITCODE -ne 0) { throw 'Passive scoring failed; no traffic decisions were changed.' }
    Write-Host "Passive test assessments: $resultPath"
    Write-Host 'Test-only downstream handlers; no production accuracy or live authentication integration claim.'
} finally {
    Pop-Location
}
