$ErrorActionPreference = 'Continue'
$b = '<PROJECT_ROOT>\06_Fluent_CFD'
# the end-of-stage-2 checkpoint is a first-order intermediate: keep it, but label it for what it is
if (Test-Path (Join-Path $b 'Case\checkpoint.cas.h5')) {
    Move-Item (Join-Path $b 'Case\checkpoint.cas.h5') (Join-Path $b 'Case\intermediate_end_stage2_firstorder_iter300.cas.h5') -Force
    Write-Output 'renamed checkpoint case'
}
if (Test-Path (Join-Path $b 'Case\checkpoint.dat.h5')) {
    Move-Item (Join-Path $b 'Case\checkpoint.dat.h5') (Join-Path $b 'Data\intermediate_end_stage2_firstorder_iter300.dat.h5') -Force
    Write-Output 'moved checkpoint data to Data'
}
# the final mesh travels with the final case
Copy-Item '<PROJECT_ROOT>\05_Meshing\Mesh_Medium\medium.msh' (Join-Path $b 'Case\medium_mesh_used_for_baseline.msh') -Force
Write-Output 'copied medium.msh into Case'
# journals used by the official run, copied next to the monitors for the record
Get-ChildItem $b -Filter '*.trn' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $b ('Logs\Fluent_raw\' + $_.Name)) -Force }
Get-ChildItem $b -Filter 'cleanup-fluent-*.bat' -File | ForEach-Object { Move-Item $_.FullName (Join-Path $b ('Logs\Fluent_raw\' + $_.Name)) -Force }
Write-Output '--- tree ---'
foreach ($d in @('Baseline','Case','Data','Journals','Monitors','Profiles','Exports','Figures','Audit')) {
    Write-Output ('[' + $d + ']')
    Get-ChildItem (Join-Path $b $d) -File | ForEach-Object { '   {0,-58} {1,12}' -f $_.Name, $_.Length }
}
