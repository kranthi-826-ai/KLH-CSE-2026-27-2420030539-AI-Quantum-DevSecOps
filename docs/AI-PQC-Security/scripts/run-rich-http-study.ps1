$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath=Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
$pwshPath=(Get-Command pwsh -ErrorAction Stop).Source
$mavenCommand=Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath=if($mavenCommand){$mavenCommand.Source}else{'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd'}
$reference=Join-Path $projectRoot 'ml\models\candidates\microservice-sessions-routed-v1'
if(-not(Test-Path -LiteralPath (Join-Path $reference 'frozen.json'))){throw 'Frozen peer-study reference is required.'}
$suffix=[guid]::NewGuid().ToString('N').Substring(0,12)
$capture=Join-Path $projectRoot "ml\data\processed\rich-capture-$suffix"
$prepared=Join-Path $projectRoot "ml\data\processed\rich-prepared-$suffix"
$study=Join-Path $projectRoot "ml\models\candidates\microservice-sessions-rich-$suffix"
Push-Location $projectRoot
try {
    & $mavenPath -q -ntp -pl 'backend/auth-service' -am test '-Dtest=RoutedSessionCollectionTests' `
        '-Dsurefire.failIfNoSpecifiedTests=false' '-Drouted.rich=true' "-Drouted.collector.python=$pythonPath" `
        "-Drouted.collector.root=$projectRoot" "-Drouted.collector.output=$capture" "-Drouted.collector.pwsh=$pwshPath"
    if($LASTEXITCODE -ne 0){throw 'Rich collection failed; no training started.'}
    & $pythonPath 'ml/data/prepare_routed_sessions.py' --source $capture --output $prepared --rich
    if($LASTEXITCODE -ne 0){throw 'Rich gateway/label join failed.'}
    & $pythonPath 'ml/training/study_rich_http.py' train --data $prepared --output $study --reference $reference
    if($LASTEXITCODE -ne 0){throw 'Freeze failed; final test not evaluated.'}
    & $pythonPath 'ml/training/study_rich_http.py' evaluate --data $prepared --output $study --reference $reference
    if($LASTEXITCODE -ne 0){throw 'One-shot evaluation failed; preserve its marker and do not retune.'}
    Write-Host "Completed controlled rich-context study: $study"
    Write-Host 'No promotion or automatic AI blocking; interpret strict quality gates and limitations.'
} finally {Pop-Location}
