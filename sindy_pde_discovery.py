#!/usr/bin/env python3
"""
sindy_pde_discovery.py — Cost of Existence PDE Extraction

Loads the 2D spatiotemporal phi field from pde_telemetry.npz and uses
PySINDy + manual finite differences to discover the governing PDE of
the Weitzenböck torsion lattice.

The expected result (blind verification):
    phi_tt = c^2 * (phi_xx + phi_yy) - alpha * phi_t + S(defect)

Usage:
    python sindy_pde_discovery.py [--file pde_telemetry.npz] [--threshold 0.1]
"""

import argparse
import numpy as np
import sys

def compute_derivatives(data, dx, dt):
    """
    Compute 1st and 2nd derivatives using centered finite differences.
    """
    phi = data['phi']
    
    T, X, Y = phi.shape
    
    # We lose 1 boundary cell on each side (time and space)
    # So interior size is (T-2, X-2, Y-2)
    phi_int = phi[1:-1, 1:-1, 1:-1]
    
    # Time derivatives (centered)
    phi_t = (phi[2:, 1:-1, 1:-1] - phi[:-2, 1:-1, 1:-1]) / (2.0 * dt)
    phi_tt = (phi[2:, 1:-1, 1:-1] - 2.0*phi_int + phi[:-2, 1:-1, 1:-1]) / (dt**2)
    
    # Spatial derivatives (centered)
    phi_x = (phi[1:-1, 2:, 1:-1] - phi[1:-1, :-2, 1:-1]) / (2.0 * dx)
    phi_y = (phi[1:-1, 1:-1, 2:] - phi[1:-1, 1:-1, :-2]) / (2.0 * dx)
    
    # If the true 3D laplacian is in the telemetry, use it (avoids missing z-derivative)
    if 'laplacian' in data.files:
        lap_true = data['laplacian'] / (dx**2)
        laplacian = lap_true[1:-1, 1:-1, 1:-1]
    else:
        # Fallback to 2D approximation
        phi_xx = (phi[1:-1, 2:, 1:-1] - 2.0*phi_int + phi[1:-1, :-2, 1:-1]) / (dx**2)
        phi_yy = (phi[1:-1, 1:-1, 2:] - 2.0*phi_int + phi[1:-1, 1:-1, :-2]) / (dx**2)
        laplacian = phi_xx + phi_yy
    
    # --- Mask out the central mass (Sun) ---
    # The physics engine hard-subtracts mass from the center pixel every tick,
    # which violates the vacuum wave equation. We must exclude the central region.
    mask = np.ones_like(phi_int, dtype=bool)
    cy, cx = phi_int.shape[1]//2, phi_int.shape[2]//2
    mask[:, cy-5:cy+6, cx-5:cx+6] = False
    
    return {
        'phi': phi_int[mask],
        'phi_t': phi_t[mask],
        'phi_tt': phi_tt[mask],
        'phi_x': phi_x[mask],
        'phi_y': phi_y[mask],
        'laplacian': laplacian[mask],
    }

