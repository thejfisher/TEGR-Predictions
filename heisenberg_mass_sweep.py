#!/usr/bin/env python3
"""
TEGR Mass-Sweep Experiment: The Heisenberg Cut
=============================================================

Automates the double-slit protocol across a logarithmic mass range
to find the exact m₀ threshold where quantum interference collapses into
classical behavior.

The TEGR framework predicts decoherence via kinematic phase-shearing
(Weitzenböck torsional wake overloading the Cost of Existence bound).

Usage:
    python heisenberg_mass_sweep.py [--gpu] [--batch_size 10000] [--output results.csv]
"""

import subprocess
import sys
import os
import csv
import json
import math
import time
import argparse

# Fix Windows cp1252 encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────

# Baseline: Preset 43 (MOSFET Plane Wave) parameters — dBB OFF
# These map directly to teleparallel_collider.py argparse keys
BASELINE = {
    "mode": "double-slit",
    "mass_a": 0.511,           # Will be overridden per sweep point
    "mass_b": 1.0,
    "num_particles": 10000,
    "slit_width": 5.0,         # Preset 43 value
    "slit_separation": 6.0,    # Preset 43 value
    "wall_depth": 3,           # 3-layer thick wall (Preset 43)
    "wall_z_layers": 1,
    "num_slits": 2,
    "screen_x": 20.0,
    "beam_start_x": -10.0,
    "beam_momentum": 10.0,
    "wave_speed": 65.0,
    "wave_dissipation": 0.9999,
    "jitter_amp": 0.0,
    "entangled": 0,
    "pauli": 10.0,             # Hardened wall (Preset 43)
    "pauli_power": 3,          # KK signature (1/r^3)
    "vacuum": 0.007,           # Preset 43 vacuum coupling
    "torsion": 1.0,            # Preset 43 torsion
    "pilot_wave": 1,           # Pilot wave ON
    "dbb_guidance": 0,         # *** dBB OFF per user directive ***
    "dbb_strength": 0.01,
    "photon_emission": 0,
    "breit_wheeler": 0,
    "bw_threshold": 2.044,
    "plane_wave_init": 1,      # Plane wave ON
    "plane_wave_amp": 20.0,    # Resonant amplitude
    "paper1_exact": 0,
    "spin_coupling": 0,
    "device": "cuda",          # *** GPU mode ***
}


# Mass sweep: logarithmic spacing from sub-electron to heavy particle
DEFAULT_MASSES = [
    0.1, 0.2, 0.3, 0.511,       # Sub-electron -> electron
    0.75, 1.0, 2.0, 5.0,         # Light particles
    10.0, 20.0, 50.0, 100.0,     # Medium
    200.0, 500.0, 938.27,         # Up to proton
    2000.0, 5000.0, 10000.0,      # Heavy
    50000.0, 100000.0,            # Very heavy (approaching classical)
]

# Baseline electron parameters for scaling
M0_ELECTRON = 0.511
DT_BASE = 0.001
TICKS_BASE = 3000
BATCH_BASE = 10000


def compute_dt(m0: float) -> float:
    """Scale dt to keep CFL condition stable as m0 increases.
    
    Higher mass → faster phase oscillation → need smaller dt.
    Scaling: dt ∝ 1/sqrt(m0/m0_e) keeps the Courant number bounded.
    """
    ratio = m0 / M0_ELECTRON
    if ratio <= 1.0:
        return DT_BASE
    return DT_BASE / math.sqrt(ratio)


def compute_ticks(m0: float, dt: float) -> int:
    """Scale total ticks to maintain equivalent physical time.
    
    Since we shrink dt, we need more ticks to cover the same time span.
    Physical time = ticks × dt. Keep physical_time = TICKS_BASE × DT_BASE.
    """
    target_time = TICKS_BASE * DT_BASE  # = 3.0 time units
    ticks = int(target_time / dt)
    # Cap at reasonable values
    return min(ticks, 100000)


