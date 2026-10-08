$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\06_Fluent_CFD'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Set-Location $base
$so = Join-Path $base 'Logs\probe_py_stdout.txt'
$se = Join-Path $base 'Logs\probe_py_stderr.txt'
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath $fl -ArgumentList '3ddp','-g','-py','-i','Journals/probe_py.py' -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
if (-not $p.WaitForExit(180000)) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Write-Output 'TIMEOUT' }
else { Write-Output ('exit ' + $p.ExitCode) }
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Output '--- stdout ---'
Get-Content $so -ErrorAction SilentlyContinue | Select-String -Pattern 'PYPROBE|rror|nvalid|arning' | Select-Object -ExpandProperty Line
Write-Output '--- stderr ---'
Get-Content $se -ErrorAction SilentlyContinue | Select-Object -First 20
