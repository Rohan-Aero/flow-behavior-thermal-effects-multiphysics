# Section 8A: runs the toy eigen-buckling BENCHMARK (sway and no-sway ends). Not project results.
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\08_Structural_Analysis\Buckling\Benchmark'
$exe  = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log  = Join-Path $base 'bench_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
foreach ($case in @('sway','nosway')) {
  $d = Join-Path $base $case
  New-Item -ItemType Directory -Path $d -Force | Out-Null
  foreach ($f in @('bench_main.inp', ('bench_' + $case + '.inp'))) { Copy-Item -Force (Join-Path $base $f) (Join-Path $d $f) }
  Copy-Item -Force '<PROJECT_ROOT>\08_Structural_Analysis\Buckling\Workbench\Scripts\s8a_buckle_snippet.inp' (Join-Path $d 's8a_buckle_snippet.inp')
  $args = @('-b','-np','2','-j',('bench_' + $case),'-i',('bench_' + $case + '.inp'),'-o',('bench_' + $case + '.out'))
  Log ('start ' + $case + ' ' + ($args -join ' '))
  $p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $d -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $d 'stdout.txt') -RedirectStandardError (Join-Path $d 'stderr.txt')
  if (-not $p.WaitForExit(1200000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
  Log ('end ' + $case + ' exit=' + $p.ExitCode)
  Get-ChildItem $d -File | ? { $_.Extension -in '.rst','.full','.esav','.emat','.db','.mode','.page','.ldhi','.r001','.rdb','.stat','.mntr','.DSP','.lock' } | Remove-Item -Force -ErrorAction SilentlyContinue
  Get-ChildItem $d -File | % { Log ('  file ' + $_.Name + ' ' + $_.Length) }
}
Log 'driver done'