def run_single_mass(m0: float, batch_size: int, collider_path: str,
                    run_index: int, total_runs: int) -> dict:
    """Run the Tonomura batch for a single mass value and parse results."""
    
    dt = compute_dt(m0)
    ticks = compute_ticks(m0, dt)
    
    print(f"\n{'='*60}")
    print(f"  RUN {run_index}/{total_runs}: m₀ = {m0:.4f}")
    print(f"  dt = {dt:.6f} | ticks = {ticks} | batch = {batch_size}")
    print(f"{'='*60}")
    
    # Build command — uses exact CLI keys from teleparallel_collider.py argparse
    run_label = f"Heisenberg Cut Sweep: m={m0}"
    cmd = [
        sys.executable, collider_path,
        "--mode", BASELINE["mode"],
        "--mass_a", str(m0),
        "--mass_b", str(BASELINE["mass_b"]),
        "--num_particles", str(BASELINE["num_particles"]),
        "--dt", str(dt),
        "--total_ticks", str(ticks),
        "--batch_size", str(batch_size),
        "--slit_width", str(BASELINE["slit_width"]),
        "--slit_separation", str(BASELINE["slit_separation"]),
        "--wall_depth", str(BASELINE["wall_depth"]),
        "--wall_z_layers", str(BASELINE["wall_z_layers"]),
        "--num_slits", str(BASELINE["num_slits"]),
        "--screen_x", str(BASELINE["screen_x"]),
        "--beam_start_x", str(BASELINE["beam_start_x"]),
        "--beam_momentum", str(BASELINE["beam_momentum"]),
        "--wave_speed", str(BASELINE["wave_speed"]),
        "--wave_dissipation", str(BASELINE["wave_dissipation"]),
        "--jitter_amp", str(BASELINE["jitter_amp"]),
        "--entangled", str(BASELINE["entangled"]),
        "--pauli", str(BASELINE["pauli"]),
        "--pauli_power", str(BASELINE["pauli_power"]),
        "--vacuum", str(BASELINE["vacuum"]),
        "--torsion", str(BASELINE["torsion"]),
        "--pilot_wave", str(BASELINE["pilot_wave"]),
        "--dbb_guidance", str(BASELINE["dbb_guidance"]),
        "--dbb_strength", str(BASELINE["dbb_strength"]),
        "--breit_wheeler", str(BASELINE["breit_wheeler"]),
        "--bw_threshold", str(BASELINE["bw_threshold"]),
        "--plane_wave_init", str(BASELINE["plane_wave_init"]),
        "--plane_wave_amp", str(BASELINE["plane_wave_amp"]),
        "--paper1_exact", str(BASELINE["paper1_exact"]),
        "--spin_coupling", str(BASELINE["spin_coupling"]),
        "--device", BASELINE["device"],
        "--run_label", run_label,
    ]

    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max per run
            cwd=os.path.dirname(collider_path)
        )
        elapsed = time.time() - start_time
        
        # Parse the output for key metrics
        output = result.stdout + result.stderr
        metrics = parse_output(output, m0, dt, ticks, batch_size, elapsed)
        
        if result.returncode != 0:
            metrics["status"] = "ERROR"
            metrics["error"] = result.stderr[-500:] if result.stderr else "Unknown error"
            print(f"  ⚠ ERROR (exit code {result.returncode})")
        else:
            metrics["status"] = "OK"
            print(f"  ✓ Completed in {elapsed:.1f}s")
        
        return metrics
        
    except subprocess.TimeoutExpired:
        return {
            "m0": m0, "dt": dt, "ticks": ticks, "batch_size": batch_size,
            "elapsed_s": 600, "status": "TIMEOUT",
            "band_visibility": None, "spatial_sigma": None,
            "kappa_coupling": None, "phase_coherence": None,
            "screen_hits": 0
        }
    except Exception as e:
        return {
            "m0": m0, "dt": dt, "ticks": ticks, "batch_size": batch_size,
            "elapsed_s": 0, "status": f"EXCEPTION: {e}",
            "band_visibility": None, "spatial_sigma": None,
            "kappa_coupling": None, "phase_coherence": None,
            "screen_hits": 0
        }


