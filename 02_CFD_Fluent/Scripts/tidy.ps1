$ErrorActionPreference = 'SilentlyContinue'
$b  = '<PROJECT_ROOT>\05_Meshing'
$lg = Join-Path $b 'Logs'
New-Item -ItemType Directory -Path $lg -Force | Out-Null
foreach ($pat in @('*.trn', 'fluent-*-error.log', 'cleanup-fluent-*.bat')) {
    Get-ChildItem $b -Filter $pat -File | ForEach-Object {
        Move-Item $_.FullName (Join-Path $lg $_.Name) -Force
        Write-Output ('moved -> Logs\' + $_.Name)
    }
}
$old = Join-Path $b 'Mesh_Quality\fluent_mesh_check.txt'
$new = Join-Path $b 'Mesh_Quality\SUPERSEDED_preflip_fluent_check.txt'
if (Test-Path $old) { Move-Item $old $new -Force; Write-Output 'renamed fluent_mesh_check.txt -> SUPERSEDED_preflip_fluent_check.txt' }
Get-ChildItem $b -File | Select-Object Name | Format-Table -AutoSize | Out-String
