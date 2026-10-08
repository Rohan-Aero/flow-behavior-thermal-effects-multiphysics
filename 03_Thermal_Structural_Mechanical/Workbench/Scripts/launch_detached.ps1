# Generic detached launcher (WMI Win32_Process.Create) for a PowerShell driver script with no arguments.
param([string]$Script, [string]$WorkDir)
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $Script + '"'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $WorkDir }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
