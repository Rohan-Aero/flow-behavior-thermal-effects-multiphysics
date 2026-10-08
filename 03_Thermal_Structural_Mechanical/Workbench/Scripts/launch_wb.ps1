param([string]$Journal, [string]$Tag, [string]$WorkDir)
$drv = '<PROJECT_ROOT>\08_Structural_Analysis\Workbench\Scripts\run_wb.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Journal "' + $Journal + '" -Tag ' + $Tag + ' -WorkDir "' + $WorkDir + '"'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $WorkDir }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
