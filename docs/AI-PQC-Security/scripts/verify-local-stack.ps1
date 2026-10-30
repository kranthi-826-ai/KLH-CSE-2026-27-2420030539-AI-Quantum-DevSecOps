param([switch]$KeepRunning, [switch]$VerifyOutage, [switch]$VerifyBot, [switch]$VerifyReplay, [switch]$VerifyAlertEngine, [switch]$VerifyPolicyMatrix, [switch]$VerifyDependencyFailures, [switch]$VerifyConcurrent, [switch]$VerifyAuditAlerts)
$ErrorActionPreference = 'Stop'
if ($VerifyReplay -and -not $VerifyOutage) { throw 'VerifyReplay requires VerifyOutage for its isolated synthetic event.' }
$projectRoot = Split-Path $PSScriptRoot -Parent
$envPath = Join-Path $projectRoot '.env'
if (-not (Test-Path -LiteralPath $envPath)) { throw 'Create the Git-ignored root .env with DB_PASSWORD first.' }
$settings = @{}
foreach ($line in [IO.File]::ReadAllLines($envPath)) {
    if ($line -match '^\s*(DB_PASSWORD|JWT_SECRET|MONITORING_API_KEY)\s*=(.*)$') {
        $key, $value = $matches[1], $matches[2].Trim()
        if ($settings.ContainsKey($key)) { throw "Duplicate configuration key: $key" }
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) { $value = $value.Substring(1, $value.Length - 2) }
        $settings[$key] = $value
    }
}
if ([string]::IsNullOrWhiteSpace($settings['DB_PASSWORD'])) { throw 'DB_PASSWORD is missing or empty; its value will not be printed.' }
foreach ($key in @('JWT_SECRET','MONITORING_API_KEY')) {
    if ([string]::IsNullOrWhiteSpace($settings[$key])) { $settings[$key] = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48)) }
}
$ports = @(8761,8080,8081,8082,8083,8090,8091)
if (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -in $ports) { throw 'A project port is occupied. Refusing to replace or stop an existing service.' }
$python = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
$java = (Get-Command java.exe -ErrorAction Stop).Source
$runDirectory = Join-Path $projectRoot ('ml\artifacts\live-stack-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDirectory | Out-Null
$started = [Collections.Generic.List[object]]::new()
$oldEnvironment = @{}
$verified = $false
$variables = @('DB_PASSWORD','JWT_SECRET','MONITORING_API_KEY','SERVER_ADDRESS','EUREKA_INSTANCE_IP_ADDRESS','PYTHONPATH','AI_MODEL_PATH','PROMETHEUS_URL')
foreach ($key in $variables) { $oldEnvironment[$key] = [Environment]::GetEnvironmentVariable($key) }
try {
    foreach ($key in $settings.Keys) { [Environment]::SetEnvironmentVariable($key, $settings[$key]) }
    $env:SERVER_ADDRESS = '127.0.0.1'
    if ($VerifyAlertEngine -or $VerifyAuditAlerts) { $env:PROMETHEUS_URL = 'http://127.0.0.1:19090' }
    $env:EUREKA_INSTANCE_IP_ADDRESS = '127.0.0.1'
    $env:PYTHONPATH = Join-Path $projectRoot 'platform\ai-security-service'
    $env:AI_MODEL_PATH = Join-Path $projectRoot 'ml\models\promoted\model.joblib'
    $ai = Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8090') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory 'ai.out.log') -RedirectStandardError (Join-Path $runDirectory 'ai.err.log') -PassThru
    $started.Add([pscustomobject]@{name='ai-security-service'; process=$ai})
    foreach ($entry in @(
        @('discovery-server','backend/discovery-server/target/discovery-server-0.0.1-SNAPSHOT.jar'),
        @('security-monitoring-service','backend/security-monitoring-service/target/security-monitoring-service-0.0.1-SNAPSHOT.jar'),
        @('auth-service','backend/auth-service/target/auth-service-0.0.1-SNAPSHOT.jar'),
        @('adaptive-policy-engine','platform/adaptive-policy-engine/target/adaptive-policy-engine-0.1.0-SNAPSHOT.jar'),
        @('business-service','backend/business-service/target/business-service-0.0.1-SNAPSHOT.jar'),
        @('api-gateway','backend/api-gateway/target/api-gateway-0.0.1-SNAPSHOT.jar')
    )) {
        $name, $relativeJar = $entry
        $jar = Join-Path $projectRoot $relativeJar
        if (-not (Test-Path -LiteralPath $jar)) { throw "Build the current JAR first: $relativeJar" }
        $child = Start-Process -FilePath $java -ArgumentList @('-Xms64m','-Xmx512m','-jar',('"' + $jar + '"')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory "$name.out.log") -RedirectStandardError (Join-Path $runDirectory "$name.err.log") -PassThru
        $started.Add([pscustomobject]@{name=$name; process=$child})
    }
    $started | ForEach-Object { [pscustomobject]@{name=$_.name; pid=$_.process.Id; startedUtc=$_.process.StartTime.ToUniversalTime().ToString('o')} } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'processes.json')
    Write-Output "Started isolated loopback services. Evidence: $runDirectory"
    $deadline = [DateTime]::UtcNow.AddSeconds(150)
    $pending = @(8761,8080,8081,8082,8083,8091,8090)
    while ($pending.Count -gt 0 -and [DateTime]::UtcNow -lt $deadline) {
        foreach ($item in $started) { if ($item.process.HasExited) { throw "Service exited: $($item.name); inspect its local log, no credentials are printed." } }
        $pending = @($pending | Where-Object {
            $healthPath = if ($_ -eq 8090) { '/health' } else { '/actuator/health' }
            try { $health = Invoke-RestMethod "http://127.0.0.1:$_$healthPath" -TimeoutSec 2; $health.status -ne 'UP' } catch { $true }
        })
        if ($pending.Count) { Start-Sleep -Seconds 2 }
    }
    if ($pending.Count) { throw "Readiness deadline exceeded for ports: $pending" }
    $aiHealth = Invoke-RestMethod 'http://127.0.0.1:8090/health' -TimeoutSec 3
    if ($aiHealth.status -ne 'UP') { throw 'The promoted model did not load; no mock inference is allowed.' }
    & $python (Join-Path $projectRoot 'tests\live\verify_stack.py') --output (Join-Path $runDirectory 'verification.json')
    if ($LASTEXITCODE -ne 0) { throw 'Live API/database checks failed. Preserve local evidence.' }
    if ($VerifyConcurrent) {
        & $python (Join-Path $projectRoot 'tests\live\verify_concurrent_adaptive.py') --output (Join-Path $runDirectory 'concurrent-adaptive.json')
        if ($LASTEXITCODE -ne 0) { throw 'Bounded concurrent adaptive verification failed; preserve evidence.' }
    }
    if ($VerifyPolicyMatrix) {
        & $python (Join-Path $projectRoot 'tests\live\verify_adaptive_matrix.py') --output (Join-Path $runDirectory 'adaptive-matrix.json')
        if ($LASTEXITCODE -ne 0) { throw 'Frozen adaptive scenario verification failed; preserve evidence.' }
    }
    if ($VerifyBot) {
        & $python (Join-Path $projectRoot 'tests\live\verify_gateway_burst.py') --output (Join-Path $runDirectory 'gateway-burst-verification.json')
        if ($LASTEXITCODE -ne 0) { throw 'Bounded gateway burst verification failed; preserve evidence.' }
    }
    if ($VerifyDependencyFailures) {
        $transitions=[Collections.Generic.List[object]]::new()
        function Stop-OwnedDependency([string]$Name,[int]$Port) {
            $owned=@($started | Where-Object name -eq $Name)
            if ($owned.Count -ne 1) { throw 'Expected exactly one owned dependency process.' }
            $oldPid=$owned[0].process.Id
            if (-not $owned[0].process.HasExited) { $owned[0].process.Kill($true); $owned[0].process.WaitForExit(10000) | Out-Null }
            if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { throw 'Dependency port remains occupied; refusing to stop any other process.' }
            $transitions.Add(@{service=$Name;action='stopped-owned-tree';pid=$oldPid;utc=[DateTime]::UtcNow.ToString('o')})
        }
        function Wait-OwnedDependency([string]$Name,[int]$Port,[string]$Path) {
            $owned=$started | Where-Object name -eq $Name
            $deadline=[DateTime]::UtcNow.AddSeconds(80)
            while ([DateTime]::UtcNow -lt $deadline) {
                if ($owned.process.HasExited) { throw 'Restarted dependency exited; preserve local logs.' }
                try { if ((Invoke-RestMethod "http://127.0.0.1:$Port$Path" -TimeoutSec 2).status -eq 'UP') { return } } catch { }
                Start-Sleep -Seconds 1
            }
            throw 'Owned dependency restart readiness deadline exceeded.'
        }
        Stop-OwnedDependency 'ai-security-service' 8090
        & $python (Join-Path $projectRoot 'tests/live/verify_dependency_failure.py') ai-down $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'AI outage fail-closed probe failed.' }
        $ownedAi=$started | Where-Object name -eq 'ai-security-service'
        $ownedAi.process=Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8090') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory 'ai.dependency-restart.out.log') -RedirectStandardError (Join-Path $runDirectory 'ai.dependency-restart.err.log') -PassThru
        $transitions.Add(@{service='ai-security-service';action='restarted-owned';pid=$ownedAi.process.Id;utc=[DateTime]::UtcNow.ToString('o')})
        Wait-OwnedDependency 'ai-security-service' 8090 '/health'
        & $python (Join-Path $projectRoot 'tests/live/verify_dependency_failure.py') ai-recovered $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'AI recovery probe failed.' }
        Stop-OwnedDependency 'adaptive-policy-engine' 8091
        & $python (Join-Path $projectRoot 'tests/live/verify_dependency_failure.py') policy-down $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Policy outage fail-closed probe failed.' }
        $ownedPolicy=$started | Where-Object name -eq 'adaptive-policy-engine'
        $policyJar=Join-Path $projectRoot 'platform/adaptive-policy-engine/target/adaptive-policy-engine-0.1.0-SNAPSHOT.jar'
        $ownedPolicy.process=Start-Process -FilePath $java -ArgumentList @('-Xms64m','-Xmx512m','-jar',('"'+$policyJar+'"')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory 'policy.dependency-restart.out.log') -RedirectStandardError (Join-Path $runDirectory 'policy.dependency-restart.err.log') -PassThru
        $transitions.Add(@{service='adaptive-policy-engine';action='restarted-owned';pid=$ownedPolicy.process.Id;utc=[DateTime]::UtcNow.ToString('o')})
        Wait-OwnedDependency 'adaptive-policy-engine' 8091 '/actuator/health'
        & $python (Join-Path $projectRoot 'tests/live/verify_dependency_failure.py') policy-recovered $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Policy recovery probe failed.' }
        $transitions | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $runDirectory 'dependency-process-transitions.json')
    }
    if ($VerifyOutage) {
        function Restart-RunService([string]$Name, [string]$RelativeJar) {
            $item = $started | Where-Object name -eq $Name
            if (-not $item.process.HasExited) { $item.process.Kill(); $item.process.WaitForExit(10000) | Out-Null }
            $jarPath = Join-Path $projectRoot $RelativeJar
            $item.process = Start-Process -FilePath $java -ArgumentList @('-Xms64m','-Xmx512m','-jar',('"' + $jarPath + '"')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory "$Name.restart.out.log") -RedirectStandardError (Join-Path $runDirectory "$Name.restart.err.log") -PassThru
            $started | ForEach-Object { [pscustomobject]@{name=$_.name; pid=$_.process.Id; startedUtc=$_.process.StartTime.ToUniversalTime().ToString('o')} } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'processes.json')
            $port = if ($Name -eq 'auth-service') { 8081 } else { 8083 }
            $ready = $false
            $limit = [DateTime]::UtcNow.AddSeconds(80)
            while ([DateTime]::UtcNow -lt $limit) {
                if ($item.process.HasExited) { throw "Restart failed for $Name" }
                try { $health = Invoke-RestMethod "http://127.0.0.1:$port/actuator/health" -TimeoutSec 2; if ($health.status -eq 'UP') { $ready = $true; break } } catch { }
                Start-Sleep -Seconds 2
            }
            if (-not $ready) { throw "Restart readiness deadline: $Name" }
        }
        $monitoring = $started | Where-Object name -eq 'security-monitoring-service'
        $monitoring.process.Kill(); $monitoring.process.WaitForExit(10000) | Out-Null
        & $python (Join-Path $projectRoot 'tests\live\verify_outbox_recovery.py') prepare $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Outage enqueue verification failed.' }
        Restart-RunService 'auth-service' 'backend/auth-service/target/auth-service-0.0.1-SNAPSHOT.jar'
        & $python (Join-Path $projectRoot 'tests\live\verify_outbox_recovery.py') check-pending $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Producer restart durability verification failed.' }
        if ($VerifyReplay) {
            & $python (Join-Path $projectRoot 'tests\live\verify_outbox_recovery.py') replay $runDirectory
            if ($LASTEXITCODE -ne 0) { throw 'Controlled replay verification failed.' }
        }
        Restart-RunService 'security-monitoring-service' 'backend/security-monitoring-service/target/security-monitoring-service-0.0.1-SNAPSHOT.jar'
        & $python (Join-Path $projectRoot 'tests\live\verify_outbox_recovery.py') verify $runDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Audit recovery/idempotency verification failed.' }
    }
    if ($VerifyAlertEngine) {
        $engineDirectory = Join-Path $projectRoot ('ml\artifacts\alerts-' + [guid]::NewGuid().ToString('N'))
        & $python (Join-Path $projectRoot 'tests\live\verify_alert_engine.py') --output-directory $engineDirectory --verify-monitoring-api
        if ($LASTEXITCODE -ne 0) { throw 'Real alert engine through Monitoring API verification failed.' }
        @{engineEvidence=$engineDirectory} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'alert-engine-location.json')
    }
    if ($VerifyAuditAlerts) {
        $auditEngineDirectory = Join-Path $projectRoot ('ml\artifacts\adaptive-audit-alerts-' + [guid]::NewGuid().ToString('N'))
        & $python (Join-Path $projectRoot 'tests\live\verify_alert_engine.py') --output-directory $auditEngineDirectory --verify-monitoring-api --audit-write-failure
        if ($LASTEXITCODE -ne 0) { throw 'Adaptive audit alert through Monitoring API verification failed.' }
        @{engineEvidence=$auditEngineDirectory} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'adaptive-audit-alert-location.json')
    }
    $verified = $true
    Write-Output "Live checks passed: $(Join-Path $runDirectory 'verification.json')"
} finally {
    if (-not $KeepRunning -or -not $verified) {
        foreach ($item in $started) { if (-not $item.process.HasExited) { $item.process.Kill($true); $item.process.WaitForExit(10000) | Out-Null } }
        Write-Output 'Stopped only the service processes started by this run. MySQL and unrelated applications remain running.'
    }
    @{cleanupRequested=(-not $KeepRunning -or -not $verified); verificationReachedEnd=$verified;
      processes=@($started | ForEach-Object { @{service=$_.name;pid=$_.process.Id;stopped=$_.process.HasExited} })} |
        ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDirectory 'cleanup.json')
    foreach ($key in $variables) { [Environment]::SetEnvironmentVariable($key, $oldEnvironment[$key]) }
}
