$drv = '<PROJECT_ROOT>\07_Thermal_Analysis\Temperature_Source\Journals\run_source.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '"'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = '<PROJECT_ROOT>\07_Thermal_Analysis\Temperature_Source' }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
