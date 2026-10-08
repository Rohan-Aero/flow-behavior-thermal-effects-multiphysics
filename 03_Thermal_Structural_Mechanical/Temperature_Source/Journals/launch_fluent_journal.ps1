param([string]$Journal, [string]$Tag)
$drv = '<PROJECT_ROOT>\07_Thermal_Analysis\Temperature_Source\Journals\run_fluent_journal.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Journal ' + $Journal + ' -Tag ' + $Tag
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = '<PROJECT_ROOT>\07_Thermal_Analysis\Temperature_Source' }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
