param(
    [string]$OutputFile = "ml/artifacts/crypto-benchmark.json"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$benchmarkJar = Join-Path $repositoryRoot "platform/crypto-agility/benchmarks/target/crypto-benchmarks.jar"
$resultPath = Join-Path $repositoryRoot $OutputFile

if (-not (Test-Path -LiteralPath $benchmarkJar)) {
    throw "Benchmark JAR not found. Run Maven package from the repository root first."
}

$resultDirectory = Split-Path -Parent $resultPath
New-Item -ItemType Directory -Force -Path $resultDirectory | Out-Null

& java -jar $benchmarkJar `
    -wi 2 -i 3 -f 1 -w 1s -r 1s `
    -rf json -rff $resultPath

if ($LASTEXITCODE -ne 0) {
    throw "JMH benchmark failed with exit code $LASTEXITCODE."
}

Write-Host "Benchmark results written to $resultPath"
