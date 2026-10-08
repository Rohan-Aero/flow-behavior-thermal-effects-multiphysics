# Post-process every finished 12C case (done.txt present, no series yet), then print status.
$B = Split-Path $PSScriptRoot -Parent
$py = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\commonfiles\CPython\3_10\winx64\Release\python\python.exe'
foreach ($c in 'C5_A1p2','C0_A0p0','C1_A0p1','C2_A0p3','C3_A0p6','C4_A0p9','N1_A0p1_halfstep') {
  if ((Test-Path "$B\runs\$c\done.txt") -and !(Test-Path "$B\results\series\$($c)_series.csv")) {
    "PROCESSED: " + ((& $py "$PSScriptRoot\post_12C_case.py" "$B\runs\$c" 2>&1 | Select -Last 1) -replace ', "iterations_per_step".*', '}')
  }
}
& "$PSScriptRoot\status_12C.ps1"
