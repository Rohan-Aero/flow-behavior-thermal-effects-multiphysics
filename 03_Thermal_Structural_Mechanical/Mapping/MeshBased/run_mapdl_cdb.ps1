# Section 7A: MAPDL (Student 2026 R1) reads the Fluent solid mesh (NBLOCK/EBLOCK built from the case file) and writes
# the native blocked CDB used as the External Data master mesh. PREP7 only - nothing is solved.
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\07_Thermal_Analysis\Mapping\MeshBased'
$exe  = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log  = Join-Path $base 'mapdl_cdb_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Set-Location $base
$args = @('-b','-np','1','-j','fluent_solid_mesh','-i','build_fluent_solid_cdb.inp','-o','build_fluent_solid_cdb.out')
Log ('start MAPDL ' + ($args -join ' '))
$p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $base 'mapdl_stdout.txt') -RedirectStandardError (Join-Path $base 'mapdl_stderr.txt')
if (-not $p.WaitForExit(1200000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Log ('end exit=' + $p.ExitCode)
foreach ($f in @('fluent_solid_mesh.cdb','fluent_solid_mesh_counts.txt')) { if (Test-Path $f) { Log ($f + ' ' + (Get-Item $f).Length + ' ' + (Get-FileHash $f).Hash) } else { Log ($f + ' MISSING') } }
Get-ChildItem $base -File | ? { $_.Extension -in '.db','.esav','.full','.page','.lock','.rst','.emat','.mntr','.stat','.err','.log' } | % { Log ('scratch ' + $_.Name + ' ' + $_.Length) }
Log 'driver done'
