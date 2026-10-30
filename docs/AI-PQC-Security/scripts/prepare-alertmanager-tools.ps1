param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$version = '0.34.1' # Official stable release verified when introduced; keep tests/deployment pinned together.
$directory = Join-Path $projectRoot "ml\artifacts\tools\alertmanager-$version"
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$name = "alertmanager-$version.windows-amd64.zip"
$base = "https://github.com/prometheus/alertmanager/releases/download/v$version"
$sums = (Invoke-WebRequest -Uri "$base/sha256sums.txt" -TimeoutSec 20).Content
if ($sums -is [byte[]]) { $sums = [Text.Encoding]::UTF8.GetString($sums) }
$line = @($sums -split "`n" | Where-Object { $_ -match "^[a-fA-F0-9]{64}\s+\*?$([regex]::Escape($name))\s*$" })
if ($line.Count -ne 1) { throw 'Missing pinned publisher checksum.' }
$expected = ($line[0] -split '\s+')[0].ToLowerInvariant()
$archive = Join-Path $directory $name
if (-not (Test-Path -LiteralPath $archive)) {
    Write-Output 'Downloading official pinned Alertmanager tools (about 40 MB).'
    Invoke-WebRequest -Uri "$base/$name" -OutFile $archive -TimeoutSec 180
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Checksum mismatch; no executable will be extracted or run.' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($archive)
try {
    foreach ($toolName in @('alertmanager.exe','amtool.exe','LICENSE','NOTICE')) {
        $entry = $zip.GetEntry("alertmanager-$version.windows-amd64/$toolName")
        if ($null -eq $entry) { throw "Missing release entry: $toolName" }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $directory $toolName), $true)
    }
} finally { $zip.Dispose() }
Write-Output "Publisher SHA-256 verified: $expected"
& (Join-Path $directory 'amtool.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'Alertmanager tool version check failed.' }
