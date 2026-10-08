param(
    [int]$Iters = 150,
    [string]$Tag = 'setup',
    [int]$Cores = 4,
    [int]$TimeoutMs = 3000000
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
$env:S5A_ITERS = "$Iters"

# Fluent stops at an "OK to overwrite?" prompt in batch, which is indistinguishable
# from a hang. Clear every file this run will write before launching.
$doomed = @(
    (Join-Path $base ('Logs\setup_transcript_' + $Iters + '.trn')),
    (Join-Path $base 'Baseline_Setup\baseline_setup.cas.h5'),
    (Join-Path $base ('Test_Run\test_' + $Iters + 'iters.cas.h5')),
    (Join-Path $base ('Test_Run\test_' + $Iters + 'iters.dat.h5')),
    (Join-Path $base 'Test_Run\s5a_monitors.out')
)
foreach ($f in $doomed) { if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue; Log ('cleared ' + (Split-Path $f -Leaf)) } }

$so = Join-Path $base ('Logs\' + $Tag + '_stdout.txt')
$se = Join-Path $base ('Logs\' + $Tag + '_stderr.txt')
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue

$argl = @('3ddp','-g','-py')
if ($Cores -gt 1) { $argl += ('-t' + $Cores) }
$argl += @('-i','Journals/setup_baseline.py')
Log ('S5A_ITERS=' + $Iters + '  launching: ' + ($argl -join ' '))

$p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('pid ' + $p.Id)
if (-not $p.WaitForExit($TimeoutMs)) { Log 'TIMEOUT - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
else { Log ('exited, code ' + $p.ExitCode) }
Start-Sleep -Seconds 2
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Log 'driver done'