def run_sindy_pde(derivs, threshold=0.1, use_pysindy=True):
    """
    Attempt PDE discovery using two methods:
    1. Direct least-squares regression (always available)
    2. PySINDy STLSQ (if pysindy is installed)
    
    Target: phi_tt
    Candidate features: phi, phi_t, laplacian (phi_xx + phi_yy), phi_xx, phi_yy
    """
    feature_dict = {
        'phi':       derivs['phi'].ravel(),
        'phi_t':     derivs['phi_t'].ravel(),
        'laplacian': derivs['laplacian'].ravel(),
        'phi_x':     derivs['phi_x'].ravel(),
        'phi_y':     derivs['phi_y'].ravel(),
    }
    
    target = derivs['phi_tt'].ravel()
    
    names = list(feature_dict.keys())
    X = np.column_stack([feature_dict[n] for n in names])
    
    # Remove any rows with NaN or Inf
    valid = np.isfinite(target) & np.all(np.isfinite(X), axis=1)
    target = target[valid]
    X = X[valid]
    
    n_samples = len(target)
    print(f"\n{'='*60}")
    print(f"PDE DISCOVERY: phi_tt = f(phi, phi_t, laplacian, ...)")
    print(f"{'='*60}")
    print(f"Total data points: {n_samples:,}")
    print(f"Feature matrix shape: {X.shape}")
    
    # === Method 1: Direct Least Squares ===
    print(f"\n--- Method 1: Ordinary Least Squares ---")
    
    # Add intercept column
    X_ols = np.column_stack([X, np.ones(n_samples)])
    names_ols = names + ['intercept']
    
    # Solve via pseudoinverse
    coeffs_ols, residuals, rank, sv = np.linalg.lstsq(X_ols, target, rcond=None)
    
    # R^2 score
    ss_res = np.sum((target - X_ols @ coeffs_ols) ** 2)
    ss_tot = np.sum((target - target.mean()) ** 2)
    r2_ols = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    
    print(f"R² = {r2_ols:.8f}")
    print(f"\nCoefficients:")
    for name, coeff in zip(names_ols, coeffs_ols):
        if abs(coeff) > 1e-10:
            print(f"  {name:>12s}: {coeff:>+16.6f}")
    
    # === Method 2: Sparse Thresholded Regression (STLSQ) ===
    print(f"\n--- Method 2: STLSQ (threshold={threshold}) ---")
    
    # Manual STLSQ implementation (no pysindy dependency required)
    coeffs_sparse = coeffs_ols.copy()
    max_iter = 20
    for iteration in range(max_iter):
        # Zero out coefficients below threshold
        small = np.abs(coeffs_sparse) < threshold
        coeffs_sparse[small] = 0.0
        
        # Find surviving features
        big_idx = np.where(~small)[0]
        if len(big_idx) == 0:
            print(f"  [WARNING] All coefficients below threshold! Try a smaller threshold.")
            break
        
        # Re-fit only the surviving features
        X_sub = X_ols[:, big_idx]
        coeffs_sub, _, _, _ = np.linalg.lstsq(X_sub, target, rcond=None)
        
        # Update sparse coefficients
        new_sparse = np.zeros_like(coeffs_sparse)
        new_sparse[big_idx] = coeffs_sub
        
        # Check convergence
        if np.allclose(new_sparse, coeffs_sparse, atol=1e-10):
            break
        coeffs_sparse = new_sparse
    
    ss_res_sp = np.sum((target - X_ols @ coeffs_sparse) ** 2)
    r2_sparse = 1.0 - ss_res_sp / ss_tot if ss_tot > 0 else 0.0
    
    print(f"R² = {r2_sparse:.8f}")
    print(f"\nSurviving terms:")
    for name, coeff in zip(names_ols, coeffs_sparse):
        if abs(coeff) > 1e-10:
            print(f"  {name:>12s}: {coeff:>+16.6f}")
    
    # === Build the human-readable equation ===
    print(f"\n{'='*60}")
    print(f"EXTRACTED PDE (Cost of Existence):")
    print(f"{'='*60}")
    
    equation_parts = []
    for name, coeff in zip(names_ols, coeffs_sparse):
        if abs(coeff) > 1e-10:
            if name == 'intercept':
                equation_parts.append(f"{coeff:+.6f}")
            else:
                equation_parts.append(f"{coeff:+.6f}·{name}")
    
    if equation_parts:
        equation = " ".join(equation_parts)
        print(f"\n  phi_tt = {equation}")
    else:
        print(f"\n  [No terms survived thresholding]")
    
    print(f"\n  R² = {r2_sparse:.8f}")
    
    # === Physical Interpretation ===
    print(f"\n{'='*60}")
    print(f"PHYSICAL INTERPRETATION:")
    print(f"{'='*60}")
    
    lap_coeff = coeffs_sparse[names_ols.index('laplacian')] if 'laplacian' in names_ols else 0.0
    phi_t_coeff = coeffs_sparse[names_ols.index('phi_t')] if 'phi_t' in names_ols else 0.0
    phi_coeff = coeffs_sparse[names_ols.index('phi')] if 'phi' in names_ols else 0.0
    
    if abs(lap_coeff) > 1e-3:
        c_extracted = np.sqrt(abs(lap_coeff))
        print(f"\n  Laplacian coefficient: {lap_coeff:.6f}")
        print(f"  => Extracted wave speed: c = sqrt({lap_coeff:.4f}) = {c_extracted:.4f}")
    
    if abs(phi_t_coeff) > 1e-6:
        print(f"\n  phi_t coefficient (damping): {phi_t_coeff:.6f}")
        # The engine applies: phi_next *= TORSION_DECAY each tick
        # In PDE form: phi_tt = c^2 * laplacian + alpha * phi_t
        # alpha < 0 means damping (energy loss)
        if phi_t_coeff < 0:
            print(f"  => DAMPING detected (energy dissipation, 'cost of existence')")
        else:
            print(f"  => ANTI-DAMPING detected (energy injection)")
    
    if abs(phi_coeff) > 1e-6:
        print(f"\n  phi coefficient (restoring): {phi_coeff:.6f}")
        if phi_coeff < 0:
            print(f"  => Klein-Gordon type mass term")
    
    return {
        'coeffs_ols': dict(zip(names_ols, coeffs_ols)),
        'coeffs_sparse': dict(zip(names_ols, coeffs_sparse)),
        'r2_ols': r2_ols,
        'r2_sparse': r2_sparse,
    }


