# Section 7B: runs the APDL post-snippet SYNTAX TEST on a toy model (not a project result). Logs to snippet_test_driver.txt
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\08_Structural_Analysis\Audits\APDL_snippet_test'
$exe  = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\ansys\bin\winx64\MAPDL.exe'
$log  = Join-Path $base 'snippet_test_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Set-Location $base
Copy-Item -Force '<PROJECT_ROOT>\08_Structural_Analysis\Workbench\Scripts\s7b_post_snippet.inp' (Join-Path $base 's7b_post_snippet.inp')
$args = @('-b','-np','1','-j','s7b_toy','-i','snippet_test_toy.inp','-o','snippet_test_toy.out')
Log ('start MAPDL ' + ($args -join ' '))
$p = Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $base 'mapdl_stdout.txt') -RedirectStandardError (Join-Path $base 'mapdl_stderr.txt')
if (-not $p.WaitForExit(900000)) { Log 'TIMEOUT'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Log ('end exit=' + $p.ExitCode)
Get-ChildItem $base -File | % { Log ('file ' + $_.Name + ' ' + $_.Length) }
Log 'driver done'
