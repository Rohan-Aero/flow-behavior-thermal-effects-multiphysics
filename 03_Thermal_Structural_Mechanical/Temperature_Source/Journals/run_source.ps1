# Section 7A driver: read-only Fluent export of the medium solid temperature field.
# Working directory = 07_Thermal_Analysis\Temperature_Source, so every relative write lands there.
$ErrorActionPreference = 'Continue'
$root = '<PROJECT_ROOT>'
$base = Join-Path $root '07_Thermal_Analysis\Temperature_Source'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
$log  = Join-Path $base 'Logs\source_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
$files = @('06_Fluent_CFD\Case\baseline_medium_final.cas.h5', '06_Fluent_CFD\Data\baseline_medium_final.dat.h5')
function HashSet() { $o = @(); foreach ($f in $files) { $p = Join-Path $root $f; $o += [pscustomobject]@{file=$f; sha256=(Get-FileHash $p -Algorithm SHA256).Hash; bytes=(Get-Item $p).Length; mtime=(Get-Item $p).LastWriteTime.ToString('s')} }; return $o }
$before = HashSet
Log ('before: ' + (($before | ForEach-Object { $_.file + '=' + $_.sha256.Substring(0,16) }) -join '; '))
Set-Location $base
$so = Join-Path $base 'Logs\source_stdout.txt'; $se = Join-Path $base 'Logs\source_stderr.txt'
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue
$argl = @('3ddp','-g','-py','-t4','-i','Journals/export_solid_temperature.py')
Log ('launching: ' + ($argl -join ' '))
$p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('fluent pid ' + $p.Id)
if (-not $p.WaitForExit(3600000)) { Log 'TIMEOUT - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } else { Log 'fluent exited' }
Start-Sleep -Seconds 3
Get-Process fluent,fl_mpi2610,cortex,cx2610 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $base 'Logs\Fluent_raw') -Force | Out-Null
Get-ChildItem $base -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Get-ChildItem $base -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
$after = HashSet
$same = $true; for ($i=0; $i -lt $before.Count; $i++) { if ($before[$i].sha256 -ne $after[$i].sha256) { $same = $false } }
[pscustomobject]@{before=$before; after=$after; identical=$same} | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $base 'Audit\source_case_data_hashes.json') -Encoding UTF8
Log ('after: identical=' + $same)
Log 'driver done'
