#!/usr/bin/env python3
"""
Droplet Detection and Metrics Extraction for OpenFOAM T-Junction Simulation

This script processes OpenFOAM VTK output to:
1. Detect droplets using connected component analysis
2. Measure droplet dimensions (diameter, length, area/volume)
3. Calculate formation frequency
4. Export metrics in CSV format compatible with causal chamber datasets

Usage:
    python extract_droplets.py <case_directory> [--output results.csv]

Requirements:
    pip install numpy scipy vtk pandas matplotlib

Author: Microfluidic Causal Chamber Project
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

try:
    import vtk
    from vtk.util import numpy_support
except ImportError:
    print("VTK not found. Install with: pip install vtk")
    sys.exit(1)

try:
    from scipy import ndimage
    from scipy.signal import find_peaks
except ImportError:
    print("SciPy not found. Install with: pip install scipy")
    sys.exit(1)


class DropletExtractor:
    """
    Extract droplet metrics from OpenFOAM VTK output.
    """
    
    def __init__(self, case_dir, alpha_threshold=0.5):
        """
        Initialize the droplet extractor.
        
        Args:
            case_dir: Path to OpenFOAM case directory
            alpha_threshold: Threshold for water phase (alpha > threshold = water)
        """
        self.case_dir = Path(case_dir)
        self.vtk_dir = self.case_dir / "VTK"
        self.alpha_threshold = alpha_threshold
        
        # Physical parameters (from blockMeshDict)
        self.w_main = 150e-6    # Main channel width (m)
        self.w_disp = 75e-6     # Dispersed channel width (m)
        self.depth = 80e-6      # Channel depth (m)
        
        # Junction location (for frequency calculation)
        self.x_junction = 0.0005 + self.w_main  # End of junction
        
    def find_vtk_files(self):
        """Find all VTK files sorted by time."""
        if not self.vtk_dir.exists():
            raise FileNotFoundError(f"VTK directory not found: {self.vtk_dir}")
        
        vtk_files = []
        for f in self.vtk_dir.glob("*.vtk"):
            # Skip series files
            if "series" in f.name:
                continue
            vtk_files.append(f)
        
        # Sort by time (extract time from filename)
        def get_time(f):
            # Filename format: casename_<time>.vtk
            parts = f.stem.split("_")
            try:
                return float(parts[-1])
            except ValueError:
                return 0.0
        
        vtk_files.sort(key=get_time)
        return vtk_files
    
    def read_vtk(self, vtk_file):
        """Read VTK file and extract alpha field."""
        reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(str(vtk_file))
        reader.Update()
        
        data = reader.GetOutput()
        
        # Get cell centers
        centers_filter = vtk.vtkCellCenters()
        centers_filter.SetInputData(data)
        centers_filter.Update()
        centers = centers_filter.GetOutput()
        
        # Extract coordinates
        points = centers.GetPoints()
        n_cells = points.GetNumberOfPoints()
        
        coords = np.zeros((n_cells, 3))
        for i in range(n_cells):
            coords[i] = points.GetPoint(i)
        
        # Extract alpha.water field
        alpha = None
        cell_data = data.GetCellData()
        for i in range(cell_data.GetNumberOfArrays()):
            name = cell_data.GetArrayName(i)
            if "alpha" in name.lower():
                arr = cell_data.GetArray(i)
                alpha = numpy_support.vtk_to_numpy(arr)
                break
        
        if alpha is None:
            raise ValueError(f"alpha.water field not found in {vtk_file}")
        
        return coords, alpha
    
    def detect_droplets_2d(self, coords, alpha):
        """
        Detect droplets in 2D simulation.
        
        Returns list of droplet properties:
            - centroid (x, y)
            - area
            - length (extent in x)
            - width (extent in y)
        """
        # Create 2D grid for analysis
        # Filter cells where alpha > threshold (water phase)
        water_mask = alpha > self.alpha_threshold
        water_coords = coords[water_mask]
        
        if len(water_coords) == 0:
            return []
        
        # For 2D, group by proximity in x-y plane
        # Use connected components via binning
        
        # Determine cell size from coordinate spacing
        x_unique = np.unique(np.round(water_coords[:, 0], 8))
        if len(x_unique) > 1:
            dx = np.min(np.diff(x_unique))
        else:
            dx = 5e-6  # Default cell size
        
        # Create labels using spatial clustering
        # Simple approach: group cells that are adjacent
        droplets = []
        
        # Only analyze outlet region (x > junction)
        outlet_mask = water_coords[:, 0] > self.x_junction
        outlet_coords = water_coords[outlet_mask]
        
        if len(outlet_coords) == 0:
            return []
        
        # Simple clustering by x-coordinate gaps
        x_sorted_idx = np.argsort(outlet_coords[:, 0])
        x_sorted = outlet_coords[x_sorted_idx, 0]
        
        # Find gaps larger than 2 cell widths (indicating separate droplets)
        gaps = np.diff(x_sorted) > 2 * dx
        droplet_starts = np.concatenate([[0], np.where(gaps)[0] + 1])
        droplet_ends = np.concatenate([np.where(gaps)[0] + 1, [len(x_sorted)]])
        
        for start, end in zip(droplet_starts, droplet_ends):
            if end - start < 5:  # Skip very small clusters
                continue
            
            drop_coords = outlet_coords[x_sorted_idx[start:end]]
            
            # Calculate properties
            centroid = np.mean(drop_coords, axis=0)
            x_min, x_max = np.min(drop_coords[:, 0]), np.max(drop_coords[:, 0])
            y_min, y_max = np.min(drop_coords[:, 1]), np.max(drop_coords[:, 1])
            
            length = x_max - x_min
            width = y_max - y_min
            area = len(drop_coords) * dx * dx  # Approximate area
            
            droplets.append({
                'centroid_x': centroid[0],
                'centroid_y': centroid[1],
                'length': length,
                'width': width,
                'area': area,
                'n_cells': len(drop_coords)
            })
        
        return droplets
    
    def calculate_frequency(self, all_droplets, times):
        """
        Calculate droplet formation frequency from time series.
        
        Counts droplets passing a reference line over time.
        """
        if len(times) < 2:
            return 0.0
        
        # Reference position for counting (mid-outlet)
        x_ref = 0.001  # 1 mm from inlet
        
        # Track droplet passage times
        passage_times = []
        
        for t, droplets in zip(times, all_droplets):
            for drop in droplets:
                # Check if droplet centroid is near reference line
                if abs(drop['centroid_x'] - x_ref) < 20e-6:  # Within 20 um
                    passage_times.append(t)
        
        # Remove duplicates (same droplet detected in consecutive frames)
        if len(passage_times) < 2:
            return 0.0
        
        passage_times = np.array(passage_times)
        unique_passages = [passage_times[0]]
        for t in passage_times[1:]:
            if t - unique_passages[-1] > 0.001:  # At least 1 ms between detections
                unique_passages.append(t)
        
        if len(unique_passages) < 2:
            return 0.0
        
        # Calculate frequency
        total_time = times[-1] - times[0]
        frequency = len(unique_passages) / total_time if total_time > 0 else 0.0
        
        return frequency
    
    def process_case(self):
        """
        Process all time steps and extract droplet metrics.
        """
        vtk_files = self.find_vtk_files()
        print(f"Found {len(vtk_files)} VTK files")
        
        results = []
        all_droplets = []
        times = []
        
        for vtk_file in vtk_files:
            # Extract time from filename
            parts = vtk_file.stem.split("_")
            try:
                time = float(parts[-1])
            except ValueError:
                time = 0.0
            
            print(f"Processing t = {time:.4f} s...")
            
            try:
                coords, alpha = self.read_vtk(vtk_file)
                droplets = self.detect_droplets_2d(coords, alpha)
                
                times.append(time)
                all_droplets.append(droplets)
                
                for i, drop in enumerate(droplets):
                    results.append({
                        'time': time,
                        'droplet_id': i,
                        'centroid_x': drop['centroid_x'] * 1e6,  # Convert to um
                        'centroid_y': drop['centroid_y'] * 1e6,
                        'length': drop['length'] * 1e6,
                        'width': drop['width'] * 1e6,
                        'area': drop['area'] * 1e12,  # um^2
                        'd_equivalent': np.sqrt(4 * drop['area'] / np.pi) * 1e6  # um
                    })
                    
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        # Calculate frequency
        frequency = self.calculate_frequency(all_droplets, times)
        
        # Create summary
        df = pd.DataFrame(results)
        
        summary = {
            'n_timesteps': len(times),
            'n_droplets_total': len(results),
            'frequency_Hz': frequency,
            'mean_length_um': df['length'].mean() if len(df) > 0 else 0,
            'mean_width_um': df['width'].mean() if len(df) > 0 else 0,
            'mean_diameter_um': df['d_equivalent'].mean() if len(df) > 0 else 0,
            'std_diameter_um': df['d_equivalent'].std() if len(df) > 0 else 0,
        }
        
        return df, summary
    
    def export_results(self, df, summary, output_file):
        """Export results to CSV files."""
        # Detailed results
        df.to_csv(output_file, index=False)
        print(f"Detailed results saved to: {output_file}")
        
        # Summary file
        summary_file = output_file.replace('.csv', '_summary.csv')
        pd.DataFrame([summary]).to_csv(summary_file, index=False)
        print(f"Summary saved to: {summary_file}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Extract droplet metrics from OpenFOAM VTK output"
    )
    parser.add_argument(
        "case_dir",
        help="Path to OpenFOAM case directory"
    )
    parser.add_argument(
        "--output", "-o",
        default="droplet_results.csv",
        help="Output CSV file (default: droplet_results.csv)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.5,
        help="Alpha threshold for water phase (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Droplet Extraction for T-Junction Simulation")
    print("=" * 60)
    print(f"Case: {args.case_dir}")
    print(f"Output: {args.output}")
    print()
    
    extractor = DropletExtractor(args.case_dir, args.threshold)
    df, summary = extractor.process_case()
    extractor.export_results(df, summary, args.output)
    
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()


