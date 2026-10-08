# Section 12A - LS-DYNA feasibility: read-only machine audit (re-runnable).
# Writes machine_audit_12A_output.txt next to this script. Changes nothing on the machine.
# Optional: -DriveScan also repeats the full C:\ and D:\ executable searches (takes several minutes).
param([switch]$DriveScan)
$ErrorActionPreference = 'SilentlyContinue'
$out = Join-Path $PSScriptRoot 'machine_audit_12A_output.txt'
$A = 'C:\Program Files\ANSYS Inc'
$S = "$A\ANSYS Student\v261"
function W($t) { Add-Content -Path $out -Value $t -Encoding UTF8 }
Set-Content -Path $out -Value "Section 12A machine audit - run $(Get-Date -Format o) on $env:COMPUTERNAME" -Encoding UTF8

W "`n== 1. ANSYS root folders =="
Get-ChildItem $A | ForEach-Object { W ("{0}  {1:yyyy-MM-dd HH:mm}" -f $_.Name, $_.LastWriteTime) }
W "`n== 2. Student v261 identity =="
W ((Get-Content "$S\package.id") -join ' | ')
W ("v261 (non-Student) folder contents: " + ((Get-ChildItem "$A\v261" -Name) -join ', '))

W "`n== 3. LS-DYNA / LS-PrePost / LS-Run executables under $A =="
$exe = Get-ChildItem $A -Recurse -File -Include 'lsdyna*.exe','ls-dyna*.exe','lsprepost*.exe','lsrun*.exe','mppdyna*.exe','smpdyna*.exe'
if ($exe) { $exe | ForEach-Object { W $_.FullName } } else { W 'NONE FOUND' }
W ("Expected LS-PrePost path from installer config (ansys\bin\winx64\lsprepost413): exists = " + (Test-Path "$S\ansys\bin\winx64\lsprepost413"))
W ("ansys\bin\winx64 files matching dyna/lspp/prepost: " + ((Get-ChildItem "$S\ansys\bin\winx64" -File | Where-Object { $_.Name -match 'dyna|lspp|prepost' } | Select -Expand Name) -join ', '))

W "`n== 4. LS-DYNA integration components present (not solvers) =="
foreach ($p in @("$S\Addins\ACT\extensions\LSDYNA.wbex", "$S\Addins\ACT\extensions\LSDYNA\LSDynaSolverExtension.dll",
  "$S\Addins\ACT\extensions\LSDYNA\LSDYNAAnalysisTemplate.xml", "$S\Addins\ACT\extensions\keywordmanager\Ansys.ACTLSDYNA.KeywordLibrary.dll",
  "$S\commonfiles\WBAddinConfiguration\LSDYNAAddIn.xml", "$S\aisol\bin\winx64\LSDYNAParser.dll", "$S\SEC\SolverExecutionController\sec\plugins\lsdyna.py",
  "$S\commonfiles\launcherQT\src\RunLsdyna.py", "$S\installer\dev_configs\lsdyna\config_lsdyna.json",
  "$S\ansys\docu\LS-DYNA_Manual_Vol_I_R16.pdf", "$S\ansys\docu\LS-DYNA_Manual_Vol_II_R16.pdf", "$S\ansys\docu\LS-DYNA_Manual_Vol_III_R16.pdf",
  "$S\tp\MPI\WindowsHPC\mat_pie_lin_pla.k", "$S\optiSLang\examples\simple_car\reference\simplecar.k")) {
  $i = Get-Item $p; if ($i) { W ("{0}  {1} bytes  {2:yyyy-MM-dd}" -f $p, $i.Length, $i.LastWriteTime) } else { W "$p  MISSING" } }
$act = Select-String -Path "$env:APPDATA\Ansys\v261\UserRegFiles_*\ACTPreferences.xml" -Pattern 'ACT_DefaultExtensions'
W ("ACT default-extension list contains LSDYNA: " + [bool]($act.Line -match '1;LSDYNA;'))

W "`n== 5. Student installation product selection (install.log header) =="
Get-Content "$A\ANSYS Student\install.log" | Select-Object -Skip 14 -First 38 | ForEach-Object { W $_ }

W "`n== 6. Licensing evidence =="
foreach ($n in 'LSTC_LICENSE','ANSYSLMD_LICENSE_FILE','ANSYSLIC_DIR','AWP_ROOT261','ANSYS261_DIR','LSTC_LICENSE_SERVER','LSTC_FILE') {
  W ("{0} : machine='{1}' user='{2}'" -f $n, [Environment]::GetEnvironmentVariable($n,'Machine'), [Environment]::GetEnvironmentVariable($n,'User')) }
W ("Shared Files\Licensing\license_files: " + ((Get-ChildItem "$A\Shared Files\Licensing\license_files" -Recurse -Name) -join ', '))
W ("ansyslmd.ini present: " + (Test-Path "$A\Shared Files\Licensing\ansyslmd.ini"))
Get-Service | Where-Object { $_.DisplayName -match 'ANSYS|FlexNet|LSTC' } | ForEach-Object { W ("service: {0} | {1} | {2}" -f $_.DisplayName, $_.Status, $_.StartType) }
W 'License Manager install log (2026-10-01) header:'
Get-Content "$A\install.log" | Select-Object -First 12 | ForEach-Object { W $_ }

W "`n== 7. Hardware =="
$c = Get-CimInstance Win32_Processor; W ("CPU: {0}; cores {1}; logical {2}" -f $c.Name, $c.NumberOfCores, $c.NumberOfLogicalProcessors)
$cs = Get-CimInstance Win32_ComputerSystem; $os = Get-CimInstance Win32_OperatingSystem
W ("RAM total {0:N2} GB; free at audit {1:N2} GB; OS {2} {3}" -f ($cs.TotalPhysicalMemory/1GB), ($os.FreePhysicalMemory/1MB), $os.Caption, $os.Version)
Get-PSDrive -PSProvider FileSystem | ForEach-Object { W ("drive {0}: free {1:N1} GB" -f $_.Name, ($_.Free/1GB)) }
Get-CimInstance Win32_VideoController | ForEach-Object { W ("GPU: " + $_.Name) }

W "`n== 8. Keyword files in the project =="
$k = Get-ChildItem (Split-Path (Split-Path $PSScriptRoot)) -Recurse -File -Include '*.k','*.key','*.dyn','d3plot*','d3eigv*','binout*'
if ($k) { $k | ForEach-Object { W $_.FullName } } else { W 'NONE FOUND' }

if ($DriveScan) {
  W "`n== 9. Full-drive executable search =="
  foreach ($d in 'C:\','D:\') { $r = cmd /c "dir ${d}*lsdyna*.exe ${d}*ls-dyna*.exe ${d}*lsprepost*.exe ${d}*lsrun*.exe /s /b /a-d 2>&1"; W "$d -> $($r -join '; ')" }
} else { W "`n== 9. Full-drive search not repeated in this run; see raw\ for the 2026-10-02 results ==" }
W "`nEND"
