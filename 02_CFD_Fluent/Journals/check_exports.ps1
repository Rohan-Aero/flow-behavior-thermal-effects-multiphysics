$b = '<PROJECT_ROOT>\06_Fluent_CFD'
foreach ($f in Get-ChildItem (Join-Path $b 'Exports') -Filter '*.csv') {
    $n = 0; $r = [System.IO.StreamReader]::new($f.FullName); $h = $r.ReadLine(); while ($null -ne $r.ReadLine()) { $n++ }; $r.Close()
    Write-Output ('{0,-22} {1,10} bytes {2,8} rows' -f $f.Name, $f.Length, $n)
    Write-Output ('   header: ' + $h.Substring(0, [Math]::Min(300, $h.Length)))
}
Write-Output '--- Case / Data ---'
Get-ChildItem (Join-Path $b 'Case'), (Join-Path $b 'Data') | ForEach-Object { '{0,-40} {1,12}' -f $_.Name, $_.Length }
Write-Output '--- Audit ---'
Get-ChildItem (Join-Path $b 'Audit') | ForEach-Object { '{0,-40} {1,10}' -f $_.Name, $_.Length }
Write-Output '--- fluent_flux_heat.txt ---'
Get-Content (Join-Path $b 'Audit\fluent_flux_heat.txt')
Write-Output '--- fluent_flux_mass.txt ---'
Get-Content (Join-Path $b 'Audit\fluent_flux_mass.txt')
