param([string]$Tag = 'A')
$b = '<PROJECT_ROOT>\06_Fluent_CFD'
Write-Output '--- export surface list ---'
Select-String -Path (Join-Path $b ('Logs\trial_' + $Tag + '_stdout.txt')) -Pattern "ascii export surfaces now" | Select-Object -ExpandProperty Line
Select-String -Path (Join-Path $b ('Logs\trial_' + $Tag + '_log.txt')) -Pattern "ascii export surfaces now" | Select-Object -ExpandProperty Line
Write-Output '--- residual file head / tail ---'
$rf = Join-Path $b ('Monitors\trial_' + $Tag + '_residuals.txt')
if (Test-Path $rf) { Get-Content $rf -TotalCount 12; Write-Output '...'; Get-Content $rf -Tail 4; Write-Output ('lines ' + (Get-Content $rf).Count) } else { Write-Output 'no residual file' }
Write-Output '--- T_solid_max every 10 iterations from iter 120 ---'
$mf = Join-Path $b ('Monitors\trial_' + $Tag + '.out')
$lines = Get-Content $mf
$hdr = $lines | Where-Object { $_ -like '("Iteration"*' }
Write-Output $hdr
$lines | Where-Object { $_ -match '^\d+\s' } | ForEach-Object {
    $t = $_ -split '\s+'
    $it = [int]$t[0]
    if (($it -ge 118 -and $it -le 126) -or ($it % 10 -eq 0)) { $_ }
}
