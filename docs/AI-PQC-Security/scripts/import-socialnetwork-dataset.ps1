param(
    [string]$SourceDirectory = (Join-Path $env:USERPROFILE 'Downloads'),
    [string]$DestinationDirectory = (Join-Path (Split-Path $PSScriptRoot -Parent) 'ml\data\raw\microservice-ids-2024\socialnetwork')
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$expected = [ordered]@{
    'SocialNetwork-training-data.zip' = '85363b48faf0473199daf4184a8164d7'
    'SocialNetwork-validation-data.zip' = 'b3b09bf1c63a8630b71c5c286847ca95'
    'SocialNetwork-attack-data.zip' = 'd6bda4b15a56eb5a60bde69003a3cd6a'
    'README.md' = '3e4ae104333d6f6427599f5626a69cfc'
}
$sourceRoot = (Resolve-Path -LiteralPath $SourceDirectory).Path
$destinationRoot = [IO.Path]::GetFullPath($DestinationDirectory)
if ($sourceRoot.TrimEnd('\') -eq $destinationRoot.TrimEnd('\')) { throw 'Source and destination must differ' }
$pendingBytes = 0L
foreach ($name in $expected.Keys) {
    $sourceFile = Join-Path $sourceRoot $name
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) { throw "Missing source: $name" }
    if (-not (Test-Path -LiteralPath (Join-Path $destinationRoot $name))) { $pendingBytes += (Get-Item -LiteralPath $sourceFile).Length }
    Write-Output "Checking publisher checksum: $name"
    if ((Get-FileHash -LiteralPath $sourceFile -Algorithm MD5).Hash.ToLowerInvariant() -ne $expected[$name]) { throw "Publisher checksum mismatch: $name" }
}
$drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($destinationRoot))
if ($drive.AvailableFreeSpace -lt ($pendingBytes + 512MB)) { throw 'Insufficient space; no source files have been removed' }
New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
$records = @()
foreach ($name in $expected.Keys) {
    $sourceFile = Join-Path $sourceRoot $name
    $destinationFile = Join-Path $destinationRoot $name
    if (-not (Test-Path -LiteralPath $destinationFile)) {
        Write-Output "Copying without deleting original: $name"
        [IO.File]::Copy($sourceFile, $destinationFile, $false)
    }
    $sourceSHA = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
    $destinationSHA = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceSHA -ne $destinationSHA) { throw "Copied file mismatch; preserve both files for investigation: $name" }
    $records += [ordered]@{ name=$name; bytes=(Get-Item -LiteralPath $destinationFile).Length; publisher_md5=$expected[$name]; sha256=$destinationSHA }
    Write-Output "Verified identical: $name"
}
$artifactDirectory = Join-Path $projectRoot 'ml\artifacts'
New-Item -ItemType Directory -Path $artifactDirectory -Force | Out-Null
$outputPath = Join-Path $artifactDirectory ('socialnetwork-import-' + [guid]::NewGuid().ToString('N') + '.json')
$manifest = [ordered]@{ schema='socialnetwork-project-import-v1'; created_utc=[DateTime]::UtcNow.ToString('o'); source=$sourceRoot; destination=$destinationRoot; originals_preserved=$true; extracted=$false; files=$records }
$stream = [IO.File]::Open($outputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($manifest | ConvertTo-Json -Depth 6))
    $stream.Write($bytes, 0, $bytes.Length)
} finally { $stream.Dispose() }
Write-Output "Import complete. Audit manifest: $outputPath"
