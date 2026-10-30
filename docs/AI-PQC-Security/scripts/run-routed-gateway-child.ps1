param([Parameter(Mandatory)][string]$AuthUrl, [Parameter(Mandatory)][string]$OutputRoot,
      [Parameter(Mandatory)][string]$PythonPath, [switch]$ControlsOnly, [switch]$Rich)
$ErrorActionPreference = 'Stop'
if ($AuthUrl -notmatch '^http://127\.0\.0\.1:[0-9]+$') { throw 'Only the isolated loopback Auth Service is supported.' }
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$mavenCommand = Get-Command mvn.cmd -ErrorAction SilentlyContinue
$mavenPath = if ($mavenCommand) { $mavenCommand.Source } else { 'C:\Program Files\Apache\Maven\apache-maven-3.9.16\bin\mvn.cmd' }
Push-Location $projectRoot
try {
    $testSelector = if ($ControlsOnly) { '-Dtest=GatewayRoutedControlTests' } else { '-Dtest=GatewayToAuthLabTests' }
    & $mavenPath -q -ntp -f 'backend/api-gateway/pom.xml' test $testSelector `
        "-Drouted.auth.url=$AuthUrl" "-Drouted.root=$projectRoot" "-Drouted.output=$OutputRoot" "-Drouted.python=$PythonPath" "-Drouted.rich=$($Rich.IsPresent.ToString().ToLowerInvariant())"
    if ($LASTEXITCODE -ne 0) { throw 'Real Gateway-to-Auth collection failed.' }
} finally { Pop-Location }
