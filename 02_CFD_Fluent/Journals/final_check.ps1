$r = '<PROJECT_ROOT>'
$b = Join-Path $r '06_Fluent_CFD'
Write-Output '--- T-018 / T-019 status ---'
Select-String -Path (Join-Path $r 'PROJECT_STATE.md') -Pattern 'T-019|T-018' |
    Select-Object -ExpandProperty Line
Write-Output ''
Write-Output '--- 06_Fluent_CFD tree ---'
Get-ChildItem $b -Recurse -File | Sort-Object FullName |
    ForEach-Object { '{0,12}  {1}' -f $_.Length, $_.FullName.Replace($b + '\', '') }
Write-Output ''
Write-Output '--- project root ---'
Get-ChildItem $r | Select-Object Name, @{n = 'Type'; e = { if ($_.PSIsContainer) { 'DIR' } else { 'file' } } } |
    Format-Table -AutoSize | Out-String
