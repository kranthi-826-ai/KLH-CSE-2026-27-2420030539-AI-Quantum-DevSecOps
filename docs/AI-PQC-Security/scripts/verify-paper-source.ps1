param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$paperPath = Join-Path $projectRoot 'docs/research/paper/main.tex'
$paperSource = [IO.File]::ReadAllText($paperPath)
$outputDirectory = Join-Path $projectRoot ('ml/artifacts/paper-preflight-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $outputDirectory | Out-Null
$checks = [Collections.Generic.List[string]]::new()
foreach ($section in @('Introduction','Related Work','Methodology','Results','Discussion','Conclusion')) {
    if (-not $paperSource.Contains('\section{' + $section + '}')) { throw "Missing required paper section: $section" }
    $checks.Add("section:$section")
}
$abstract = [regex]::Match($paperSource, '(?s)\\begin\{abstract\}(.*?)\\end\{abstract\}').Groups[1].Value
$words = [regex]::Matches($abstract, '\S+').Count
if ($words -lt 150 -or $words -gt 250) { throw "Abstract length outside teacher range: $words" }
if ($abstract -match '\\cite') { throw 'Teacher template requires no citations in abstract.' }
$checks.Add('abstract:150-250-words-no-citations')
$keys = @([regex]::Matches($paperSource, '\\bibitem\{([^}]+)\}') | ForEach-Object { $_.Groups[1].Value })
if (($keys | Select-Object -Unique).Count -ne $keys.Count) { throw 'Duplicate bibliography keys.' }
$usedKeys = @([regex]::Matches($paperSource, '\\cite\{([^}]+)\}') | ForEach-Object { $_.Groups[1].Value.Split(',') })
foreach ($key in $usedKeys) { if ($key.Trim() -notin $keys) { throw "Undefined citation key: $key" } }
$checks.Add('citation-keys:defined-and-unique')
foreach ($key in $keys) {
    if ($key -notin $usedKeys) { throw "Bibliography entry is never cited: $key" }
}
$firstAppearance = @($usedKeys | ForEach-Object { $_.Trim() } | Select-Object -Unique)
if (($firstAppearance -join ',') -ne ($keys -join ',')) { throw 'Bibliography order differs from first in-text citation order.' }
$checks.Add('bibliography:all-entries-cited-in-first-appearance-order')
$retainedPaperKeys = @('adaptive','sage','flora','session','devsecops','gateway','kem','enterprise','feature','xai','readiness')
foreach ($key in $retainedPaperKeys) {
    if ($key -notin $usedKeys) { throw "Retained source not cited: $key" }
}
$checks.Add('retained-library:all-eleven-cited')
$labels = @([regex]::Matches($paperSource, '\\label\{([^}]+)\}') | ForEach-Object { $_.Groups[1].Value })
if (($labels | Select-Object -Unique).Count -ne $labels.Count) { throw 'Duplicate figure/table/equation labels.' }
foreach ($match in [regex]::Matches($paperSource, '\\ref\{([^}]+)\}')) {
    if ($match.Groups[1].Value -notin $labels) { throw "Undefined cross-reference: $($match.Groups[1].Value)" }
}
$checks.Add('cross-reference-labels:defined-and-unique')
$tableCount = [regex]::Matches($paperSource, '\\begin\{table\*?\}').Count
$figureCount = [regex]::Matches($paperSource, '\\begin\{figure\*?\}').Count
# Independently recompute accuracy from the recorded confusion matrices.
$matrices = @(@('UNSW RF',29657,7343,1064,44268,89.79),
              @('CIC RF',11474,526,5742,36810,88.510),
              @('CIC XGB',10421,1579,3660,38892,90.396))
foreach ($matrix in $matrices) {
    $accuracy = 100.0 * ($matrix[1] + $matrix[4]) / ($matrix[1] + $matrix[2] + $matrix[3] + $matrix[4])
    if ([Math]::Abs($accuracy - $matrix[5]) -gt 0.0051) { throw "Recorded accuracy inconsistent with confusion matrix: $($matrix[0])" }
    $checks.Add("arithmetic:$($matrix[0])")
}
$receipt = [ordered]@{schema='paper-source-preflight-v1';source_sha256=(Get-FileHash $paperPath).Hash.ToLowerInvariant();
    passed=$true;abstract_words=$words;reference_count=$keys.Count;checks=@($checks);
    table_count=$tableCount;figure_count=$figureCount;retained_papers_cited=$retainedPaperKeys.Count;
    author_details_pending=$paperSource.Contains('Author details pending confirmation');
    visual_review_complete=$false;plagiarism_checked=$false;submission_ready=$false;
    limitations=@('Source checks only, not compilation or layout verification.',
        'Arithmetic uses explicit recorded matrices; no dataset/model rerun.',
        'Defined citation keys do not establish source accuracy or full literature coverage.')}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputDirectory 'verification.json')
Write-Output "Paper source preflight passed; abstract $words words, $($keys.Count) references. Not submission-ready. Evidence: $outputDirectory"
