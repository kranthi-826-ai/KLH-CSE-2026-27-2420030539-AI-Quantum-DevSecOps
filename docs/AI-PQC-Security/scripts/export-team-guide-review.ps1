param([string]$ReviewName = 'word-review.pdf')
$ErrorActionPreference = 'Stop'
if ($ReviewName -notin @('word-review.pdf','word-review-v2.pdf')) { throw 'Unexpected review filename.' }
$taskRoot = Split-Path $PSScriptRoot -Parent
$source = Join-Path $taskRoot 'docs/team/AI-PQC-Security-Team-Guide.docx'
$target = Join-Path $taskRoot ('ml/artifacts/team-guide-2026-10-26/' + $ReviewName)
if (Test-Path -LiteralPath $target) { throw 'Preserve prior review export.' }
$word = $null
$document = $null
$ownsInstance = $false
try {
    $word = New-Object -ComObject Word.Application
    if ($word.Documents.Count -ne 0) { throw 'Unexpected documents in Word instance; leave them untouched.' }
    $ownsInstance = $true
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($source, $false, $true)
    $document.ExportAsFixedFormat($target, 17)
    Write-Output $target
} finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($null -ne $word) {
        if ($ownsInstance -and $word.Documents.Count -eq 0) { $word.Quit(0) }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
}
