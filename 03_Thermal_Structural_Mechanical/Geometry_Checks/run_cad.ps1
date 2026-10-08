# Section 9B-1: build the T01_THIN and T03_THICK CAD in SpaceClaim (headless batch), one process per case.
# Writes only into 10_Parametric_Study\Geometry_Checks\<CASE>\. RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$gc = '<PROJECT_ROOT>\10_Parametric_Study\Geometry_Checks'
$sc = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe'
$log = Join-Path $gc 'run_cad_driver.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Remove-Item $log -Force -ErrorAction SilentlyContinue
foreach ($case in @('T01_THIN','T03_THICK')) {
    $scr = Join-Path $gc ('build_geometry_' + $case + '.py')
    New-Item -ItemType Directory -Path (Join-Path $gc $case) -Force | Out-Null
    $argl = @(('/RunScript="' + $scr + '"'), '/ScriptAPI=21', '/Headless=True', '/Splash=False', '/Welcome=False', '/ExitAfterScript=True')
    Log ('launch ' + $case + ': ' + ($argl -join ' '))
    $t0 = Get-Date
    $p = Start-Process -FilePath $sc -ArgumentList $argl -PassThru
    if (-not $p.WaitForExit(900000)) { Log ('TIMEOUT 15 min ' + $case + ' - killing'); Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    Log ($case + ' exit code ' + $p.ExitCode + ' after ' + [math]::Round(((Get-Date) - $t0).TotalSeconds,1) + ' s')
    Start-Sleep -Seconds 2
}
Log 'cad driver done'
