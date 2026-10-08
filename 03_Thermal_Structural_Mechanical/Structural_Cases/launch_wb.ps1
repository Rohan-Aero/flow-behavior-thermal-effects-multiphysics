param([string]$Journal, [string]$Tag, [string]$WorkDir, [int]$TimeoutMin = 240)
# Detached launch of run_wb.ps1 (survives a dropped remote session). RE-ANALYSIS 2026.
$drv = '<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases\run_wb.ps1'
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $drv + '" -Journal "' + $Journal + '" -Tag ' + $Tag + ' -WorkDir "' + $WorkDir + '" -TimeoutMin ' + $TimeoutMin
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $WorkDir }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
