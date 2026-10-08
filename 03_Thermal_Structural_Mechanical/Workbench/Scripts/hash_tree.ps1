param([string]$Root, [string]$Out)
# Section 7A: SHA-256 of every file under $Root -> JSON ($Out). Used before/after the build to prove that the
# Section 4 Workbench project and the official Fluent case/data are not modified.
$items = @()
Get-ChildItem $Root -Recurse -File | Sort-Object FullName | ForEach-Object {
  $items += [ordered]@{ file = $_.FullName.Substring($Root.Length).TrimStart('\'); bytes = $_.Length; mtime = $_.LastWriteTime.ToString('s'); sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash }
}
[ordered]@{ root = $Root; taken = (Get-Date).ToString('s'); count = $items.Count; files = $items } | ConvertTo-Json -Depth 5 | Out-File -FilePath $Out -Encoding utf8
Write-Output ("hashed " + $items.Count + " files under " + $Root)
