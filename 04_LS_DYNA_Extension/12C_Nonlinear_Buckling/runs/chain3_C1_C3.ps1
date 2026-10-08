# Scope change 2026-10-07 (user instruction): reduced final 12C study = THREE-POINT imperfection sensitivity,
# C1 (0.1 mm), C3 (0.6 mm), C5 (1.2 mm). C5 completed; C1 running; C3 next. C2, C4, N1, C0b are NOT run.
# This replaces keepawake_chain.ps1 (stopped while C1 was running; the C1 solver process was left running)
# and chain2_C0b.ps1 (stopped while waiting; C0b never started).
# Same runner, arguments, keep-awake request and memory gate as keepawake_chain.ps1.
Add-Type -Name P -Namespace W -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState(0x80000001) | Out-Null
$D = $PSScriptRoot
$RUN = '<PROJECT_ROOT>\15_LS_DYNA_Extension\work_12B\run_lsdyna.cmd'
$log = "$D\chain_log.txt"
function FreeMB { [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024) }
"CHAIN3 START $(Get-Date -Format s) (three-point scope: C1, C3, C5)" | Out-File $log -Append
# C1 was launched by keepawake_chain.ps1; wait for run_lsdyna.cmd to write its EXIT line.
while (-not (Select-String -Path "$D\C1_A0p1\run_status.txt" -Pattern 'EXIT' -Quiet)) { Start-Sleep 30 }
'DONE' | Out-File "$D\C1_A0p1\done.txt"
"C1_A0p1 end $(Get-Date -Format s) (EXIT detected by chain3)" | Out-File $log -Append
Start-Sleep 40
$c = 'C3_A0p6'
if (!(Test-Path "$D\$c\done.txt")) {
  $t0 = Get-Date
  while ((FreeMB) -lt 7000 -and ((Get-Date) - $t0).TotalMinutes -lt 20) { Start-Sleep 20 }
  "$c launch $(Get-Date -Format s) freeMB=$(FreeMB)" | Out-File $log -Append
  & cmd.exe /c "call `"$RUN`" `"$D\$c`" case.k 4 20m" *>> $log
  'DONE' | Out-File "$D\$c\done.txt"
  "$c end $(Get-Date -Format s)" | Out-File $log -Append
}
'C1 + C3 DONE' | Out-File "$D\chain3_done.txt"
"CHAIN3 END $(Get-Date -Format s)" | Out-File $log -Append
[W.P]::SetThreadExecutionState(0x80000000) | Out-Null
