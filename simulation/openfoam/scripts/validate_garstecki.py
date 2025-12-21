#!/usr/bin/env python3
"""
Validation Script: Compare OpenFOAM Results to Garstecki Scaling Law

This script validates simulation results against the theoretical
Garstecki scaling law for T-junction droplet formation:

    L/w = 1 + α * (Q_disp/Q_cont)

where:
    L = droplet length
    w = main channel width
    α = geometry-dependent constant (typically 1-3)
    Q_disp = dispersed phase flow rate
    Q_cont = continuous phase flow rate

Usage:
    python validate_garstecki.py <results_file.csv> [--plot]

Requirements:
    pip install numpy pandas matplotlib scipy

Author: Microfluidic Causal Chamber Project
"""

import argparse
import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from scipy import optimize


# Physical parameters (matching blockMeshDict)
W_MAIN = 150e-6      # Main channel width (m)
W_DISP = 75e-6       # Dispersed channel width (m)
DEPTH = 80e-6        # Channel depth (m)

# Fluid properties (matching transportProperties)
MU_CONT = 0.048      # Oil dynamic viscosity (Pa.s)
MU_DISP = 0.001      # Water dynamic viscosity (Pa.s)
RHO_CONT = 960       # Oil density (kg/m³)
RHO_DISP = 1000      # Water density (kg/m³)


def hagen_poiseuille_rectangular(delta_p, mu, length, width, depth):
    """
    Calculate flow rate in rectangular channel using Hagen-Poiseuille.
    
    Q = (w * h³ / 12μL) * (1 - 0.63 * h/w) * ΔP
    
    for h < w (height < width)
    """
    if width < depth:
        width, depth = depth, width  # Swap if needed
    
    # Hydraulic resistance factor
    correction = 1 - 0.63 * (depth / width)
    
    Q = (width * depth**3 / (12 * mu * length)) * correction * delta_p
    
    return Q


def garstecki_scaling(Q_ratio, alpha=1.0):
    """
    Garstecki scaling law for droplet length.
    
    L/w = 1 + alpha * (Q_disp / Q_cont)
    """
    return 1 + alpha * Q_ratio


def fit_garstecki(Q_ratios, L_over_w):
    """
    Fit Garstecki scaling law to data.
    
    Returns fitted alpha value.
    """
    def residual(alpha):
        predicted = garstecki_scaling(Q_ratios, alpha)
        return np.sum((predicted - L_over_w)**2)
    
    result = optimize.minimize_scalar(residual, bounds=(0.5, 5.0), method='bounded')
    return result.x


def validate_results(df, channel_length=500e-6):
    """
    Validate simulation results against theory.
    
    Args:
        df: DataFrame with columns P_cont, P_disp, mean_length_um
        channel_length: Channel length for flow rate calculation
    
    Returns:
        validation dict with metrics
    """
    results = []
    
    for _, row in df.iterrows():
        P_cont = row['P_cont']
        P_disp = row['P_disp']
        L_droplet = row.get('mean_length_um', 0) * 1e-6  # Convert to m
        
        if L_droplet <= 0:
            continue
        
        # Calculate expected flow rates
        Q_cont = hagen_poiseuille_rectangular(
            P_cont, MU_CONT, channel_length, W_MAIN, DEPTH
        )
        Q_disp = hagen_poiseuille_rectangular(
            P_disp, MU_DISP, channel_length, W_DISP, DEPTH
        )
        
        if Q_cont <= 0:
            continue
        
        Q_ratio = Q_disp / Q_cont
        L_over_w = L_droplet / W_MAIN
        
        results.append({
            'P_cont': P_cont,
            'P_disp': P_disp,
            'Q_cont': Q_cont * 1e9 * 60,  # Convert to uL/min
            'Q_disp': Q_disp * 1e9 * 60,
            'Q_ratio': Q_ratio,
            'L_droplet_um': L_droplet * 1e6,
            'L_over_w': L_over_w,
        })
    
    if len(results) == 0:
        print("No valid results to validate")
        return None
    
    val_df = pd.DataFrame(results)
    
    # Fit Garstecki scaling
    alpha_fit = fit_garstecki(val_df['Q_ratio'].values, val_df['L_over_w'].values)
    
    # Calculate predicted values
    val_df['L_over_w_predicted'] = garstecki_scaling(val_df['Q_ratio'], alpha_fit)
    
    # Calculate error metrics
    residuals = val_df['L_over_w'] - val_df['L_over_w_predicted']
    rmse = np.sqrt(np.mean(residuals**2))
    r_squared = 1 - np.var(residuals) / np.var(val_df['L_over_w'])
    
    validation = {
        'alpha_fit': alpha_fit,
        'rmse': rmse,
        'r_squared': r_squared,
        'n_points': len(val_df),
        'data': val_df
    }
    
    return validation


