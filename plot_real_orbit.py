"""
=============================================================
  TEGR: Bodies of Orbit -- Venus Elliptical Analysis (REAL RUN)
=============================================================
  Loads electron_trajectory.npy from the latest simulation run
  and plots the trajectory to prove the "training wheels"
  worked and the SINDy equations held the orbit in free-flight!
"""

import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    print("Loading electron_trajectory.npy...")
    traj = np.load("electron_trajectory.npy")
    
    # Shape is (8000, 2, 12)
    # Particle 0 is Venus, Particle 1 is the Sun
    
    pos_x = traj[:, 0, 1]
    pos_y = traj[:, 0, 2]
    
    # We know the first 4000 ticks were on rails (Training Wheels)
    # And the last 4000 ticks were free flight!
    
    plt.style.use('dark_background')
    plt.figure(figsize=(10, 10))
    
    # Plot Sun
    plt.scatter([0], [0], color='yellow', s=300, zorder=5, label="Sun (Mass=408670)")
    
    # Plot Training Wheels Orbit (first 4000)
    plt.plot(pos_x[:4000], pos_y[:4000], color='cyan', linewidth=2.5, alpha=0.8, label="Tracks ON (Ticks 0-4000)")
    
    # Plot Free Flight Orbit (last 4000)
    plt.plot(pos_x[4000:], pos_y[4000:], color='magenta', linewidth=2.5, alpha=0.8, linestyle='--', label="Free Flight (Ticks 4000-8000)")
    
    # Mark start and end
    plt.scatter(pos_x[0], pos_y[0], color='cyan', s=100, marker='o', zorder=10, label="Start")
    plt.scatter(pos_x[4000], pos_y[4000], color='white', s=100, marker='*', zorder=10, label="Tracks Turned OFF")
    plt.scatter(pos_x[-1], pos_y[-1], color='magenta', s=100, marker='X', zorder=10, label="End of Sim")
    
    plt.title("Venus Elliptical Orbit: Training Wheels Test", fontsize=16, color='white', pad=20)
    plt.xlabel("X Position (r_0 = 20.0)", fontsize=12)
    plt.ylabel("Y Position (r_0 = 20.0)", fontsize=12)
    plt.axis('equal')
    plt.grid(True, alpha=0.2)
    plt.legend(loc='upper right', fontsize=10)
    
    out_file = "training_wheels_orbit.png"
    plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"Saved {out_file}")
    
    # Plot radius over time to see the wobble and stability
    plt.figure(figsize=(12, 6))
    r = np.sqrt(pos_x**2 + pos_y**2)
    
    plt.plot(np.arange(4000), r[:4000], color='cyan', label="Tracks ON")
    plt.plot(np.arange(4000, 8000), r[4000:], color='magenta', label="Free Flight")
    plt.axvline(4000, color='white', linestyle=':', alpha=0.5, label="Tracks OFF")
    
    plt.title("Orbital Radius over Time", fontsize=16, color='white', pad=20)
    plt.xlabel("Simulation Ticks", fontsize=12)
    plt.ylabel("Radius", fontsize=12)
    plt.grid(True, alpha=0.2)
    plt.legend(loc='upper right', fontsize=10)
    
    out_file2 = "training_wheels_radius.png"
    plt.savefig(out_file2, dpi=300, bbox_inches='tight', facecolor='#111111')
    print(f"Saved {out_file2}")
    
if __name__ == "__main__":
    main()
