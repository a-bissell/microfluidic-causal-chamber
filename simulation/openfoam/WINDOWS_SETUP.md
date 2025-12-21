# Running OpenFOAM on Windows

OpenFOAM is primarily a Linux application. Here are your options for running it on Windows, listed from recommended to alternative approaches.

## Option 1: WSL2 (Recommended)

Windows Subsystem for Linux 2 is the best way to run OpenFOAM on Windows 10/11.

### Step 1: Install WSL2

Open PowerShell as Administrator and run:
```powershell
wsl --install
```

This installs Ubuntu by default. Restart your computer when prompted.

### Step 2: Install OpenFOAM in WSL

Open Ubuntu (from Start menu) and run:
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Add OpenFOAM repository
sudo sh -c "wget -O - https://dl.openfoam.org/gpg.key | apt-key add -"
sudo add-apt-repository "deb http://dl.openfoam.org/ubuntu $(lsb_release -sc) main"

# Install OpenFOAM v11 (or use openfoam2306 for ESI version)
sudo apt install openfoam11

# Source OpenFOAM environment
echo "source /opt/openfoam11/etc/bashrc" >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Access Your Files

Your Windows files are accessible at `/mnt/c/` in WSL:
```bash
# Navigate to your project
cd /mnt/c/Users/alexa/OneDrive/Documents/microfluidic-causal-chamber-main/microfluidic-causal-chamber-main

# Go to simulation directory
cd simulation/openfoam/tjunction_2d

# Run the simulation
chmod +x Allrun Allclean
./Allrun
```

### Step 4: Install ParaView

```bash
sudo apt install paraview
```

To run ParaView with GUI, you'll need an X server on Windows:
- Install **VcXsrv** or **X410** from Microsoft Store
- Set display: `export DISPLAY=:0`

---

## Option 2: Docker (Cross-Platform)

Docker provides a containerized OpenFOAM environment.

### Step 1: Install Docker Desktop

Download from: https://www.docker.com/products/docker-desktop

### Step 2: Pull OpenFOAM Image

```powershell
docker pull openfoam/openfoam11-paraview510
```

### Step 3: Run Container

```powershell
# Navigate to your case directory first
cd C:\Users\alexa\OneDrive\Documents\microfluidic-causal-chamber-main\microfluidic-causal-chamber-main\simulation\openfoam

# Run container with volume mount
docker run -it -v ${PWD}:/home/openfoam/work openfoam/openfoam11-paraview510

# Inside container:
cd work/tjunction_2d
./Allrun
```

---

## Option 3: Native Windows (blueCFD-Core)

blueCFD-Core provides a native Windows build of OpenFOAM.

### Step 1: Download and Install

1. Download from: http://bluecfd.github.io/Core/
2. Install to default location (e.g., `C:\Program Files\blueCFD-Core-2020`)

### Step 2: Use the Provided Windows Scripts

See the `Allrun.ps1` and `Allrun.bat` files created in the case directories.

### Step 3: Run from blueCFD Terminal

1. Open "blueCFD-Core Terminal" from Start menu
2. Navigate to case:
   ```bash
   cd /c/Users/alexa/OneDrive/Documents/microfluidic-causal-chamber-main/microfluidic-causal-chamber-main/simulation/openfoam/tjunction_2d
   ./Allrun
   ```

---

## Comparison of Options

| Feature | WSL2 | Docker | blueCFD |
|---------|------|--------|---------|
| Setup complexity | Medium | Medium | Easy |
| Performance | Excellent | Good | Good |
| Disk usage | ~2 GB | ~5 GB | ~3 GB |
| GUI support | Needs X server | Limited | Native |
| Recommended for | Daily use | CI/CD, portability | Quick testing |

---

## Troubleshooting

### "Permission denied" in WSL
```bash
chmod +x Allrun Allclean
```

### Line ending issues (CRLF vs LF)
If scripts fail with strange errors, convert line endings:
```bash
sed -i 's/\r$//' Allrun Allclean
```

Or use dos2unix:
```bash
sudo apt install dos2unix
dos2unix Allrun Allclean
```

### ParaView display issues in WSL
```bash
# Install X server on Windows (VcXsrv)
# Then in WSL:
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
export LIBGL_ALWAYS_INDIRECT=1
paraview
```

### Docker: "Cannot connect to Docker daemon"
Make sure Docker Desktop is running before using docker commands.

