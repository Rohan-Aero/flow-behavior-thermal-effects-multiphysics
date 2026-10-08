# Section 9B-2: runs, one after the other, the remaining design cases (wb_param_9B2_REST: T03, V01, V03, Q01, Q03), then -
# only if no case stopped - the 9A structural mesh-adequacy cases M01/M02 and the S3 deck (deck mode, NOT solved).
# Written after the first ALL batch was interrupted at T03 by a machine shutdown (26-09-2026 23:57); C00 and T01 had
# completed in that batch. RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$sc  = '<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases'
$log = Join-Path $sc 'Audits\chain_rest_log.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
function RunWB($j, $tag, $min) {
  $wd = Join-Path $sc ('Audits\Run_' + $tag)
  New-Item -ItemType Directory -Force $wd | Out-Null
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sc 'run_wb.ps1') -Journal (Join-Path $sc ('Scripts\' + $j)) -Tag ('wb_' + $tag) -WorkDir $wd -TimeoutMin $min
}
Log 'start REST (T03, V01, V03, Q01, Q03)'
RunWB 'wb_param_9B2_REST.wbjn' 'REST' 300
$r = Get-Content (Join-Path $sc 'Audits\wb_param_9B2_REST_log.txt') -Raw
if ($r -match 'STOP:' -or $r -match 'FATAL' -or $r -notmatch 'WB PARAMETRIC MECHANICAL REST DONE') { Log 'REST reported STOP/FATAL or did not finish - chain stopped'; exit }
Log 'REST done; start M01/M02'
RunWB 'wb_param_9B2_M.wbjn' 'M' 120
$m = Get-Content (Join-Path $sc 'Audits\wb_param_9B2_M_log.txt') -Raw
if ($m -match 'STOP:' -or $m -match 'FATAL') { Log 'M reported STOP/FATAL - S3 deck not started'; exit }
Log 'M done; start S3 deck (no solve)'
RunWB 'wb_s3_9B2_deck.wbjn' 'S3_deck' 60
Log 'chain done'
