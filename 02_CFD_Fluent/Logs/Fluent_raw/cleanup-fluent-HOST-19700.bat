echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\tell.exe" HOST 59367 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 24208) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 19700) 
if /i "%LOCALHOST%"=="HOST" (%KILL_CMD% 13900)
del "<PROJECT_ROOT>\06_Fluent_CFD\cleanup-fluent-HOST-19700.bat"
