param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$tool = Join-Path $projectRoot 'ml\artifacts\tools\prometheus-3.7.3\promtool.exe'
if (-not (Test-Path -LiteralPath $tool)) { throw 'Run scripts/prepare-prometheus-tools.ps1 first.' }
$runDirectory = Join-Path $projectRoot ('ml\artifacts\monitoring-rules-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDirectory | Out-Null
$evidence = [ordered]@{schema='monitoring-rules-verification-v1'; passed=$false; files=@(); external_notification_tested=$false}
try {
    $relativeFiles = @('infrastructure/monitoring/prometheus.yml','infrastructure/monitoring/prometheus-local.yml',
                      'infrastructure/monitoring/audit-alerts.yml','infrastructure/monitoring/audit-alerts.test.yml')
    foreach ($relative in $relativeFiles) {
        $evidence.files += @{path=$relative; sha256=(Get-FileHash -LiteralPath (Join-Path $projectRoot $relative) -Algorithm SHA256).Hash.ToLowerInvariant()}
    }
    & $tool --version *> (Join-Path $runDirectory 'version.log')
    if ($LASTEXITCODE -ne 0) { throw 'Promtool version check failed.' }
    & $tool check config (Join-Path $projectRoot $relativeFiles[0]) (Join-Path $projectRoot $relativeFiles[1]) *> (Join-Path $runDirectory 'config-check.log')
    if ($LASTEXITCODE -ne 0) { throw 'Monitoring configuration validation failed; retain evidence.' }
    & $tool test rules (Join-Path $projectRoot 'infrastructure/monitoring/audit-alerts.test.yml') *> (Join-Path $runDirectory 'rule-tests.log')
    if ($LASTEXITCODE -ne 0) { throw 'Monitoring rule tests failed; retain evidence.' }
    $evidence.passed = $true
    Write-Output "Both configurations and all alert rule scenarios passed. Evidence: $runDirectory"
} finally {
    $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDirectory 'verification.json')
}
