# 12C protection audit (read-only). Hashes the protected files and compares them with the SHA-256 prefixes recorded in 12B
# (LS_DYNA_GATE_STATUS_12B.md); lists every file outside 15_LS_DYNA_Extension changed after the end of 12B
# (PROJECT_STATE.md written 2026-10-03 01:36:52 local). Writes audit\hash_audit_12C.csv and audit\changed_outside_12C.txt.
$P = '<PROJECT_ROOT>'; $O = "$PSScriptRoot"
$exp = [ordered]@{
  'report PDF' = @('13_Report', '*.pdf', '7F8F32AD'); 'report DOCX' = @('13_Report', '*.docx', '2D40820C')
  'presentation PPTX' = @('14_Presentation', '*.pptx', '02EAB433'); 'MASTER_PROJECT_DATA.csv' = @('.', 'MASTER_PROJECT_DATA.csv', '727ADD0A')
  'Fluent baseline case' = @('06_Fluent_CFD', 'baseline_medium_final*.cas*', '84D6511B'); 'Fluent baseline data' = @('06_Fluent_CFD', 'baseline_medium_final*.dat*', 'F05837C5')
  'LC2 solver deck' = @('08_Structural_Analysis', 'LC2_solve_input_ds.dat', '51D80678'); 's7b_nodal.csv' = @('08_Structural_Analysis', 's7b_nodal.csv', 'DC650A0C')
  's8a_mode1.csv' = @('08_Structural_Analysis', 's8a_mode1.csv', 'A5FDC844'); 'BUCKLING_RESULTS.md' = @('08_Structural_Analysis', 'BUCKLING_RESULTS.md', '5BABD2DC') }
$rows = foreach ($k in $exp.Keys) {
  $d, $pat, $pre = $exp[$k]
  $hit = $null
  foreach ($f in Get-ChildItem (Join-Path $P $d) -Recurse -File -Filter $pat -EA SilentlyContinue) {
    $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
    if ($h.StartsWith($pre)) { $hit = [pscustomobject]@{Item=$k; Expected_prefix=$pre; SHA256=$h; Match='UNCHANGED'; Path=$f.FullName.Substring($P.Length+1); Bytes=$f.Length; LastWrite=$f.LastWriteTime.ToString('s')}; break }
  }
  if (!$hit) { $hit = [pscustomobject]@{Item=$k; Expected_prefix=$pre; SHA256=''; Match='NO FILE WITH RECORDED HASH FOUND'; Path="$d\$pat"; Bytes=''; LastWrite=''} }
  $hit
}
$rows | Export-Csv "$O\hash_audit_12C.csv" -NoTypeInformation
$cut = [datetime]'2026-10-03T01:36:53'
$chg = Get-ChildItem $P -Recurse -File -EA SilentlyContinue | ? { $_.LastWriteTime -gt $cut -and $_.FullName -notlike "$P\15_LS_DYNA_Extension\*" }
"Files outside 15_LS_DYNA_Extension changed after $($cut.ToString('s')) (end of 12B): $(@($chg).Count)" | Out-File "$O\changed_outside_12C.txt"
$chg | % { "$($_.LastWriteTime.ToString('s'))  $($_.FullName.Substring($P.Length+1))" } | Out-File "$O\changed_outside_12C.txt" -Append
$rows | ft Item, Match, @{n='SHA';e={$_.SHA256.Substring(0,[Math]::Min(16,$_.SHA256.Length))}}, Path -auto | Out-String -Width 220
Get-Content "$O\changed_outside_12C.txt"
$E = "$P\15_LS_DYNA_Extension"
$chg2 = Get-ChildItem $E -Recurse -File -EA SilentlyContinue | ? { $_.LastWriteTime -gt $cut -and $_.FullName -notlike "$E\12C_Nonlinear_Buckling\*" }
"Files in 15_LS_DYNA_Extension outside 12C_Nonlinear_Buckling (12A/12B files) changed after $($cut.ToString('s')): $(@($chg2).Count)" | Out-File "$O\changed_outside_12C.txt" -Append
$chg2 | % { "$($_.LastWriteTime.ToString('s'))  $($_.FullName.Substring($P.Length+1))" } | Out-File "$O\changed_outside_12C.txt" -Append
Get-Content "$O\changed_outside_12C.txt" | Select -Last (1 + @($chg2).Count)
