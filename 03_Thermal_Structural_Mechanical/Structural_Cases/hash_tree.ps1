param([string]$Root, [string]$Out)
# SHA-256 of every file under $Root (relative path, size, hash) -> $Out (CSV). RE-ANALYSIS 2026 integrity record.
$items = Get-ChildItem -Path $Root -Recurse -File | Sort-Object FullName
$rows = foreach ($f in $items) { [pscustomobject]@{ path = $f.FullName.Substring($Root.Length).TrimStart('\'); bytes = $f.Length; sha256 = (Get-FileHash $f.FullName -Algorithm SHA256).Hash } }
$rows | Export-Csv -Path $Out -NoTypeInformation -Encoding ascii
Write-Output ('hashed ' + $rows.Count + ' files under ' + $Root + ' -> ' + $Out)
