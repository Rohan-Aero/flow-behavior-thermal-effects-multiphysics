$b = '<PROJECT_ROOT>\06_Fluent_CFD'
$so = Join-Path $b 'Logs\test150_stdout.txt'
Write-Output '===== warnings / errors in the solver output ====='
$hits = Select-String -Path $so -Pattern 'nan|NaN|divergen|Divergen|floating point|temperature limited|turbulent viscosity limited|reversed flow|Warning|WARNING|Error:'
if ($hits) { $hits | ForEach-Object { '{0,6}: {1}' -f $_.LineNumber, $_.Line.Trim() } | Select-Object -First 40 }
else { Write-Output '(none)' }

Write-Output ''
Write-Output '===== residual header + first 3 + last 8 iterations ====='
$res = Select-String -Path $so -Pattern '^\s*\d+\s+\d\.\d{4}e[+-]\d\d' | Select-Object -ExpandProperty Line
Select-String -Path $so -Pattern 'iter\s+continuity' | Select-Object -First 1 | ForEach-Object { $_.Line }
$res | Select-Object -First 3
Write-Output '   ...'
$res | Select-Object -Last 8
Write-Output ('total residual lines: ' + $res.Count)

Write-Output ''
Write-Output '===== monitor file (head + tail) ====='
$mf = Join-Path $b 'Test_Run\s5a_monitors.out'
if (Test-Path $mf) {
    Get-Content $mf -TotalCount 4
    Write-Output '   ...'
    Get-Content $mf -Tail 3
    Write-Output ('monitor lines: ' + (Get-Content $mf).Count)
} else { Write-Output 'monitor file NOT FOUND' }

Write-Output ''
Write-Output '===== files produced ====='
Get-ChildItem $b -Recurse -File | Where-Object { $_.Length -gt 0 } | Sort-Object FullName |
    ForEach-Object { '{0,12}  {1}' -f $_.Length, $_.FullName.Replace($b + '\', '') }
