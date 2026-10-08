# 12C run chain (supersedes calling run_12C_chain.cmd directly; same cases, order, runner and arguments).
# - Holds a per-process "system required" request so idle sleep cannot end a run (released on exit;
#   no power setting is changed). A user restart still ends it (C5 attempt 2, 2026-10-03).
# - Memory gate: waits up to 20 min for >= 7000 MB free before each case, because a case started on
#   low free memory factorises out of core (Warning 60120), 3-4x slower. Results are not affected.
# - Skips cases that already have done.txt, so the chain can be relaunched after an interruption.
Add-Type -Name P -Namespace W -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState(0x80000001) | Out-Null   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
$D = $PSScriptRoot
$RUN = '<PROJECT_ROOT>\15_LS_DYNA_Extension\work_12B\run_lsdyna.cmd'
$log = "$D\chain_log.txt"
function FreeMB { [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024) }
"CHAIN START $(Get-Date -Format s)" | Out-File $log -Append
foreach ($c in 'C5_A1p2','C0_A0p0','C1_A0p1','C2_A0p3','C3_A0p6','C4_A0p9','N1_A0p1_halfstep') {
  if (Test-Path "$D\$c\done.txt") { "$c skipped (done.txt present)" | Out-File $log -Append; continue }
  $t0 = Get-Date
  while ((FreeMB) -lt 7000 -and ((Get-Date) - $t0).TotalMinutes -lt 20) { Start-Sleep 20 }
  "$c launch $(Get-Date -Format s) freeMB=$(FreeMB)" | Out-File $log -Append
  & cmd.exe /c "call `"$RUN`" `"$D\$c`" case.k 4 20m" *>> $log
  'DONE' | Out-File "$D\$c\done.txt"
  "$c end $(Get-Date -Format s)" | Out-File $log -Append
  Start-Sleep 40
}
'ALL DONE' | Out-File "$D\chain_done.txt"
"CHAIN END $(Get-Date -Format s)" | Out-File $log -Append
[W.P]::SetThreadExecutionState(0x80000000) | Out-Null