def plot_validation(validation, output_file=None):
    """Create validation plot."""
    if not HAS_MATPLOTLIB:
        print("Matplotlib not available for plotting")
        return
    
    df = validation['data']
    alpha = validation['alpha_fit']
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: L/w vs Q_ratio
    ax1 = axes[0]
    ax1.scatter(df['Q_ratio'], df['L_over_w'], 
                c=df['P_cont']/1000, cmap='viridis', 
                s=80, edgecolor='black', label='Simulation')
    
    # Theoretical line
    Q_range = np.linspace(0, df['Q_ratio'].max() * 1.1, 100)
    ax1.plot(Q_range, garstecki_scaling(Q_range, alpha), 
             'r--', linewidth=2, label=f'Garstecki fit (α={alpha:.2f})')
    ax1.plot(Q_range, garstecki_scaling(Q_range, 1.0), 
             'b:', linewidth=1, alpha=0.5, label='Garstecki (α=1)')
    
    ax1.set_xlabel('$Q_{disp}/Q_{cont}$', fontsize=12)
    ax1.set_ylabel('$L/w$', fontsize=12)
    ax1.set_title('Garstecki Scaling Law Validation', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(ax1.collections[0], ax=ax1)
    cbar.set_label('$P_{cont}$ (kPa)')
    
    # Plot 2: Parity plot
    ax2 = axes[1]
    ax2.scatter(df['L_over_w_predicted'], df['L_over_w'], 
                c=df['P_cont']/1000, cmap='viridis', s=80, edgecolor='black')
    
    # Perfect agreement line
    lim = max(df['L_over_w'].max(), df['L_over_w_predicted'].max()) * 1.1
    ax2.plot([0, lim], [0, lim], 'k--', linewidth=1, label='Perfect agreement')
    
    ax2.set_xlabel('Predicted $L/w$', fontsize=12)
    ax2.set_ylabel('Simulated $L/w$', fontsize=12)
    ax2.set_title(f'Parity Plot (R² = {validation["r_squared"]:.3f})', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, lim)
    ax2.set_ylim(0, lim)
    ax2.set_aspect('equal')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Validate OpenFOAM results against Garstecki scaling law"
    )
    parser.add_argument(
        "results_file",
        help="CSV file with simulation results"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate validation plot"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file for plot (if not specified, displays interactively)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Garstecki Scaling Law Validation")
    print("=" * 60)
    
    # Load results
    df = pd.read_csv(args.results_file)
    print(f"Loaded {len(df)} data points from {args.results_file}")
    
    # Validate
    validation = validate_results(df)
    
    if validation is None:
        return
    
    # Print results
    print()
    print("Validation Results:")
    print("-" * 40)
    print(f"  Fitted α:  {validation['alpha_fit']:.3f}")
    print(f"  Expected:  1.0 - 3.0 (literature range)")
    print(f"  RMSE:      {validation['rmse']:.4f}")
    print(f"  R²:        {validation['r_squared']:.4f}")
    print(f"  N points:  {validation['n_points']}")
    print()
    
    if validation['r_squared'] > 0.9:
        print("✓ Excellent agreement with Garstecki scaling!")
    elif validation['r_squared'] > 0.7:
        print("✓ Good agreement with Garstecki scaling")
    else:
        print("⚠ Poor agreement - check simulation parameters")
    
    # Plot if requested
    if args.plot:
        plot_validation(validation, args.output)


if __name__ == "__main__":
    main()


