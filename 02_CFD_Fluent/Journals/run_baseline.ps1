param(
    [string]$Tag = 'baseline',
    [int]$AuditOnly = 0,
    [int]$Cores = 4
)
$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\06_Fluent_CFD'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
foreach ($d in @('Baseline','Case','Data','Monitors','Profiles','Exports','Figures','Audit','Logs\Fluent_raw')) {
    New-Item -ItemType Directory -Path (Join-Path $base $d) -Force | Out-Null
}
$log = Join-Path $base ('Logs\' + $Tag + '_driver.txt')
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

if ($AuditOnly -eq 0) {
    # a batch run must never meet an overwrite prompt: clear everything this run writes
    foreach ($g in @('Monitors\baseline_monitors.out', 'Case\*.cas.h5', 'Data\*.dat.h5', 'Exports\*.csv',
                     'Audit\fluent_*.txt', 'Audit\setup_audit_*', 'Audit\convergence_evaluations.json',
                     'Audit\run_summary.json', ('Logs\' + $Tag + '_transcript.trn'))) {
        Get-ChildItem (Join-Path $base $g) -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force; Log ('cleared ' + $_.Name) }
    }
}
Set-Location $base
$env:BASE_TAG = $Tag
$env:S5B_AUDIT_ONLY = "$AuditOnly"
$so = Join-Path $base ('Logs\' + $Tag + '_stdout.txt')
$se = Join-Path $base ('Logs\' + $Tag + '_stderr.txt')
Remove-Item $so,$se -Force -ErrorAction SilentlyContinue
$argl = @('3ddp','-g','-py',('-t' + $Cores),'-i','Journals/solve_baseline.py')
Log ('launching (audit-only=' + $AuditOnly + '): ' + ($argl -join ' '))
$p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
Log ('fluent pid ' + $p.Id)
if (-not $p.WaitForExit(14400000)) { Log 'TIMEOUT 4 h - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
else { Log 'fluent exited' }
Start-Sleep -Seconds 3
Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-ChildItem $base -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Get-ChildItem $base -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
Log 'driver done'
