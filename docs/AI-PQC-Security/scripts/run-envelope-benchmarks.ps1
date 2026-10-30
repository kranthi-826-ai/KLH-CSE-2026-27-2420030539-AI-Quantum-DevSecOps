param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$jar = Join-Path $projectRoot 'platform/crypto-agility/benchmarks/target/crypto-benchmarks.jar'
if (-not (Test-Path -LiteralPath $jar)) { throw 'Build the benchmark reactor before this run.' }
$java = (Get-Command java.exe -ErrorAction Stop).Source
$folder = Join-Path $projectRoot ('ml/artifacts/envelope-benchmark-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $folder | Out-Null
$result = Join-Path $folder 'jmh.json'
$process = $null
$started = [DateTime]::UtcNow
$receipt = [ordered]@{
    schema='matched-envelope-jmh-v1'; passed=$false; payloadBytes=4096; threads=1; forks=5
    warmupIterations=5; measurementIterations=10; iterationSeconds=1
    maximumRunSeconds=600; heapMiB=512; profiler='gc'; modeOrder='JMH parameter order, not randomized'
    scope='Fresh-provider/keygen/seal/open/equality/wipe; no AI, policy, HTTP, persistence or end-to-end latency'
    javaExecutable=$java; jarSha256=(Get-FileHash -LiteralPath $jar -Algorithm SHA256).Hash.ToLowerInvariant()
    revision=(& git -C $projectRoot rev-parse HEAD).Trim(); startedUtc=$started.ToString('o')
    powerThermalConditions='Not externally controlled; no temperature measurement or CPU affinity'
}
try {
    $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
    $os=Get-CimInstance Win32_OperatingSystem
    $receipt.cpu=[ordered]@{name=$cpu.Name; logicalProcessors=$cpu.NumberOfLogicalProcessors; loadPercentBefore=$cpu.LoadPercentage}
    $receipt.memoryKiB=[ordered]@{total=$os.TotalVisibleMemorySize; freeBefore=$os.FreePhysicalMemory}
    $arguments=@('-jar',('"'+$jar+'"'),'EnvelopeBenchmark.freshKeyRoundTrip','-wi','5','-i','10','-f','5','-t','1','-w','1s','-r','1s',
        '-jvmArgs','"-Xms256m -Xmx512m"','-prof','gc','-foe','true','-rf','json','-rff',('"'+$result+'"'))
    $process=Start-Process -FilePath $java -ArgumentList $arguments -WindowStyle Hidden -PassThru -WorkingDirectory $projectRoot `
        -RedirectStandardOutput (Join-Path $folder 'jmh.out.log') -RedirectStandardError (Join-Path $folder 'jmh.err.log')
    Write-Output "Matched envelope benchmark started. Evidence: $folder"
    $lastUpdate=[DateTime]::UtcNow
    while (-not $process.WaitForExit(1000)) {
        if (([DateTime]::UtcNow-$started).TotalSeconds -gt 600) { throw 'Bounded benchmark deadline exceeded.' }
        if (([DateTime]::UtcNow-$lastUpdate).TotalSeconds -ge 30) {
            Write-Output ('Owned benchmark still running; elapsed seconds: '+[int]([DateTime]::UtcNow-$started).TotalSeconds)
            $lastUpdate=[DateTime]::UtcNow
        }
    }
    if ($process.ExitCode -ne 0) { throw 'JMH failed; retain logs and do not report a passing benchmark.' }
    $data=Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
    if (@($data).Count -ne 3) { throw 'Expected exactly three matched profile results.' }
    foreach ($entry in $data) {
        if ($entry.forks -ne 5 -or $entry.measurementIterations -ne 10 -or $entry.threads -ne 1 -or
            $entry.primaryMetric.scoreUnit -ne 'ms/op' -or @($entry.primaryMetric.rawData).Count -ne 5) {
            throw 'Recorded protocol differs from frozen requirements.'
        }
    }
    & $java -cp $jar com.pqc.security.crypto.benchmark.EnvelopeBenchmark > (Join-Path $folder 'sizes.json')
    if ($LASTEXITCODE -ne 0) { throw 'Size/round-trip report failed.' }
    $sizes=Get-Content -LiteralPath (Join-Path $folder 'sizes.json') -Raw | ConvertFrom-Json
    if (@($sizes.modes).Count -ne 3) { throw 'Incomplete size report.' }
    $receipt.resultSha256=(Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash.ToLowerInvariant()
    $receipt.sizesSha256=(Get-FileHash -LiteralPath (Join-Path $folder 'sizes.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    $receipt.passed=$true
} catch {
    $receipt.error=$_.Exception.Message
    throw
} finally {
    if ($process -and -not $process.HasExited) { $process.Kill($true); $process.WaitForExit(5000) | Out-Null }
    $receipt.ownedProcessStopped=($null -eq $process -or $process.HasExited)
    $receipt.seconds=[Math]::Round(([DateTime]::UtcNow-$started).TotalSeconds,2)
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $folder 'verification.json') -Encoding utf8
}
Write-Output "Matched benchmark completed; owned JVMs stopped. Evidence: $folder"
