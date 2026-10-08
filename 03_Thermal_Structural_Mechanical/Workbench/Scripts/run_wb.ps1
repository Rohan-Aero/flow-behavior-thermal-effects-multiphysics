param([string]$Journal, [string]$Tag, [string]$WorkDir)
# Generic Workbench batch driver: runwb2 -B -R <journal>. Logs to <WorkDir>\<Tag>_driver.txt
$ErrorActionPreference = 'Continue'
$wb = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\runwb2.exe'
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
$log = Join-Path $WorkDir ($Tag + '_driver.txt')
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Set-Location $WorkDir
Log ('launching runwb2 -B -R ' + $Journal)
$p = Start-Process -FilePath $wb -ArgumentList @('-B','-R',('"' + $Journal + '"')) -WorkingDirectory $WorkDir -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $WorkDir ($Tag + '_stdout.txt')) -RedirectStandardError (Join-Path $WorkDir ($Tag + '_stderr.txt'))
Log ('pid ' + $p.Id)
if (-not $p.WaitForExit(5400000)) { Log 'TIMEOUT 90 min - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } else { Log 'runwb2 exited' }
Log 'driver done'
