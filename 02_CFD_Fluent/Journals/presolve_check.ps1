$r = '<PROJECT_ROOT>'
$b = Join-Path $r '06_Fluent_CFD'
Write-Output '===== 5A test150 run: Inconel density lines ====='
Select-String -Path (Join-Path $b 'Logs\setup_log_150.txt') -Pattern 'inconel' | Select-Object -ExpandProperty Line
Write-Output ''
Write-Output '===== 5A dry run (first attempt) evidence of 2719 ====='
Select-String -Path (Join-Path $b 'Logs\setup_log_0.txt') -Pattern 'inconel' | Select-Object -ExpandProperty Line
Write-Output ''
Write-Output '===== NR requirements ====='
Select-String -Path (Join-Path $r '01_Requirements\ENGINEERING_REQUIREMENTS.md') -Pattern '^\| NR-|^\| PR-|^\| FR-' | Select-Object -ExpandProperty Line
Write-Output ''
Write-Output '===== EXPECTED_RESULTS table rows ====='
Select-String -Path (Join-Path $r '02_Engineering_Calculations\EXPECTED_RESULTS.md') -Pattern '^\|' | Select-Object -ExpandProperty Line
Write-Output ''
Write-Output '===== axial_profiles.csv head ====='
Get-Content (Join-Path $r '02_Engineering_Calculations\axial_profiles.csv') -TotalCount 4
Write-Output ('rows: ' + (Get-Content (Join-Path $r '02_Engineering_Calculations\axial_profiles.csv')).Count)
Write-Output ''
Write-Output '===== baseline_results.csv ====='
Get-Content (Join-Path $r '02_Engineering_Calculations\baseline_results.csv')
