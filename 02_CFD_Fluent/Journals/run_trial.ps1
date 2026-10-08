param(
    [string]$Tag = 'A',
    [int]$FlowIters = 120,
    [int]$EnergyIters = 150,
    [double]$SolidFactor = 1.0,
    [int]$Cores = 4
)
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\06_Fluent_CFD'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
foreach ($d in @('Baseline','Case','Data','Monitors','Profiles','Exports','Figures','Audit')) {
    New-Item -ItemType Directory -Path (Join-Path $base $d) -Force | Out-Null
}
$log = Join-Path $base ('Logs\trial_' + $Tag + '_driver.txt')
function Log($m) { ((Get-Date -Format 'HH:mm:ss') + '  ' + $m) | Tee-Object -FilePath $log -Append }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
foreach ($f in @(('Monitors\trial_' + $Tag + '.out'), ('Monitors\trial_' + $Tag + '_residuals.txt'), ('Monitors\trial_' + $Tag + '_result.json'))) {
    $p = Join-Path $base $f; if (Test-Path $p) { Remove-Item $p -Force }
}
Set-Location $base
$env:TRIAL_TAG = $Tag
$env:TRIAL_FLOW_ITERS = "$FlowIters"
$env:TRIAL_ENERGY_ITERS = "$EnergyIters"
$env:TRIAL_SOLID_FACTOR = "$SolidFactor"
$so = Join-Path $base ('Logs\trial_' + $Tag + '_stdout.txt')
$se = Join-Path $base ('Logs\trial_' + $Tag + '_stderr.txt')
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue
$argl = @('3ddp','-g','-py',('-t' + $Cores),'-i','Journals/startup_trial.py')
Log ('trial ' + $Tag + ' launching: ' + ($argl -join ' '))
$p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('pid ' + $p.Id)
if (-not $p.WaitForExit(1800000)) { Log 'TIMEOUT - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
else { Log 'exited' }
Start-Sleep -Seconds 2
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-ChildItem $base -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Get-ChildItem $base -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Log 'driver done'
