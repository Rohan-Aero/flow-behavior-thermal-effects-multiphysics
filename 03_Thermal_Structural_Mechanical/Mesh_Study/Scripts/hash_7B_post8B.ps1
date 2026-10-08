# SECTION 8B (RE-ANALYSIS 2026) - integrity check of the official 7B project after the mesh study.
# Recomputes SHA-256 of every file listed in Mesh_Study/Audits/pre8B_7B_project_hashes.json (recorded before run A)
# plus any file that now exists in the 7B project but was not listed, and writes the comparison.
$ws = '<PROJECT_ROOT>\08_Structural_Analysis\Workbench'
$au = '<PROJECT_ROOT>\08_Structural_Analysis\Mesh_Study\Audits'
$pre = Get-Content "$au\pre8B_7B_project_hashes.json" -Raw | ConvertFrom-Json
$post = [ordered]@{}
$files = @(Get-Item "$ws\Flow_Behavior_Thermal_Effects_Structural_7B.wbpj") + @(Get-ChildItem "$ws\Flow_Behavior_Thermal_Effects_Structural_7B_files" -Recurse -File)
foreach ($f in $files) { $k = $f.FullName.Substring($ws.Length); $post[$k] = (Get-FileHash $f.FullName -Algorithm SHA256).Hash }
$post | ConvertTo-Json | Set-Content "$au\post8B_7B_project_hashes.json" -Encoding UTF8
$diff = @(); $missing = @(); $new = @()
foreach ($p in $pre.PSObject.Properties) {
  if (-not $post.Contains($p.Name)) { $missing += $p.Name }
  elseif ($post[$p.Name] -ne $p.Value) { $diff += $p.Name }
}
$preNames = @($pre.PSObject.Properties.Name)
foreach ($k in $post.Keys) { if ($preNames -notcontains $k) { $new += $k } }
$res = [ordered]@{ pre_files = $preNames.Count; post_files = $post.Count; changed = $diff; missing = $missing; not_in_pre_record = $new;
                   verdict = $(if ($diff.Count -eq 0 -and $missing.Count -eq 0) { 'IDENTICAL' } else { 'DIFFERENT' }) }
$res | ConvertTo-Json -Depth 4 | Set-Content "$au\hash_compare_7B_pre_post_8B.json" -Encoding UTF8
$res | ConvertTo-Json -Depth 4
