$ErrorActionPreference = 'Continue'
$base = '<PROJECT_ROOT>\05_Meshing'
$fl   = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe'
$mq   = Join-Path $base 'Mesh_Quality'
$log  = Join-Path $mq '_driver_log.txt'

function Log($m) { ((Get-Date -Format 'HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }

Remove-Item $log -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $mq '_check_complete.txt') -Force -ErrorAction SilentlyContinue
Log 'driver start (serial Fluent, one session per mesh)'

Set-Location $base

foreach ($lv in @('coarse','medium','fine')) {
    Log ("=== " + $lv + " : killing stale fluent processes ===")
    Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3

    Get-ChildItem $base -Filter '*.trn' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    $so = Join-Path $mq ($lv + '_stdout.txt')
    $se = Join-Path $mq ($lv + '_stderr.txt')
    Remove-Item $so,$se -Force -ErrorAction SilentlyContinue

    Log ("launching serial fluent 3ddp -g on " + $lv)
    $p = Start-Process -FilePath $fl -ArgumentList '3ddp','-g','-i',("Scripts/check_" + $lv + ".jou") -WorkingDirectory $base -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
    Log ("pid " + $p.Id)

    $done = $p.WaitForExit(900000)
    if (-not $done) { Log 'TIMEOUT 900 s - killing'; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    else { Log ("exited with code " + $p.ExitCode) }

    Start-Sleep -Seconds 3
    $t = Get-ChildItem $base -Filter '*.trn' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($t) { Copy-Item $t.FullName (Join-Path $mq ($lv + '_fluent_check.txt')) -Force; Log ('transcript copied: ' + $t.Name) }
    else    { Log 'NO TRANSCRIPT PRODUCED' }

    Get-Process fluent,fl_mpi2610,cortex -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 4
}

Log 'driver finished'
'ALL THREE CHECKED' | Out-File (Join-Path $mq '_check_complete.txt') -Encoding ascii
