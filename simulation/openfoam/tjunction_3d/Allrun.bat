@echo off
REM Windows batch file for running 3D T-Junction simulation via WSL

echo ==========================================
echo 3D T-Junction Microfluidic Simulation
echo ==========================================
echo.

where wsl >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: WSL is not installed.
    pause
    exit /b 1
)

set "WINPATH=%~dp0"
set "WSLPATH=%WINPATH:\=/%"
set "WSLPATH=%WSLPATH:C:=/mnt/c%"

wsl bash -c "cd '%WSLPATH%' && sed -i 's/\r$//' Allrun Allclean 2>/dev/null; chmod +x Allrun && source /opt/openfoam11/etc/bashrc 2>/dev/null || source /opt/openfoam/openfoam2306/etc/bashrc 2>/dev/null; ./Allrun"

echo.
echo Simulation complete!
pause


