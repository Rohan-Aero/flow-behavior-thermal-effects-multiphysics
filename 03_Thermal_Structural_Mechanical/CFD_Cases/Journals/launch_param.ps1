param([string]$Cases = 'C00_PIPELINE_CHECK', [int]$AuditOnly = 0)
# Launch the 9B-1 driver OUTSIDE this shell's process tree so a dropped remote session cannot take the
# Fluent runs down with it. RE-ANALYSIS 2026.
$drv = '<PROJECT_ROOT>\10_Parametric_Study\CFD_Cases\Journals\run_param.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Cases ' + $Cases + ' -AuditOnly ' + $AuditOnly + ' -Cores 4'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmd
    CurrentDirectory = '<PROJECT_ROOT>\10_Parametric_Study\CFD_Cases'
}
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
