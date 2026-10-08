param([string]$Journal, [string]$Tag)
# Generic read-only Fluent runner in 07_Thermal_Analysis\Temperature_Source; hashes the official case/data before and after.
$ErrorActionPreference = 'Continue'
$root = '<PROJECT_ROOT>'
$base = Join-Path $root '07_Thermal_Analysis\Temperature_Source'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
New-Item -ItemType Directory -Path (Join-Path $base 'Probe') -Force | Out-Null
$log  = Join-Path $base ('Logs\' + $Tag + '_driver.txt')
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
$files = @('06_Fluent_CFD\Case\baseline_medium_final.cas.h5', '06_Fluent_CFD\Data\baseline_medium_final.dat.h5')
$before = @(); foreach ($f in $files) { $before += (Get-FileHash (Join-Path $root $f) -Algorithm SHA256).Hash }
Set-Location $base
$so = Join-Path $base ('Logs\' + $Tag + '_stdout.txt'); $se = Join-Path $base ('Logs\' + $Tag + '_stderr.txt')
$p = Start-Process -FilePath $fl -ArgumentList @('3ddp','-g','-py','-t4','-i',$Journal) -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('fluent pid ' + $p.Id + ' journal ' + $Journal)
if (-not $p.WaitForExit(3600000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force } else { Log 'fluent exited' }
Start-Sleep -Seconds 3
Get-ChildItem $base -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Get-ChildItem $base -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
$after = @(); foreach ($f in $files) { $after += (Get-FileHash (Join-Path $root $f) -Algorithm SHA256).Hash }
Log ('case/data identical after run: ' + (($before[0] -eq $after[0]) -and ($before[1] -eq $after[1])))
Log 'driver done'
