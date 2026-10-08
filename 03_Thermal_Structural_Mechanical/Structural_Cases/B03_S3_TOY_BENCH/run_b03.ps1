# Section 9B-2: runs the B03_S3_TOY_BENCH benchmark (MAPDL, toy tube, S3 ends). Not project results. RE-ANALYSIS 2026.
param([string]$Dir = '<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases\B03_S3_TOY_BENCH')
$ErrorActionPreference = 'Continue'
$d   = $Dir
$s8  = '<PROJECT_ROOT>\08_Structural_Analysis'
$exe = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log = Join-Path $d 'b03_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Copy-Item -Force (Join-Path $s8 'Buckling\Workbench\Scripts\s8a_buckle_snippet.inp') $d
Copy-Item -Force (Join-Path $s8 'Workbench\Scripts\s7b_post_snippet.inp') $d
$args = @('-b','-np','2','-j','b03','-i','b03_main.inp','-o','b03_main.out')
Log ('start ' + ($args -join ' '))
$p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $d -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $d 'stdout.txt') -RedirectStandardError (Join-Path $d 'stderr.txt')
if (-not $p.WaitForExit(1800000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Log ('end exit=' + $p.ExitCode)
Get-ChildItem $d -File | ? { $_.Extension -in '.rst','.full','.esav','.emat','.db','.mode','.page','.ldhi','.r001','.rdb','.stat','.mntr','.DSP','.lock','.osav','.cnm' } | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $d -File | % { Log ('  file ' + $_.Name + ' ' + $_.Length) }
Log 'driver done'
