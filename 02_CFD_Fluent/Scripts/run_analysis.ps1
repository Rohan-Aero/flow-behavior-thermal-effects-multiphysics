$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\05_Meshing'
$py   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\commonfiles\CPython\3_10\winx64\Release\python\python.exe'
$log  = Join-Path $base 'Mesh_Quality\_analysis_log.txt'
Remove-Item $log -Force -ErrorAction SilentlyContinue
Set-Location $base
& $py (Join-Path $base 'Scripts\mesh_analysis.py') *>&1 | Tee-Object -FilePath $log
'ANALYSIS EXIT ' + $LASTEXITCODE | Out-File -FilePath $log -Append -Encoding ascii
