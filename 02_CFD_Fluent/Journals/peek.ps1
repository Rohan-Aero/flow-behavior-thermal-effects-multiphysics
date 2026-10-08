$b = '<PROJECT_ROOT>\06_Fluent_CFD'
$so = Join-Path $b 'Logs\baseline_stdout.txt'
Get-Content $so | Select-String -Pattern '^S5B (FAIL|EVAL|CONFIRM|STAGE 3 finished|RUN COMPLETE|OK    checkpoint)|S5B-DONE' | Select-Object -ExpandProperty Line
$h = (Get-Content $so | Select-String -Pattern '^\s+iter\s+continuity' | Select-Object -Last 1).Line
$l = (Get-Content $so | Select-String -Pattern '^\s+\d+\s+\d\.\d{4}e' | Select-Object -Last 1).Line
$hn = ($h.Trim() -split '\s+')
$lv = ($l.Trim() -split '\s+')
Write-Output ('--- latest iteration ' + $lv[0] + ' ---')
for ($i = 1; $i -lt [Math]::Min($hn.Count - 1, $lv.Count); $i++) { '{0,-16} {1}' -f $hn[$i], $lv[$i] }
Get-Content (Join-Path $b 'Logs\baseline_driver.txt') -Tail 2
