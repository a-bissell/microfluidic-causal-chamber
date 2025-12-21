"""
OpenFOAM Output Parser

Parses log files and VTK output for post-processing and visualization.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class TimeStep:
    """Data from a single time step."""
    time: float
    courant_mean: float = 0.0
    courant_max: float = 0.0
    execution_time: float = 0.0
    clock_time: float = 0.0
    

@dataclass
class DropletInfo:
    """Information about a detected droplet."""
    id: int
    time: float
    position: Tuple[float, float, float]
    volume: float
    diameter: float  # Equivalent spherical diameter
    length: float    # Major axis length
    velocity: Tuple[float, float, float]


@dataclass
class SimulationLog:
    """Parsed simulation log data."""
    time_steps: List[TimeStep] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    solver: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_foam_log(log_path: Path) -> SimulationLog:
    """Parse an OpenFOAM log file."""
    result = SimulationLog()
    
    if not log_path.exists():
        return result
    
    content = log_path.read_text()
    
    # Extract solver name
    solver_match = re.search(r'Selecting solver (\w+)', content)
    if solver_match:
        result.solver = solver_match.group(1)
    
    # Extract time steps
    time_pattern = r'Time = ([\d.e+-]+)\n.*?Courant Number mean: ([\d.e+-]+) max: ([\d.e+-]+)'
    for match in re.finditer(time_pattern, content, re.DOTALL):
        ts = TimeStep(
            time=float(match.group(1)),
            courant_mean=float(match.group(2)),
            courant_max=float(match.group(3)),
        )
        result.time_steps.append(ts)
    
    # Extract execution time
    exec_pattern = r'ExecutionTime = ([\d.]+) s  ClockTime = ([\d.]+) s'
    exec_matches = list(re.finditer(exec_pattern, content))
    for i, match in enumerate(exec_matches):
        if i < len(result.time_steps):
            result.time_steps[i].execution_time = float(match.group(1))
            result.time_steps[i].clock_time = float(match.group(2))
    
    # Extract errors and warnings
    for line in content.split('\n'):
        if 'ERROR' in line or 'FATAL' in line:
            result.errors.append(line.strip())
        elif 'Warning' in line:
            result.warnings.append(line.strip())
    
    if result.time_steps:
        result.start_time = result.time_steps[0].time
        result.end_time = result.time_steps[-1].time
    
    return result


def parse_blockMesh_log(log_path: Path) -> Dict:
    """Parse blockMesh log for mesh statistics."""
    result = {
        'cells': 0,
        'points': 0,
        'faces': 0,
        'patches': [],
        'bounding_box': None,
        'success': False,
    }
    
    if not log_path.exists():
        return result
    
    content = log_path.read_text()
    
    # Check for success
    if 'End' in content and 'FOAM FATAL' not in content:
        result['success'] = True
    
    # Extract cell count
    cells_match = re.search(r'cells:\s+(\d+)', content)
    if cells_match:
        result['cells'] = int(cells_match.group(1))
    
    # Extract point count
    points_match = re.search(r'points:\s+(\d+)', content)
    if points_match:
        result['points'] = int(points_match.group(1))
    
    # Extract bounding box
    bb_match = re.search(r'Overall domain bounding box \(([\d.e+-]+) ([\d.e+-]+) ([\d.e+-]+)\) \(([\d.e+-]+) ([\d.e+-]+) ([\d.e+-]+)\)', content)
    if bb_match:
        result['bounding_box'] = {
            'min': [float(bb_match.group(i)) for i in range(1, 4)],
            'max': [float(bb_match.group(i)) for i in range(4, 7)],
        }
    
    return result


def detect_droplets_from_alpha(alpha_data: np.ndarray, mesh_data: Dict, threshold: float = 0.5) -> List[DropletInfo]:
    """
    Detect droplets from alpha field data.
    
    Args:
        alpha_data: Volume fraction field (alpha.water)
        mesh_data: Mesh geometry information
        threshold: Volume fraction threshold for droplet detection
    
    Returns:
        List of detected droplets
    """
    droplets = []
    
    # Find connected regions where alpha > threshold
    # This is a simplified version - real implementation would use proper 
    # connected component analysis on the mesh
    
    # For now, return empty list - actual implementation requires VTK
    return droplets


def calculate_droplet_statistics(droplets: List[DropletInfo]) -> Dict:
    """Calculate statistics from detected droplets."""
    if not droplets:
        return {
            'count': 0,
            'mean_diameter': 0,
            'std_diameter': 0,
            'mean_velocity': 0,
            'frequency': 0,
        }
    
    diameters = [d.diameter for d in droplets]
    velocities = [np.linalg.norm(d.velocity) for d in droplets]
    
    # Estimate frequency from droplet times
    times = sorted([d.time for d in droplets])
    if len(times) > 1:
        intervals = np.diff(times)
        frequency = 1.0 / np.mean(intervals) if np.mean(intervals) > 0 else 0
    else:
        frequency = 0
    
    return {
        'count': len(droplets),
        'mean_diameter': np.mean(diameters),
        'std_diameter': np.std(diameters),
        'mean_velocity': np.mean(velocities),
        'frequency': frequency,
        'cv': np.std(diameters) / np.mean(diameters) if np.mean(diameters) > 0 else 0,
    }


def read_vtk_field(vtk_path: Path, field_name: str = 'alpha.water') -> Optional[np.ndarray]:
    """
    Read a field from VTK file.
    
    For full implementation, use the vtk library:
    
    import vtk
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(str(vtk_path))
    reader.Update()
    data = reader.GetOutput().GetCellData().GetArray(field_name)
    return vtk.util.numpy_support.vtk_to_numpy(data)
    """
    # Placeholder - requires VTK library
    return None


def export_results_csv(
    output_path: Path,
    time_steps: List[TimeStep],
    droplets: List[DropletInfo]
) -> None:
    """Export simulation results to CSV format."""
    
    # Time step data
    with open(output_path / 'timesteps.csv', 'w') as f:
        f.write('time,courant_mean,courant_max,execution_time\n')
        for ts in time_steps:
            f.write(f'{ts.time},{ts.courant_mean},{ts.courant_max},{ts.execution_time}\n')
    
    # Droplet data
    with open(output_path / 'droplets.csv', 'w') as f:
        f.write('id,time,x,y,z,volume,diameter,length,vx,vy,vz\n')
        for d in droplets:
            f.write(f'{d.id},{d.time},{d.position[0]},{d.position[1]},{d.position[2]},'
                   f'{d.volume},{d.diameter},{d.length},'
                   f'{d.velocity[0]},{d.velocity[1]},{d.velocity[2]}\n')


# Garstecki scaling law validation
def validate_garstecki_scaling(
    droplet_lengths: List[float],
    channel_width: float,
    flow_ratios: List[float],
) -> Dict:
    """
    Validate against Garstecki scaling law: L/w = 1 + α(Q_d/Q_c)
    
    Args:
        droplet_lengths: Measured droplet lengths
        channel_width: Channel width
        flow_ratios: Q_dispersed / Q_continuous for each measurement
    
    Returns:
        Fitting parameters and R² value
    """
    if len(droplet_lengths) != len(flow_ratios) or len(droplet_lengths) < 2:
        return {'alpha': 0, 'r_squared': 0, 'valid': False}
    
    # Normalized lengths
    L_norm = np.array(droplet_lengths) / channel_width
    Q_ratio = np.array(flow_ratios)
    
    # Linear fit: L/w = 1 + alpha * (Qd/Qc)
    # Rearrange: (L/w - 1) = alpha * (Qd/Qc)
    y = L_norm - 1
    x = Q_ratio
    
    # Least squares fit
    alpha = np.sum(x * y) / np.sum(x * x) if np.sum(x * x) > 0 else 0
    
    # R² calculation
    y_pred = alpha * x
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'alpha': alpha,
        'r_squared': r_squared,
        'valid': r_squared > 0.8,  # Good fit threshold
    }

