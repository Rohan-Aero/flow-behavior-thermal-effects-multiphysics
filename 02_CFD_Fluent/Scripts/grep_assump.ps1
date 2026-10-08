$r = '<PROJECT_ROOT>'
$files = @(
  "$r\01_Requirements\ASSUMPTIONS.md",
  "$r\01_Requirements\ENGINEERING_REQUIREMENTS.md",
  "$r\02_Engineering_Calculations\ENGINEERING_THEORY.md"
)
foreach ($f in $files) {
  Write-Output ('########## ' + (Split-Path $f -Leaf) + ' ##########')
  Select-String -Path $f -Pattern 'turbulen|intensit|gravit|buoyan|Richardson|Grashof|radiat|backflow|outlet|pressure-based|density-based|steady|SST|k-omega|k-w|y\+|wall function|operating pressure|incompressible|ideal gas|adiabatic|roughness|smooth' |
    ForEach-Object { '{0,5}: {1}' -f $_.LineNumber, $_.Line.Trim() }
  Write-Output ''
}
