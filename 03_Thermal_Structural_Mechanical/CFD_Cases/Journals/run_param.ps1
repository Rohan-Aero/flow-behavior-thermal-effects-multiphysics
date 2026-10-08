param(
    [string]$Cases = 'C00_PIPELINE_CHECK',
    [int]$AuditOnly = 0,
    [int]$Cores = 4
)
# Section 9B-1 driver. Runs the listed cases ONE AFTER ANOTHER (comma-separated), each in its own
# Fluent session whose working directory is 10_Parametric_Study\CFD_Cases\<CASE>, so every relative
# path a journal writes lands inside that case folder and nowhere else.
# RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$root = '<PROJECT_ROOT>\10_Parametric_Study'
$cfd  = Join-Path $root 'CFD_Cases'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
New-Item -ItemType Directory -Path (Join-Path $root 'Logs') -Force | Out-Null
$blog = Join-Path $root ('Logs\batch_driver_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
function BLog($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $blog -Append -Encoding ascii }
BLog ('batch start: cases=' + $Cases + ' audit-only=' + $AuditOnly + ' cores=' + $Cores)
foreach ($case in ($Cases -split ',')) {
    $case = $case.Trim()
    if (-not $case) { continue }
    $base = Join-Path $cfd $case
    foreach ($d in @('Case','Data','Monitors','Exports','Audit','EnSight','Logs\Fluent_raw')) {
        New-Item -ItemType Directory -Path (Join-Path $base $d) -Force | Out-Null
    }
    $log = Join-Path $base ('Logs\' + $case + '_driver.txt')
    function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
    Remove-Item $log -Force -ErrorAction SilentlyContinue
    Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    # a new run of a case replaces that case's previous solver outputs (only inside its own folder)
    foreach ($g in @('Monitors\*.out', 'Case\*.cas.h5', 'Case\*.dat.h5', 'Data\*.dat.h5', 'Exports\*.csv', 'EnSight\*',
                     'Audit\*.json', 'Audit\*.txt', 'Logs\*_transcript.trn', 'Logs\*_log.txt')) {
        Get-ChildItem (Join-Path $base $g) -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item $_.FullName -Force; Log ('cleared ' + $_.Name) }
    }
    Set-Location $base
    $env:PARAM_CASE = $case
    $env:PARAM_AUDIT_ONLY = "$AuditOnly"
    $so = Join-Path $base ('Logs\' + $case + '_stdout.txt')
    $se = Join-Path $base ('Logs\' + $case + '_stderr.txt')
    Remove-Item $so,$se -Force -ErrorAction SilentlyContinue
    $argl = @('3ddp','-g','-py',('-t' + $Cores),'-i','../Journals/solve_param.py')
    Log ('launching case ' + $case + ' (audit-only=' + $AuditOnly + '): ' + ($argl -join ' '))
    BLog ('case ' + $case + ' launched')
    $t0 = Get-Date
    $p = Start-Process -FilePath $fl -ArgumentList $argl -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
    Log ('fluent pid ' + $p.Id)
    if (-not $p.WaitForExit(14400000)) { Log 'TIMEOUT 4 h - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    else { Log 'fluent exited' }
    $wall = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    Start-Sleep -Seconds 3
    Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-ChildItem $base -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
    Get-ChildItem $base -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $base ('Logs\Fluent_raw\' + $_.Name)) -Force }
    $done = Select-String -Path $so -Pattern 'S9B1-DONE (\S+)' -ErrorAction SilentlyContinue | Select-Object -Last 1
    $st = if ($done) { $done.Matches[0].Groups[1].Value } else { 'NO_DONE_MARKER' }
    Log ('wall clock ' + $wall + ' s; journal status ' + $st)
    BLog ('case ' + $case + ' finished: status ' + $st + ', wall ' + $wall + ' s')
    Log 'driver done'
}
BLog 'batch done'
