# Detached launch of run_cad.ps1 (survives a dropped remote session). RE-ANALYSIS 2026.
$drv = '<PROJECT_ROOT>\10_Parametric_Study\Geometry_Checks\run_cad.ps1'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '"'
    CurrentDirectory = '<PROJECT_ROOT>\10_Parametric_Study\Geometry_Checks'
}
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
