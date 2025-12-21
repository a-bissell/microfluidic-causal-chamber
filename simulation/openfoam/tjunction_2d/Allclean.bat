@echo off
REM Windows batch file for cleaning T-Junction simulation
REM Usage: Double-click this file or run from Command Prompt

echo Cleaning T-Junction case...

REM Get the current directory and convert to WSL path
set "WINPATH=%~dp0"
set "WSLPATH=%WINPATH:\=/%"
set "WSLPATH=%WSLPATH:C:=/mnt/c%"

REM Clean via WSL
wsl bash -c "cd '%WSLPATH%' && chmod +x Allclean && ./Allclean"

echo Done.
pause


