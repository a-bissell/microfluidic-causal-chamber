@echo off
REM Windows batch file for cleaning 3D T-Junction simulation

echo Cleaning 3D T-Junction case...

set "WINPATH=%~dp0"
set "WSLPATH=%WINPATH:\=/%"
set "WSLPATH=%WSLPATH:C:=/mnt/c%"

wsl bash -c "cd '%WSLPATH%' && chmod +x Allclean && ./Allclean"

echo Done.
pause


