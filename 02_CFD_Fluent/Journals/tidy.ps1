$ErrorActionPreference = 'SilentlyContinue'
$b  = '<PROJECT_ROOT>\06_Fluent_CFD'
$lg = Join-Path $b 'Logs\Fluent_raw'
New-Item -ItemType Directory -Path $lg -Force | Out-Null
foreach ($pat in @('*.trn', 'cleanup-fluent-*.bat', 'fluent-*-error.log')) {
    Get-ChildItem $b -Filter $pat -File | ForEach-Object {
        Move-Item $_.FullName (Join-Path $lg $_.Name) -Force
        Write-Output ('moved -> Logs\Fluent_raw\' + $_.Name)
    }
}
Write-Output '--- 06_Fluent_CFD root now ---'
Get-ChildItem $b | Select-Object Name, @{n='Type';e={ if ($_.PSIsContainer) {'DIR'} else {'file'} }} |
    Format-Table -AutoSize | Out-String