def main():
    parser = argparse.ArgumentParser(description="PDE Discovery for Weitzenböck Torsion Lattice")
    parser.add_argument("--file", type=str, default="pde_telemetry.npz",
                        help="Path to the exported grid telemetry file")
    parser.add_argument("--threshold", type=float, default=0.1,
                        help="STLSQ sparsity threshold")
    parser.add_argument("--subsample_time", type=int, default=1,
                        help="Temporal subsampling factor (1=use all, 2=every other, etc.)")
    parser.add_argument("--subsample_space", type=int, default=1,
                        help="Spatial subsampling factor")
    args = parser.parse_args()
    
    # --- Load Data ---
    print(f"Loading {args.file}...")
    data = np.load(args.file)
    
    phi = data['phi']  # Shape: (T, X, Y)
    dx = float(data['dx'])
    dt_eff = float(data['dt_effective'])
    wave_speed = float(data['wave_speed'])
    torsion_decay = float(data['torsion_decay'])
    sink_mass = float(data['sink_mass'])
    
    print(f"\n--- Grid Telemetry ---")
    print(f"  phi shape:       {phi.shape}")
    print(f"  dx (spatial):    {dx:.6f}")
    print(f"  dt (effective):  {dt_eff:.6f}")
    print(f"  wave_speed:      {wave_speed:.2f}")
    print(f"  torsion_decay:   {torsion_decay}")
    print(f"  sink_mass:       {sink_mass:.2f}")
    print(f"  data range:      [{phi.min():.6f}, {phi.max():.6f}]")
    print(f"  data std:        {phi.std():.6f}")
    
    # Apply subsampling if requested
    # Note: We need a way to pass subsampled data if we want to change 'phi' object itself, 
    # but for simplicity, we pass the original data and rely on derivative logic 
    # if modification of original arrays is not desired.
    
    # --- Sanity Check ---
    if phi.std() < 1e-12:
        print("\n[ERROR] The phi field is effectively zero everywhere.")
        print("[ERROR] The grid may not have been excited. Check that the simulation")
        print("[ERROR] actually placed a mass defect that dents the phi field.")
        sys.exit(1)
    
    # --- Compute Finite Differences ---
    print(f"\nComputing spatial and temporal derivatives...")
    derivs = compute_derivatives(data, dx, dt_eff)
    
    interior_shape = derivs['phi'].shape
    print(f"  Interior grid shape: {interior_shape}")
    print(f"  Total data points:   {np.prod(interior_shape):,}")
    
    # --- Run PDE Discovery ---
    results = run_sindy_pde(derivs, threshold=args.threshold)
    
    # --- Save Results ---
    output_file = args.file.replace('.npz', '_pde_results.npz')
    np.savez(output_file,
        coeffs_ols=np.array(list(results['coeffs_ols'].values())),
        coeffs_sparse=np.array(list(results['coeffs_sparse'].values())),
        feature_names=np.array(list(results['coeffs_ols'].keys())),
        r2_ols=results['r2_ols'],
        r2_sparse=results['r2_sparse'],
        dx=dx,
        dt=dt_eff,
        wave_speed=wave_speed,
        torsion_decay=torsion_decay
    )
    print(f"\nResults saved to {output_file}")
    
    # --- Expected vs Extracted comparison ---
    print(f"\n{'='*60}")
    print(f"GROUND TRUTH COMPARISON")
    print(f"{'='*60}")
    
    C_SQUARED = (wave_speed * (dt / args.subsample_time if args.subsample_time > 1 else data['dt_physics']) / dx * args.subsample_space if args.subsample_space > 1 else (wave_speed * float(data['dt_physics']) / float(data['dx']))) ** 2
    
    # Simpler: the engine computes C_SQUARED = (WAVE_SPEED * DT / DX)^2
    c_sq_engine = (wave_speed * float(data['dt_physics']) / float(data['dx'])) ** 2
    
    print(f"\n  Engine's C² = (c·dt/dx)² = ({wave_speed} × {float(data['dt_physics'])} / {float(data['dx'])})² = {c_sq_engine:.6f}")
    print(f"  Engine's torsion decay = {torsion_decay}")
    
    lap_coeff = results['coeffs_sparse'].get('laplacian', 0.0)
    if abs(lap_coeff) > 1e-6:
        # The PDE in continuous form: phi_tt = c^2 * laplacian
        # But in discrete FDTD: phi_next = 2*phi - phi_prev + C_SQ*laplacian
        # Dividing by dt^2: phi_tt = C_SQ/dt^2 * (dx^2 * laplacian_discrete)
        # Wait — the engine laplacian already uses dx in the kernel convolution
        # The continuous PDE coefficient should be c^2 = WAVE_SPEED^2
        print(f"\n  Extracted laplacian coefficient:  {lap_coeff:.6f}")
        print(f"  Expected (c² = WAVE_SPEED²):     {wave_speed**2:.6f}")
        ratio = lap_coeff / (wave_speed**2) if wave_speed > 0 else 0
        print(f"  Ratio (extracted/expected):       {ratio:.6f}")


if __name__ == "__main__":
    main()
