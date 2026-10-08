# Follow-on run, added 2026-10-07 after C0 finished: C0b = C0 (perfect geometry) with NEGEV = 1
# (*CONTROL_IMPLICIT_SOLVER), end time 0.7 (lambda 1.15). Purpose: bifurcation detection only.
# C0 used the default NEGEV = 2, which this solver build documents as "ignore negative eigenvalues"
# (d3hsp), so C0 could not flag the bifurcation. Convergence tolerances, precision, mesh, loads unchanged.
# Waits for the main chain (chain_done.txt), then runs with the same keep-awake and memory gate.
Add-Type -Name P -Namespace W -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[W.P]::SetThreadExecutionState(0x80000001) | Out-Null
$D = $PSScriptRoot; $c = 'C0b_A0p0_negev1_bifurcation_detect'
$RUN = '<PROJECT_ROOT>\15_LS_DYNA_Extension\work_12B\run_lsdyna.cmd'
$log = "$D\chain_log.txt"
function FreeMB { [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024) }
while (!(Test-Path "$D\chain_done.txt")) { Start-Sleep 60 }
Start-Sleep 40
if (!(Test-Path "$D\$c\done.txt")) {
  $t0 = Get-Date
  while ((FreeMB) -lt 7000 -and ((Get-Date) - $t0).TotalMinutes -lt 20) { Start-Sleep 20 }
  "$c launch $(Get-Date -Format s) freeMB=$(FreeMB)" | Out-File $log -Append
  & cmd.exe /c "call `"$RUN`" `"$D\$c`" case.k 4 20m" *>> $log
  'DONE' | Out-File "$D\$c\done.txt"
  "$c end $(Get-Date -Format s)" | Out-File $log -Append
}
'C0b DONE' | Out-File "$D\chain2_done.txt"
[W.P]::SetThreadExecutionState(0x80000000) | Out-Null
