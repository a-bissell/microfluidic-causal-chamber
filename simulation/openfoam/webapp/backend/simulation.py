"""
OpenFOAM Simulation Manager

Handles:
- Case creation from template
- Running simulations as subprocesses
- Monitoring progress
- Parsing results
"""

import os
import re
import asyncio
import shutil
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from pydantic import BaseModel


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""
    p_cont: float = 50000
    p_disp: float = 30000
    end_time: float = 0.05
    write_interval: float = 0.001
    nu_oil: float = 5e-5
    nu_water: float = 1e-6
    sigma: float = 0.03


@dataclass
class SimulationState:
    """Current state of a simulation."""
    case_id: str
    case_dir: Path
    config: SimulationConfig
    status: str = "created"  # created, meshing, running, completed, failed
    progress: float = 0.0
    current_time: float = 0.0
    courant_number: Optional[float] = None
    process: Optional[asyncio.subprocess.Process] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    error_message: str = ""


class SimulationManager:
    """Manages OpenFOAM simulation cases."""
    
    def __init__(self, cases_dir: Path, template_dir: Path):
        self.cases_dir = Path(cases_dir)
        self.template_dir = Path(template_dir)
        self.simulations: Dict[str, SimulationState] = {}
        self.sweeps: Dict[str, Dict] = {}
        
        # OpenFOAM environment
        self.openfoam_source = self._find_openfoam_bashrc()
    
    def _find_openfoam_bashrc(self) -> Optional[str]:
        """Find OpenFOAM bashrc file."""
        possible_paths = [
            "/opt/openfoam11/etc/bashrc",
            "/opt/openfoam/openfoam2306/etc/bashrc",
            "/usr/lib/openfoam/openfoam2306/etc/bashrc",
            str(Path.home() / "OpenFOAM/OpenFOAM-11/etc/bashrc"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def check_openfoam(self) -> bool:
        """Check if OpenFOAM is available."""
        return self.openfoam_source is not None
    
    def get_active_count(self) -> int:
        """Get number of active simulations."""
        return sum(1 for s in self.simulations.values() if s.status == "running")
    
    async def create_case(self, params) -> str:
        """Create a new simulation case from template."""
        case_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        case_dir = self.cases_dir / case_id
        
        # Copy template
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
        
        shutil.copytree(self.template_dir, case_dir)
        
        # Create config
        config = SimulationConfig(
            p_cont=params.p_cont,
            p_disp=params.p_disp,
            end_time=params.end_time,
            write_interval=params.write_interval,
            nu_oil=getattr(params, 'nu_oil', 5e-5),
            nu_water=getattr(params, 'nu_water', 1e-6),
            sigma=getattr(params, 'sigma', 0.03),
        )
        
        # Modify case files
        self._update_pressure_bc(case_dir, config)
        self._update_control_dict(case_dir, config)
        self._update_transport_properties(case_dir, config)
        
        # Store simulation state
        self.simulations[case_id] = SimulationState(
            case_id=case_id,
            case_dir=case_dir,
            config=config,
            status="created"
        )
        
        return case_id
    
    def _update_pressure_bc(self, case_dir: Path, config: SimulationConfig):
        """Update pressure boundary conditions in 0/p_rgh."""
        p_rgh_file = case_dir / "0" / "p_rgh"
        if not p_rgh_file.exists():
            return
        
        content = p_rgh_file.read_text()
        
        # Update oil_inlet pressure
        content = re.sub(
            r'(oil_inlet\s*\{[^}]*p0\s+uniform\s+)\d+',
            f'\\g<1>{int(config.p_cont)}',
            content
        )
        content = re.sub(
            r'(oil_inlet\s*\{[^}]*value\s+uniform\s+)\d+',
            f'\\g<1>{int(config.p_cont)}',
            content
        )
        
        # Update water_inlet pressure
        content = re.sub(
            r'(water_inlet\s*\{[^}]*p0\s+uniform\s+)\d+',
            f'\\g<1>{int(config.p_disp)}',
            content
        )
        content = re.sub(
            r'(water_inlet\s*\{[^}]*value\s+uniform\s+)\d+',
            f'\\g<1>{int(config.p_disp)}',
            content
        )
        
        p_rgh_file.write_text(content)
    
    def _update_control_dict(self, case_dir: Path, config: SimulationConfig):
        """Update controlDict with simulation parameters."""
        control_file = case_dir / "system" / "controlDict"
        if not control_file.exists():
            return
        
        content = control_file.read_text()
        
        # Update endTime
        content = re.sub(
            r'(endTime\s+)\S+;',
            f'\\g<1>{config.end_time};',
            content
        )
        
        # Update writeInterval
        content = re.sub(
            r'(writeInterval\s+)\S+;',
            f'\\g<1>{config.write_interval};',
            content
        )
        
        control_file.write_text(content)
    
    def _update_transport_properties(self, case_dir: Path, config: SimulationConfig):
        """Update fluid properties."""
        # For OpenFOAM 11, properties are in physicalProperties files
        # But we'll keep template values for simplicity
        pass
    
    async def run_simulation(self, case_id: str, ws_manager=None):
        """Run the simulation as a subprocess."""
        if case_id not in self.simulations:
            return
        
        sim = self.simulations[case_id]
        sim.status = "meshing"
        sim.start_timestamp = datetime.now()
        
        try:
            # Build the command script
            script = f"""
source {self.openfoam_source}
cd {sim.case_dir}

# Clean if needed
rm -rf constant/polyMesh 0/cellToRegion [1-9]* 0.[0-9]* 2>/dev/null || true

# Generate mesh
blockMesh > log.blockMesh 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: blockMesh failed"
    exit 1
fi

# Set initial fields
rm -f 0/alpha.water
cp 0/alpha.water.orig 0/alpha.water 2>/dev/null || true
setFields > log.setFields 2>&1

# Run solver
foamRun -solver incompressibleVoF > log.foamRun 2>&1 &
SOLVER_PID=$!

# Wait for solver
wait $SOLVER_PID
EXIT_CODE=$?

# Post-process if successful
if [ $EXIT_CODE -eq 0 ]; then
    foamToVTK > log.foamToVTK 2>&1
fi

exit $EXIT_CODE
"""
            
            # Run the script
            sim.status = "running"
            process = await asyncio.create_subprocess_shell(
                f"bash -c '{script}'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(sim.case_dir)
            )
            sim.process = process
            
            # Monitor progress in background
            asyncio.create_task(self._monitor_progress(case_id, ws_manager))
            
            # Wait for completion
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                sim.status = "completed"
                sim.progress = 1.0
            else:
                sim.status = "failed"
                sim.error_message = stderr.decode() if stderr else "Unknown error"
            
        except Exception as e:
            sim.status = "failed"
            sim.error_message = str(e)
        
        sim.end_timestamp = datetime.now()
        sim.process = None
        
        # Notify via WebSocket
        if ws_manager:
            await ws_manager.broadcast(case_id, {
                "type": "status",
                "status": sim.status,
                "progress": sim.progress,
                "message": sim.error_message or "Simulation complete"
            })
    
    async def _monitor_progress(self, case_id: str, ws_manager=None):
        """Monitor simulation progress by parsing log file."""
        if case_id not in self.simulations:
            return
        
        sim = self.simulations[case_id]
        log_file = sim.case_dir / "log.foamRun"
        
        last_time = 0.0
        
        while sim.status == "running":
            await asyncio.sleep(1)
            
            if log_file.exists():
                try:
                    content = log_file.read_text()
                    
                    # Parse current time
                    time_matches = re.findall(r'Time = (\d+\.?\d*)', content)
                    if time_matches:
                        current_time = float(time_matches[-1])
                        if current_time != last_time:
                            last_time = current_time
                            sim.current_time = current_time
                            sim.progress = min(current_time / sim.config.end_time, 1.0)
                    
                    # Parse Courant number
                    co_matches = re.findall(r'Courant Number mean: [\d.]+ max: ([\d.]+)', content)
                    if co_matches:
                        sim.courant_number = float(co_matches[-1])
                    
                    # Send update via WebSocket
                    if ws_manager:
                        await ws_manager.broadcast(case_id, {
                            "type": "progress",
                            "current_time": sim.current_time,
                            "end_time": sim.config.end_time,
                            "progress": sim.progress,
                            "courant_number": sim.courant_number
                        })
                        
                except Exception:
                    pass
    
    async def stop_simulation(self, case_id: str) -> bool:
        """Stop a running simulation."""
        if case_id not in self.simulations:
            return False
        
        sim = self.simulations[case_id]
        if sim.process and sim.status == "running":
            sim.process.terminate()
            await sim.process.wait()
            sim.status = "stopped"
            sim.process = None
            return True
        return False
    
    def get_status(self, case_id: str) -> Optional[Dict]:
        """Get status of a simulation."""
        if case_id not in self.simulations:
            return None
        
        sim = self.simulations[case_id]
        return {
            "case_id": case_id,
            "status": sim.status,
            "progress": sim.progress,
            "current_time": sim.current_time,
            "end_time": sim.config.end_time,
            "courant_number": sim.courant_number,
            "message": sim.error_message
        }
    
    def get_results(self, case_id: str) -> Optional[Dict]:
        """Get results from a completed simulation."""
        if case_id not in self.simulations:
            return None
        
        sim = self.simulations[case_id]
        times = self.get_output_times(case_id)
        
        return {
            "case_id": case_id,
            "status": sim.status,
            "parameters": {
                "p_cont": sim.config.p_cont,
                "p_disp": sim.config.p_disp,
                "end_time": sim.config.end_time
            },
            "output_times": times,
            "case_dir": str(sim.case_dir)
        }
    
    def get_output_times(self, case_id: str) -> List[float]:
        """Get list of output time directories."""
        if case_id not in self.simulations:
            return []
        
        sim = self.simulations[case_id]
        times = []
        
        for item in sim.case_dir.iterdir():
            if item.is_dir():
                try:
                    t = float(item.name)
                    if t > 0:
                        times.append(t)
                except ValueError:
                    continue
        
        return sorted(times)
    
    def get_field_data(self, case_id: str, time_step: float, field: str) -> Optional[Dict]:
        """Get field data for visualization."""
        if case_id not in self.simulations:
            return None
        
        sim = self.simulations[case_id]
        vtk_dir = sim.case_dir / "VTK"
        
        if not vtk_dir.exists():
            return None
        
        # Find VTK file for this time step
        # VTK files are named like case_<time>.vtk
        vtk_files = list(vtk_dir.glob("*.vtk"))
        
        # Return file path for frontend to fetch
        return {
            "case_id": case_id,
            "time_step": time_step,
            "field": field,
            "vtk_files": [str(f.name) for f in vtk_files]
        }
    
    def get_logs(self, case_id: str, lines: int = 100) -> List[str]:
        """Get recent log lines."""
        if case_id not in self.simulations:
            return []
        
        sim = self.simulations[case_id]
        log_file = sim.case_dir / "log.foamRun"
        
        if not log_file.exists():
            # Try other logs
            for log_name in ["log.blockMesh", "log.setFields"]:
                alt_log = sim.case_dir / log_name
                if alt_log.exists():
                    log_file = alt_log
                    break
        
        if not log_file.exists():
            return []
        
        try:
            content = log_file.read_text()
            log_lines = content.split('\n')
            return log_lines[-lines:]
        except Exception:
            return []
    
    def list_cases(self) -> List[Dict]:
        """List all simulation cases."""
        cases = []
        for case_id, sim in self.simulations.items():
            cases.append({
                "case_id": case_id,
                "status": sim.status,
                "created": sim.start_timestamp.isoformat() if sim.start_timestamp else None,
                "p_cont": sim.config.p_cont,
                "p_disp": sim.config.p_disp
            })
        return cases
    
    def delete_case(self, case_id: str) -> bool:
        """Delete a simulation case."""
        if case_id not in self.simulations:
            return False
        
        sim = self.simulations[case_id]
        
        # Don't delete running simulations
        if sim.status == "running":
            return False
        
        # Delete files
        if sim.case_dir.exists():
            shutil.rmtree(sim.case_dir)
        
        del self.simulations[case_id]
        return True
    
    async def create_sweep(self, config) -> str:
        """Create a parametric sweep."""
        sweep_id = f"sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        self.sweeps[sweep_id] = {
            "id": sweep_id,
            "config": config,
            "cases": [],
            "completed": 0,
            "total": len(config.p_cont_values) * len(config.p_disp_values),
            "status": "created"
        }
        
        return sweep_id
    
    async def run_sweep(self, sweep_id: str, ws_manager=None):
        """Run all simulations in a parametric sweep."""
        if sweep_id not in self.sweeps:
            return
        
        sweep = self.sweeps[sweep_id]
        sweep["status"] = "running"
        config = sweep["config"]
        
        for p_cont in config.p_cont_values:
            for p_disp in config.p_disp_values:
                # Create and run case
                params = type('Params', (), {
                    'p_cont': p_cont,
                    'p_disp': p_disp,
                    'end_time': config.end_time,
                    'write_interval': 0.001
                })()
                
                case_id = await self.create_case(params)
                sweep["cases"].append(case_id)
                
                await self.run_simulation(case_id, ws_manager)
                sweep["completed"] += 1
                
                if ws_manager:
                    await ws_manager.broadcast(f"sweep_{sweep_id}", {
                        "type": "sweep_progress",
                        "completed": sweep["completed"],
                        "total": sweep["total"],
                        "current_case": case_id
                    })
        
        sweep["status"] = "completed"
    
    def get_sweep_status(self, sweep_id: str) -> Optional[Dict]:
        """Get status of a parametric sweep."""
        return self.sweeps.get(sweep_id)
    
    async def cleanup(self):
        """Cleanup on shutdown."""
        for sim in self.simulations.values():
            if sim.process and sim.status == "running":
                sim.process.terminate()

