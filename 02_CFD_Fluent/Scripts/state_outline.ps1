$f = '<PROJECT_ROOT>\PROJECT_STATE.md'
Write-Output ('bytes: ' + (Get-Item $f).Length)
Write-Output ('lines: ' + (Get-Content $f).Count)
Select-String -Path $f -Pattern '^#{1,3} ' | ForEach-Object { '{0,5}: {1}' -f $_.LineNumber, $_.Line }
Write-Output '--- open tasks ---'
Select-String -Path $f -Pattern 'T-0\d\d' | ForEach-Object { '{0,5}: {1}' -f $_.LineNumber, $_.Line.Trim() }