def parse_output(output: str, m0: float, dt: float, ticks: int, 
                 batch_size: int, elapsed: float) -> dict:
    """Extract decoherence metrics from the collider's stdout."""
    
    metrics = {
        "m0": m0,
        "dt": dt,
        "ticks": ticks,
        "batch_size": batch_size,
        "elapsed_s": round(elapsed, 2),
        "band_visibility": None,
        "spatial_sigma": None,
        "kappa_coupling": None,
        "phase_coherence": None,
        "screen_hits": 0,
        "bands_detected": None,
        "band_count": 0,
        "slit_to_blob_distance": None,
    }
    
    for line in output.split("\n"):
        line = line.strip()
        
        # Look for band analysis output
        if "visibility" in line.lower() and "=" in line:
            try:
                val = float(line.split("=")[-1].strip().rstrip("%"))
                if val > 1.0:
                    val /= 100.0  # Convert percentage
                metrics["band_visibility"] = round(val, 6)
            except (ValueError, IndexError):
                pass
        
        if "sigma" in line.lower() and "=" in line:
            try:
                metrics["spatial_sigma"] = float(line.split("=")[-1].strip())
            except (ValueError, IndexError):
                pass
        
        if "kappa" in line.lower() and "=" in line:
            try:
                metrics["kappa_coupling"] = float(line.split("=")[-1].strip())
            except (ValueError, IndexError):
                pass
        
        if "screen_hits" in line.lower() or "arrivals" in line.lower():
            try:
                val = line.split("=")[-1].strip().split()[0]
                metrics["screen_hits"] = int(val.replace(",", ""))
            except (ValueError, IndexError):
                pass
        
        if "bands" in line.lower() and ("found" in line.lower() or "detected" in line.lower()):
            try:
                val = int(''.join(c for c in line.split(":")[-1] if c.isdigit()))
                metrics["band_count"] = val
                metrics["bands_detected"] = val > 0
            except (ValueError, IndexError):
                pass
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="TEGR Mass-Sweep: The Heisenberg Cut")
    parser.add_argument("--batch_size", type=int, default=BATCH_BASE, help="Particles per batch")
    parser.add_argument("--output", type=str, default="mass_sweep_results.csv", help="Output CSV path")
    parser.add_argument("--masses", type=str, default=None, 
                        help="Comma-separated list of m0 values (overrides defaults)")
    parser.add_argument("--collider", type=str, default="teleparallel_collider.py",
                        help="Path to collider script")
    parser.add_argument("--dry_run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()
    
    # Resolve collider path
    collider_path = os.path.abspath(args.collider)
    if not os.path.exists(collider_path):
        print(f"ERROR: Collider not found at {collider_path}")
        sys.exit(1)
    
    # Parse mass list
    if args.masses:
        masses = [float(x.strip()) for x in args.masses.split(",")]
    else:
        masses = DEFAULT_MASSES
    
    print(f"{'='*60}")
    print(f"  TEGR MASS-SWEEP: The Heisenberg Cut")
    print(f"  Masses to sweep: {len(masses)} values")
    print(f"  Range: m₀ = {min(masses):.4f} → {max(masses):.1f}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Device: {BASELINE['device']}")
    print(f"  Output: {args.output}")
    print(f"  Collider: {collider_path}")
    print(f"{'='*60}")
    
    if args.dry_run:
        print("\n[DRY RUN] Would execute the following runs:")
        for i, m0 in enumerate(masses, 1):
            dt = compute_dt(m0)
            ticks = compute_ticks(m0, dt)
            print(f"  {i:3d}. m₀={m0:>10.4f}  dt={dt:.6f}  ticks={ticks:>6d}")
        return
    
    # Run the sweep
    all_results = []
    
    for i, m0 in enumerate(masses, 1):
        result = run_single_mass(m0, args.batch_size, collider_path, i, len(masses))
        all_results.append(result)
        
        # Write incrementally so we don't lose data on crash
        write_csv(all_results, args.output)
        
        # Brief summary
        v = result.get("band_visibility")
        s = result.get("spatial_sigma")
        k = result.get("kappa_coupling")
        status = result.get("status", "?")
        print(f"  → Visibility={v}  σ={s}  κ={k}  [{status}]")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"  SWEEP COMPLETE: {len(all_results)} runs")
    print(f"  Results saved to: {args.output}")
    print(f"{'='*60}")
    
    # Print transition summary
    print("\n  Mass vs Band Visibility:")
    print(f"  {'m₀':>12s}  {'Visibility':>12s}  {'σ':>10s}  {'Bands':>6s}")
    print(f"  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*6}")
    for r in all_results:
        v = f"{r['band_visibility']:.4f}" if r['band_visibility'] is not None else "N/A"
        s = f"{r['spatial_sigma']:.4f}" if r['spatial_sigma'] is not None else "N/A"
        b = str(r.get('band_count', '?'))
        print(f"  {r['m0']:>12.4f}  {v:>12s}  {s:>10s}  {b:>6s}")


def write_csv(results: list, path: str):
    """Write results to CSV, overwriting each time (incremental save)."""
    if not results:
        return
    
    fieldnames = list(results[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
