$ErrorActionPreference = 'SilentlyContinue'
$b = '<PROJECT_ROOT>\05_Meshing'
Write-Output ('complete: ' + (Test-Path (Join-Path $b 'Mesh_Quality\_check_complete.txt')))
Write-Output ('fluentprocs: ' + (@(Get-Process -Name fluent,fl_mpi2610,cortex)).Count)
Write-Output '--- Mesh_Quality ---'
Get-ChildItem (Join-Path $b 'Mesh_Quality') -File | Select-Object Name,LastWriteTime,Length | Format-Table -AutoSize | Out-String -Width 120
Write-Output '--- meshes ---'
Get-ChildItem (Join-Path $b 'Mesh_Coarse'),(Join-Path $b 'Mesh_Medium'),(Join-Path $b 'Mesh_Fine') -File | Select-Object Name,LastWriteTime,Length | Format-Table -AutoSize | Out-String -Width 120
Write-Output '--- Scripts ---'
Get-ChildItem (Join-Path $b 'Scripts') -File | Select-Object Name,LastWriteTime,Length | Format-Table -AutoSize | Out-String -Width 120
