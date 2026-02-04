@echo off
echo Configuring Windows for safe 24/7 operation...

:: Disable hibernate and sleep
powercfg -h off
powercfg -change -standby-timeout-ac 0
powercfg -change -hibernate-timeout-ac 0
powercfg -change -monitor-timeout-ac 0

:: Limit CPU max usage to 85% (thermal protection)
powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 85
powercfg -setactive SCHEME_CURRENT

:: Force Balanced plan
powercfg /setactive SCHEME_BALANCED

:: Disable Fast Startup
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" ^
 /v HiberbootEnabled /t REG_DWORD /d 0 /f

:: Reduce background load
sc stop SysMain
sc config SysMain start=disabled

:: Auto reboot on crash
wmic recoveros set AutoReboot=True

echo Done. Reboot the system.
pause
