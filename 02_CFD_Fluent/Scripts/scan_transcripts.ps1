$mq = '<PROJECT_ROOT>\05_Meshing\Mesh_Quality'
foreach ($lv in @('coarse','medium','fine')) {
    $f = Join-Path $mq ($lv + '_fluent_check.txt')
    Write-Output ('##### ' + $lv + ' #####')
    $hits = Select-String -Path $f -Pattern 'warning|wrong node|error|fail|limit|exceed|student|not supported|negative' -AllMatches
    if ($hits) { $hits | ForEach-Object { Write-Output ('  ' + $_.LineNumber + ': ' + $_.Line.Trim()) } }
    else { Write-Output '  (no warning/error/limit lines)' }
}
