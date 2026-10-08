# Compact 12C chain status: last chain_log lines, then per case: last step, exit line, out-of-core flag, done flag, series present.
$B = Split-Path $PSScriptRoot -Parent; $D = "$B\runs"
Get-Content "$D\chain_log.txt" -EA SilentlyContinue | ? { $_ -match 'launch|end|CHAIN' } | Select -Last 4
foreach ($c in 'C5_A1p2','C0_A0p0','C1_A0p1','C2_A0p3','C3_A0p6','C4_A0p9','N1_A0p1_halfstep') {
  $m = "$D\$c\messag"; if (!(Test-Path $m)) { "$c : not started"; continue }
  $s = (Select-String -Path $m -Pattern 'BEGIN implicit' | Select -Last 1).Line -replace '\s+',' ' -replace 'BEGIN implicit statics ',''
  $x = (Get-Content "$D\$c\run_status.txt" -EA SilentlyContinue | ? { $_ -match 'EXIT' }) -join ''
  $nt = [bool](Select-String -Path "$D\$c\messag" -Pattern 'N o r m a l' -Quiet)
  $oc = [bool](Select-String -Path $m -Pattern 'out-of-core' -Quiet)
  "$c :$s | $x | normal=$nt ooc=$oc done=$(Test-Path "$D\$c\done.txt") series=$(Test-Path "$B\results\series\$($c)_series.csv")"
}
"freeMB=$([int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)) solver=$(@(Get-Process | ? {$_.Name -like 'ls-dyna*'}).Count)"
