# Section 9B-2: copies the two 8A static result files (read-only use of the 8A project) and re-extracts their nodal
# tables with MAPDL /POST1 (no solve). RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$d   = '<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases\S2_REEXTRACT'
$src = '<PROJECT_ROOT>\08_Structural_Analysis\Buckling\Workbench\Flow_Behavior_Thermal_Effects_Buckling_8A_files\dp0'
$exe = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log = Join-Path $d 's2x_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
foreach ($p in @(@('SYS-6','s2'), @('SYS-3','s1'))) {
  $f = Join-Path $src ($p[0] + '\MECH\file.rst')
  Log ('source ' + $f + ' ' + (Get-Item $f).Length + ' ' + (Get-FileHash $f).Hash)
  Copy-Item -Force $f (Join-Path $d ($p[1] + '.rst'))
  Log ('copy ' + $p[1] + '.rst ' + (Get-FileHash (Join-Path $d ($p[1] + '.rst'))).Hash)
}
$args = @('-b','-np','1','-j','s2x','-i','run_s2x.inp','-o','run_s2x.out')
Log ('start MAPDL ' + ($args -join ' '))
$pr = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $d -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $d 'stdout.txt') -RedirectStandardError (Join-Path $d 'stderr.txt')
if (-not $pr.WaitForExit(1200000)) { Log 'TIMEOUT'; Stop-Process -Id $pr.Id -Force -ErrorAction SilentlyContinue }
Log ('end exit=' + $pr.ExitCode)
Get-ChildItem $d -File | ? { $_.Extension -in '.rst' } | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $d -File | % { Log ('  file ' + $_.Name + ' ' + $_.Length) }
Log 'driver done'
