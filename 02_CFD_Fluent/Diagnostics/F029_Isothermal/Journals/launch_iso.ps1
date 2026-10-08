param([string]$Journal = 'Journals/iso_diag.py', [string]$Tag = 'iso', [int]$AuditOnly = 0)
# Launch the driver OUTSIDE this shell's process tree so a dropped remote session cannot
# take the Fluent run down with it.
$drv = '<PROJECT_ROOT>\06_Fluent_CFD\Diagnostics\F029_Isothermal\Journals\run_iso.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Journal ' + $Journal + ' -Tag ' + $Tag + ' -AuditOnly ' + $AuditOnly + ' -Cores 4'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmd
    CurrentDirectory = '<PROJECT_ROOT>\06_Fluent_CFD\Diagnostics\F029_Isothermal'
}
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
