#!/usr/bin/env python3
"""
Parametric Sweep Automation for T-Junction Simulation

This script automates running OpenFOAM simulations across a grid of
(P_cont, P_disp) pressure values to generate datasets for the
microfluidic causal chamber.

Usage:
    python run_parametric.py --base-case ../tjunction_2d \
                             --output-dir ../parametric_results \
                             --p-cont 20000 40000 60000 80000 100000 \
                             --p-disp 10000 20000 30000 40000 50000

Requirements:
    - OpenFOAM installed and sourced
    - Python 3.8+
    - numpy, pandas

Author: Microfluidic Causal Chamber Project
"""

import os
import sys
import argparse
import shutil
import subprocess
import time
from pathlib import Path
import json

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("Required packages not found. Install with:")
    print("  pip install numpy pandas")
    sys.exit(1)


class ParametricRunner:
    """
    Run parametric sweeps of OpenFOAM T-junction simulation.
    """
    
    def __init__(self, base_case, output_dir, dry_run=False):
        """
        Initialize parametric runner.
        
        Args:
            base_case: Path to template OpenFOAM case
            output_dir: Directory for parametric sweep results
            dry_run: If True, only generate cases without running
        """
        self.base_case = Path(base_case)
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        
        if not self.base_case.exists():
            raise FileNotFoundError(f"Base case not found: {self.base_case}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_case(self, case_name, P_cont, P_disp):
        """
        Generate a new case with modified pressure boundary conditions.
        
        Args:
            case_name: Name for the new case
            P_cont: Continuous phase inlet pressure (Pa)
            P_disp: Dispersed phase inlet pressure (Pa)
        
        Returns:
            Path to generated case
        """
        case_dir = self.output_dir / case_name
        
        # Copy base case
        if case_dir.exists():
            shutil.rmtree(case_dir)
        shutil.copytree(self.base_case, case_dir)
        
        # Modify p_rgh boundary conditions
        p_rgh_file = case_dir / "0" / "p_rgh"
        self._modify_pressure_bc(p_rgh_file, P_cont, P_disp)
        
        # Create metadata file
        metadata = {
            'P_cont': P_cont,
            'P_disp': P_disp,
            'P_out': 0,
            'case_name': case_name,
            'base_case': str(self.base_case),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(case_dir / 'case_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"  Generated: {case_name}")
        return case_dir
    
    def _modify_pressure_bc(self, p_rgh_file, P_cont, P_disp):
        """Modify pressure values in p_rgh file."""
        with open(p_rgh_file, 'r') as f:
            content = f.read()
        
        # Replace oil_inlet pressure
        content = self._replace_pressure_value(
            content, 'oil_inlet', P_cont
        )
        
        # Replace water_inlet pressure
        content = self._replace_pressure_value(
            content, 'water_inlet', P_disp
        )
        
        with open(p_rgh_file, 'w') as f:
            f.write(content)
    
    def _replace_pressure_value(self, content, boundary_name, pressure):
        """
        Replace pressure value for a specific boundary.
        
        This is a simple text replacement - works for our specific format.
        For more robust parsing, use PyFoam or similar.
        """
        import re
        
        # Pattern to match the boundary block and p0 value
        # This is a simplified approach - assumes standard formatting
        
        lines = content.split('\n')
        new_lines = []
        in_boundary = False
        brace_count = 0
        
        for line in lines:
            if boundary_name in line and '{' not in line:
                in_boundary = True
            
            if in_boundary:
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                
                # Replace p0 value
                if 'p0' in line and 'uniform' in line:
                    line = f"        p0              uniform {pressure};"
                if 'value' in line and 'uniform' in line and 'p0' not in line:
                    line = f"        value           uniform {pressure};"
                
                if brace_count == 0 and '}' in line:
                    in_boundary = False
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def run_case(self, case_dir):
        """
        Run OpenFOAM simulation for a case.
        
        Returns:
            dict with run status and timing
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would run: {case_dir}")
            return {'status': 'dry_run', 'time': 0}
        
        start_time = time.time()
        
        # Run Allrun script
        allrun = case_dir / "Allrun"
        if not allrun.exists():
            # Create simple run commands if Allrun doesn't exist
            result = self._run_commands(case_dir)
        else:
            result = subprocess.run(
                ['bash', 'Allrun'],
                cwd=case_dir,
                capture_output=True,
                text=True
            )
        
        elapsed_time = time.time() - start_time
        
        # Check for success
        log_file = case_dir / "log.interFoam"
        success = False
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_content = f.read()
                if 'End' in log_content:
                    success = True
        
        return {
            'status': 'success' if success else 'failed',
            'time': elapsed_time
        }
    
    def _run_commands(self, case_dir):
        """Run OpenFOAM commands manually."""
        commands = [
            'blockMesh',
            'setFields',
            'interFoam'
        ]
        
        for cmd in commands:
            result = subprocess.run(
                [cmd],
                cwd=case_dir,
                capture_output=True,
                text=True
            )
            
            # Save log
            log_file = case_dir / f"log.{cmd}"
            with open(log_file, 'w') as f:
                f.write(result.stdout)
                f.write(result.stderr)
            
            if result.returncode != 0:
                print(f"  Error running {cmd}")
                return result
        
        return result
    
    def extract_results(self, case_dir):
        """
        Extract results from completed simulation.
        
        Returns dict with droplet metrics.
        """
        # Import our extraction module
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from extract_droplets import DropletExtractor
            
            extractor = DropletExtractor(case_dir)
            df, summary = extractor.process_case()
            
            return summary
        except Exception as e:
            print(f"  Error extracting results: {e}")
            return {'error': str(e)}
    
    def run_sweep(self, p_cont_values, p_disp_values, parallel=1):
        """
        Run full parametric sweep.
        
        Args:
            p_cont_values: List of continuous phase pressures (Pa)
            p_disp_values: List of dispersed phase pressures (Pa)
            parallel: Number of parallel runs (not implemented yet)
        
        Returns:
            DataFrame with all results
        """
        print("=" * 60)
        print("T-Junction Parametric Sweep")
        print("=" * 60)
        print(f"P_cont values: {p_cont_values}")
        print(f"P_disp values: {p_disp_values}")
        print(f"Total cases: {len(p_cont_values) * len(p_disp_values)}")
        print()
        
        results = []
        
        for P_cont in p_cont_values:
            for P_disp in p_disp_values:
                case_name = f"P_cont_{int(P_cont/1000)}kPa_P_disp_{int(P_disp/1000)}kPa"
                
                print(f"\nCase: {case_name}")
                print(f"  P_cont = {P_cont/1000:.0f} kPa, P_disp = {P_disp/1000:.0f} kPa")
                
                # Generate case
                case_dir = self.generate_case(case_name, P_cont, P_disp)
                
                # Run simulation
                run_result = self.run_case(case_dir)
                print(f"  Status: {run_result['status']}, Time: {run_result['time']:.1f} s")
                
                # Extract results
                if run_result['status'] == 'success':
                    metrics = self.extract_results(case_dir)
                else:
                    metrics = {}
                
                # Combine results
                result = {
                    'case_name': case_name,
                    'P_cont': P_cont,
                    'P_disp': P_disp,
                    'P_out': 0,
                    'run_status': run_result['status'],
                    'run_time': run_result['time'],
                    **metrics
                }
                results.append(result)
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Save results
        output_file = self.output_dir / 'parametric_sweep_results.csv'
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")
        
        return df
    
    def generate_causal_dataset(self, df, output_file=None):
        """
        Convert parametric sweep results to causal chamber dataset format.
        
        Creates CSV compatible with variables.csv from mf_tjunction_test_v1.
        """
        if output_file is None:
            output_file = self.output_dir / 'openfoam_causal_dataset.csv'
        
        # Map to causal chamber variable names
        dataset = []
        for i, row in df.iterrows():
            entry = {
                'timestamp': i * 1000,  # Dummy timestamp
                'config': 'pressure_driven',
                'counter': i,
                'flag': i,
                'intervention': 0,
                'P_cont': row['P_cont'],
                'P_disp': row['P_disp'],
                'P_out': row.get('P_out', 0),
                'P_cont_meas': row['P_cont'],  # Simulation has no noise
                'P_disp_meas': row['P_disp'],
                'P_out_meas': row.get('P_out', 0),
                'f_droplet': row.get('frequency_Hz', 0),
                'd_droplet': row.get('mean_diameter_um', 0),
                'L_droplet': row.get('mean_length_um', 0),
                'w_droplet': row.get('mean_width_um', 0),
                'n_droplets': row.get('n_droplets_total', 0),
                'polydispersity': (row.get('std_diameter_um', 0) / 
                                   row.get('mean_diameter_um', 1) 
                                   if row.get('mean_diameter_um', 0) > 0 else 0),
                'regime': 'dripping' if row.get('frequency_Hz', 0) > 0 else 'unknown',
                'camera': 0,
                'Q_cont_calc': 0,  # Would need flow rate extraction
                'Q_disp_calc': 0,
            }
            dataset.append(entry)
        
        causal_df = pd.DataFrame(dataset)
        causal_df.to_csv(output_file, index=False)
        print(f"Causal dataset saved to: {output_file}")
        
        return causal_df


def main():
    parser = argparse.ArgumentParser(
        description="Run parametric sweep of T-junction simulations"
    )
    parser.add_argument(
        "--base-case",
        required=True,
        help="Path to template OpenFOAM case"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for parametric sweep results"
    )
    # NOTE: pressures here are of order 100-1000 Pa, NOT tens of kPa. Over
    # this short domain (no tubing/serpentine resistance), kPa-scale inlets
    # give Ca >> 0.02 and a junction pressure above P_disp — stratified flow
    # and zero droplets (this was the Dec 2025 failure). Droplets need
    # Ca = mu_cont*U/sigma <= ~0.05 and P_disp above the junction pressure
    # (roughly 0.65 * P_cont for this geometry).
    parser.add_argument(
        "--p-cont",
        type=float,
        nargs='+',
        default=[600, 850, 1100],
        help="Continuous phase pressure values (Pa); see regime note in source"
    )
    parser.add_argument(
        "--p-disp",
        type=float,
        nargs='+',
        default=[500, 650, 800],
        help="Dispersed phase pressure values (Pa); must exceed ~0.65*P_cont"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate cases without running simulations"
    )
    
    args = parser.parse_args()
    
    runner = ParametricRunner(
        args.base_case,
        args.output_dir,
        dry_run=args.dry_run
    )
    
    df = runner.run_sweep(args.p_cont, args.p_disp)
    
    if not args.dry_run:
        runner.generate_causal_dataset(df)
    
    print("\nDone!")


if __name__ == "__main__":
    main()


