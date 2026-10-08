$ErrorActionPreference = 'SilentlyContinue'
$b = '<PROJECT_ROOT>\05_Meshing'
Write-Output '--- 05_Meshing tree ---'
Get-ChildItem $b -Recurse -File | Sort-Object FullName |
    ForEach-Object { '{0,10}  {1}' -f $_.Length, $_.FullName.Replace($b + '\', '') }
Write-Output ''
Write-Output '--- ns_dump.txt ---'
Get-Content (Join-Path $b 'Scripts\ns_dump.txt')
Write-Output ''
Write-Output '--- wb_build_log.txt ---'
Get-Content (Join-Path $b 'Scripts\wb_build_log.txt')
