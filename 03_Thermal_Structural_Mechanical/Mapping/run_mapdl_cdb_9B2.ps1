# Section 9B-2: MAPDL (Student 2026 R1) reads each case's Fluent solid mesh (NBLOCK/EBLOCK built from ITS case file) and
# writes the native blocked CDB used as that case's External Data master mesh. PREP7 only - nothing is solved.
# Same procedure as 07_Thermal_Analysis/Mapping/MeshBased/run_mapdl_cdb.ps1 (Section 7A). RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$root = '<PROJECT_ROOT>\10_Parametric_Study\Mapping'
$exe  = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log  = Join-Path $root 'mapdl_cdb_9B2_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
foreach ($case in @('C00_PIPELINE_CHECK','V01_LOW','V03_HIGH','Q01_LOW','Q03_HIGH','T01_THIN','T03_THICK')) {
  $d = Join-Path $root $case
  Set-Location $d
  $args = @('-b','-np','1','-j','fluent_solid_mesh','-i','build_fluent_solid_cdb.inp','-o','build_fluent_solid_cdb.out')
  Log ('start ' + $case + ' MAPDL ' + ($args -join ' '))
  $p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $d -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $d 'mapdl_stdout.txt') -RedirectStandardError (Join-Path $d 'mapdl_stderr.txt')
  if (-not $p.WaitForExit(1200000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
  Log ('end ' + $case + ' exit=' + $p.ExitCode)
  foreach ($f in @('fluent_solid_mesh.cdb','fluent_solid_mesh_counts.txt')) { if (Test-Path $f) { Log ('  ' + $f + ' ' + (Get-Item $f).Length + ' ' + (Get-FileHash $f).Hash) } else { Log ('  ' + $f + ' MISSING') } }
  if (Test-Path 'fluent_solid_mesh_counts.txt') { Log ('  counts ' + (Get-Content 'fluent_solid_mesh_counts.txt')) }
  Get-ChildItem $d -File | ? { $_.Extension -in '.db','.esav','.full','.page','.lock','.rst','.emat','.mntr','.stat','.err','.log' } | % { Log ('  scratch ' + $_.Name + ' ' + $_.Length) }
}
Log 'driver done'
