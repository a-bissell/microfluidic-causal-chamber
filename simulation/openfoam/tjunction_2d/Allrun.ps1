# PowerShell script for running T-Junction simulation
# For use with blueCFD-Core or WSL OpenFOAM
#
# Usage (WSL): wsl bash ./Allrun
# Usage (blueCFD): Run from blueCFD terminal: ./Allrun

Write-Host "=========================================="
Write-Host "T-Junction Microfluidic Simulation"
Write-Host "=========================================="
Write-Host ""

# Check if running in WSL context
$useWSL = $true

if ($useWSL) {
    Write-Host "Running via WSL..."
    Write-Host ""
    
    # Get WSL path
    $windowsPath = (Get-Location).Path
    $wslPath = $windowsPath -replace '\\', '/' -replace 'C:', '/mnt/c'
    
    # Run commands through WSL
    $commands = @"
cd '$wslPath'

# Source OpenFOAM (try different locations)
if [ -f /opt/openfoam11/etc/bashrc ]; then
    source /opt/openfoam11/etc/bashrc
elif [ -f /opt/openfoam/openfoam2306/etc/bashrc ]; then
    source /opt/openfoam/openfoam2306/etc/bashrc
elif [ -f /usr/lib/openfoam/openfoam2306/etc/bashrc ]; then
    source /usr/lib/openfoam/openfoam2306/etc/bashrc
else
    echo "ERROR: OpenFOAM not found. Please install OpenFOAM in WSL."
    exit 1
fi

echo "Using OpenFOAM from: `$WM_PROJECT_DIR"
echo ""

# Fix line endings if needed
sed -i 's/\r$//' Allrun Allclean 2>/dev/null || true

# Run the bash script
chmod +x Allrun
./Allrun
"@
    
    # Execute via WSL
    wsl bash -c $commands
}
else {
    Write-Host "ERROR: Native Windows execution not supported."
    Write-Host "Please use one of the following options:"
    Write-Host "  1. WSL2 (recommended): wsl bash ./Allrun"
    Write-Host "  2. Docker: See WINDOWS_SETUP.md"
    Write-Host "  3. blueCFD-Core: Run from blueCFD terminal"
}

Write-Host ""
Write-Host "Done."


