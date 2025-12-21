@echo off
REM Start the Microfluidic Simulation Web Application (Windows via WSL)

echo ==========================================
echo   Microfluidic Simulation Web App
echo ==========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

echo Starting webapp via WSL...
echo.

REM Convert Windows path to WSL path
for /f "delims=" %%i in ('wsl wslpath -a "%SCRIPT_DIR%"') do set WSL_PATH=%%i

REM Run the startup script in WSL
wsl bash -c "cd '%WSL_PATH%' && chmod +x start_webapp.sh && ./start_webapp.sh"

