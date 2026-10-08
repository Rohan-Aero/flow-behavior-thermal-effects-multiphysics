$drv = '<PROJECT_ROOT>\10_Parametric_Study\Mapping\run_mapdl_cdb_9B2.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '"'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = '<PROJECT_ROOT>\10_Parametric_Study\Mapping' }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
