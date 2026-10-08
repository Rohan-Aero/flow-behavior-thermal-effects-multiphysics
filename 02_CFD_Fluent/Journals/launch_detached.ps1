param([string]$Tag = 'baseline')
# Launch the production driver OUTSIDE this shell's process tree, so a dropped remote
# session cannot take a multi-hour Fluent run down with it.
$drv = '<PROJECT_ROOT>\06_Fluent_CFD\Journals\run_baseline.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Tag ' + $Tag + ' -AuditOnly 0 -Cores 4'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $cmd
    CurrentDirectory = '<PROJECT_ROOT>\06_Fluent_CFD'
}
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
