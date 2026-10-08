param(
    [Parameter(Mandatory = $true)][string]$Script,
    [string]$Tag = 'run',
    [int]$Cores = 4,
    [int]$TimeoutMs = 900000
)
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\06_Fluent_CFD'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
$log  = Join-Path $base ('Logs\' + $Tag + '_driver.txt')

function Log($m) { ((Get-Date -Format 'HH:mm:ss') + '  ' + $m) | Tee-Object -FilePath $log -Append }

Remove-Item $log -Force -ErrorAction SilentlyContinue
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Set-Location $base

$so = Join-Path $base ('Logs\' + $Tag + '_stdout.txt')
$se = Join-Path $base ('Logs\' + $Tag + '_stderr.txt')
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue

$argl = @('3ddp','-g','-py')
if ($Cores -gt 1) { $argl += @('-t' + $Cores) }
$argl += @('-i', $Script)
Log ('launching: ' + ($argl -join ' '))

$p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('pid ' + $p.Id)
if (-not $p.WaitForExit($TimeoutMs)) {
    Log 'TIMEOUT - killing'
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
} else {
    Log ('exited, code ' + $p.ExitCode)
}
Start-Sleep -Seconds 2
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Log 'done'
