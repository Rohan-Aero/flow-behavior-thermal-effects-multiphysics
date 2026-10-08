# Section 9B-2: waits for the design-case batch (wb_param_9B2_ALL) to finish, then - only if no case stopped - runs the
# 9A structural mesh-adequacy cases M01/M02 and writes the S3 solver input deck (deck mode, NOT solved). RE-ANALYSIS 2026.
$ErrorActionPreference = 'Continue'
$sc  = '<PROJECT_ROOT>\10_Parametric_Study\Structural_Cases'
$log = Join-Path $sc 'Audits\chain_after_all_log.txt'
function Log($m) { ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m) | Out-File -FilePath $log -Append -Encoding ascii }
Log 'waiting for Run_ALL'
while (-not (Select-String -Path (Join-Path $sc 'Audits\Run_ALL\wb_ALL_driver.txt') -Pattern 'driver done' -Quiet -ErrorAction SilentlyContinue)) { Start-Sleep 30 }
$all = Get-Content (Join-Path $sc 'Audits\wb_param_9B2_ALL_log.txt') -Raw
if ($all -match 'STOP:' -or $all -match 'FATAL') { Log 'Run_ALL reported STOP/FATAL - chain aborted (nothing else started)'; exit }
Log 'Run_ALL finished without STOP; starting M01/M02'
New-Item -ItemType Directory -Force (Join-Path $sc 'Audits\Run_M') | Out-Null
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sc 'run_wb.ps1') -Journal (Join-Path $sc 'Scripts\wb_param_9B2_M.wbjn') -Tag wb_M -WorkDir (Join-Path $sc 'Audits\Run_M') -TimeoutMin 120
Log 'M batch finished; starting S3 deck (no solve)'
New-Item -ItemType Directory -Force (Join-Path $sc 'Audits\Run_S3_deck') | Out-Null
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $sc 'run_wb.ps1') -Journal (Join-Path $sc 'Scripts\wb_s3_9B2_deck.wbjn') -Tag wb_S3deck -WorkDir (Join-Path $sc 'Audits\Run_S3_deck') -TimeoutMin 60
Log 'chain done'
