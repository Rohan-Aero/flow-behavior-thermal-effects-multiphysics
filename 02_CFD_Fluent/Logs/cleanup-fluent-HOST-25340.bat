echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\tell.exe" HOST 49729 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 9568) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 2940) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 14992) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 23604) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 25340) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 7648)
del "<PROJECT_ROOT>\05_Meshing\cleanup-fluent-HOST-25340.bat"
