@echo off
REM Windows batch file for running T-Junction simulation via WSL
REM 
REM Prerequisites:
REM   1. WSL2 installed with Ubuntu
REM   2. OpenFOAM installed in WSL
REM
REM Usage: Double-click this file or run from Command Prompt

echo ==========================================
echo T-Junction Microfluidic Simulation
echo ==========================================
echo.

REM Check if WSL is available
where wsl >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: WSL is not installed.
    echo Please install WSL2 first. See WINDOWS_SETUP.md for instructions.
    pause
    exit /b 1
)

echo Running simulation via WSL...
echo.

REM Get the current directory and convert to WSL path
set "WINPATH=%~dp0"
set "WSLPATH=%WINPATH:\=/%"
set "WSLPATH=%WSLPATH:C:=/mnt/c%"

REM Run the simulation via WSL
wsl bash -c "cd '%WSLPATH%' && sed -i 's/\r$//' Allrun Allclean 2>/dev/null; chmod +x Allrun && source /opt/openfoam11/etc/bashrc 2>/dev/null || source /opt/openfoam/openfoam2306/etc/bashrc 2>/dev/null || source /usr/lib/openfoam/openfoam2306/etc/bashrc 2>/dev/null; ./Allrun"

echo.
echo ==========================================
echo Simulation complete!
echo ==========================================
echo.
echo View results with ParaView:
echo   wsl paraview VTK/tjunction_2d.vtk.series
echo.
pause


