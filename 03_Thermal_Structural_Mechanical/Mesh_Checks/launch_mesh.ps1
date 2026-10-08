# Detached launch of param_mesh.py with the ANSYS-bundled CPython 3.10 (the Section 4 interpreter).
# RE-ANALYSIS 2026.
$mc = '<PROJECT_ROOT>\10_Parametric_Study\Mesh_Checks'
$py = 'C:\Program Files\ANSYS Inc\ANSYS Student\v261\commonfiles\CPython\3_10\winx64\Release\python\python.exe'
$cmd = 'cmd.exe /c ""' + $py + '" "' + $mc + '\param_mesh.py" > "' + $mc + '\param_mesh_stdout.txt" 2>&1"'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $mc }
Write-Output ('Win32_Process.Create return=' + $r.ReturnValue + ' pid=' + $r.ProcessId)
