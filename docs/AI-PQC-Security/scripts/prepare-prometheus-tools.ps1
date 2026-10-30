param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$version = '3.7.3' # Match the repository's existing Compose image, not a latest-version claim.
$directory = Join-Path $projectRoot "ml\artifacts\tools\prometheus-$version"
New-Item -ItemType Directory -Force -Path $directory | Out-Null
$name = "prometheus-$version.windows-amd64.zip"
$base = "https://github.com/prometheus/prometheus/releases/download/v$version"
$sums = (Invoke-WebRequest -Uri "$base/sha256sums.txt" -TimeoutSec 20).Content
if ($sums -is [byte[]]) { $sums = [Text.Encoding]::UTF8.GetString($sums) }
$line = @($sums -split "`n" | Where-Object { $_ -match "^[a-fA-F0-9]{64}\s+\*?$([regex]::Escape($name))\s*$" })
if ($line.Count -ne 1) { throw 'Expected one publisher checksum for the pinned Windows archive.' }
$expected = ($line[0] -split '\s+')[0].ToLowerInvariant()
$archive = Join-Path $directory $name
if (-not (Test-Path -LiteralPath $archive)) {
    Write-Output 'Downloading the official pinned Prometheus tools archive (about 136 MB).'
    Invoke-WebRequest -Uri "$base/$name" -OutFile $archive -TimeoutSec 180
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Archive checksum mismatch; no executable will be extracted or run.'
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($archive)
try {
    foreach ($toolName in @('promtool.exe', 'prometheus.exe', 'LICENSE', 'NOTICE')) {
        $entry = $zip.GetEntry("prometheus-$version.windows-amd64/$toolName")
        if ($null -eq $entry) { throw "Missing expected release entry: $toolName" }
        [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, (Join-Path $directory $toolName), $true)
    }
} finally { $zip.Dispose() }
Write-Output "Publisher SHA-256 verified: $expected"
& (Join-Path $directory 'promtool.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'Promtool version check failed.' }
