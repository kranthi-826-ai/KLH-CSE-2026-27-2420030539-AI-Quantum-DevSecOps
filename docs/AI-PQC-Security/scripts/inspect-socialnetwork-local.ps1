param([string]$OutputManifest)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot 'ml\.venv\Scripts\python.exe'
$entry = Join-Path $projectRoot 'ml\data\inspect_socialnetwork_local.py'
if ($OutputManifest) { & $python $entry --output $OutputManifest }
else { & $python $entry }
if ($LASTEXITCODE -ne 0) { throw 'Project-local dataset inspection failed; evidence was not overwritten' }
