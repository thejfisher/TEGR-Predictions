"""
=============================================================
  TEGR: Bodies of Orbit -- Venus Elliptical Analysis
  Preset 63 Post-Run Visualization
=============================================================
  Generates publication-quality plots from the Keplerian
  parameters and SINDy-extracted coefficients.
  NO remote data needed -- everything computed locally.

  Usage:  python analyze_venus_orbit.py
=============================================================
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os, sys, webbrowser, math

# -- Configuration -------------------------------------------------
DT        = 0.001
OMEGA     = 1.5708        # Mean motion (pi/2 rad/s)
A_ORB     = 20.0          # Semi-major axis
ECC       = 0.0067        # Venus eccentricity
SUN_MASS  = 408670.0      # Anchor mass (MeV)
N_TICKS   = 8000          # Total simulation ticks
OUTPUT_DIR = "./venus_analysis_plots"

# -- Keplerian constants -------------------------------------------
GM_KEPLER = OMEGA**2 * A_ORB**3   # n^2 * a^3
R_PERI    = A_ORB * (1 - ECC)     # 19.866
R_APH     = A_ORB * (1 + ECC)     # 20.134

# -- SINDy-extracted coefficients (average of 2 reproducible runs) -
# Run 1: vx' = -19729.010 x/r^3    vy' = -19735.084 y/r^3
# Run 2: vx' = -19727.690 x/r^3    vy' = -19738.342 y/r^3
GM_SINDY_VX = (-19729.010 + -19727.690) / 2.0  # -19728.35
GM_SINDY_VY = (-19735.084 + -19738.342) / 2.0  # -19736.71
GM_SINDY    = (abs(GM_SINDY_VX) + abs(GM_SINDY_VY)) / 2.0  # 19732.53

# -- Pretty plot styling -------------------------------------------
plt.rcParams.update({
    "figure.facecolor":  "#0d1117",
    "axes.facecolor":    "#161b22",
    "axes.edgecolor":    "#30363d",
    "axes.labelcolor":   "#c9d1d9",
    "text.color":        "#c9d1d9",
    "xtick.color":       "#8b949e",
    "ytick.color":       "#8b949e",
    "grid.color":        "#21262d",
    "grid.alpha":        0.6,
    "font.family":       "sans-serif",
    "font.size":         11,
})

VENUS   = "#f0883e"
SUN     = "#ffd700"
KAPPA   = "#58a6ff"
RADIAL  = "#7ee787"
AX_COL  = "#ff7b72"
AY_COL  = "#d2a8ff"
PHASE   = "#79c0ff"
DIM     = "#484f58"

# ==================================================================
#  RECONSTRUCT KEPLERIAN ORBIT (same solver as the collider)
# ==================================================================
print("=" * 60)
print("  TEGR: Venus Elliptical Orbit Analysis (Preset 63)")
print("=" * 60)

def solve_kepler(M, e, tol=1e-12, max_iter=50):
    E = M
    for _ in range(max_iter):
        dE = (M - E + e * math.sin(E)) / (1 - e * math.cos(E))
        E += dE
        if abs(dE) < tol:
            break
    return E

t_arr  = np.arange(N_TICKS) * DT
x_arr  = np.zeros(N_TICKS)
y_arr  = np.zeros(N_TICKS)
vx_arr = np.zeros(N_TICKS)
vy_arr = np.zeros(N_TICKS)
r_arr  = np.zeros(N_TICKS)

print("\n  Reconstructing Keplerian orbit (8000 ticks)...")
for i, t in enumerate(t_arr):
    M = OMEGA * t
    E = solve_kepler(M, ECC)

    theta = 2.0 * math.atan2(
        math.sqrt(1 + ECC) * math.sin(E / 2),
        math.sqrt(1 - ECC) * math.cos(E / 2))

    r = A_ORB * (1 - ECC * math.cos(E))
    r_arr[i]  = r
    x_arr[i]  = r * math.cos(theta)
    y_arr[i]  = r * math.sin(theta)

    dE_dt = OMEGA / (1 - ECC * math.cos(E))
    h = OMEGA * A_ORB**2 * math.sqrt(1 - ECC**2)
    dtheta_dt = h / (r * r)
    dr_dt = A_ORB * ECC * math.sin(E) * dE_dt

    vx_arr[i] = dr_dt * math.cos(theta) - r * dtheta_dt * math.sin(theta)
    vy_arr[i] = dr_dt * math.sin(theta) + r * dtheta_dt * math.cos(theta)

# Derived quantities
v_mag  = np.sqrt(vx_arr**2 + vy_arr**2)
ax_arr = np.gradient(vx_arr, DT)
ay_arr = np.gradient(vy_arr, DT)
a_mag  = np.sqrt(ax_arr**2 + ay_arr**2)
theta_arr = np.arctan2(y_arr, x_arr)

n_orbits = t_arr[-1] * OMEGA / (2 * np.pi)

print(f"  Semi-major axis:  {A_ORB}")
print(f"  Eccentricity:     {ECC}")
print(f"  Perihelion:       {R_PERI:.3f}    (measured min r: {r_arr.min():.4f})")
print(f"  Aphelion:         {R_APH:.3f}    (measured max r: {r_arr.max():.4f})")
print(f"  GM (Kepler):      {GM_KEPLER:.2f}")
print(f"  GM (SINDy avg):   {GM_SINDY:.2f}")
print(f"  Agreement:        {abs(GM_KEPLER - GM_SINDY)/GM_KEPLER * 100:.3f}%")
print(f"  Total sim time:   {t_arr[-1]:.1f}s  ({n_orbits:.2f} orbits)")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================================================================
#  FIGURE 1 : Orbital Trajectory (XY plane)
# ==================================================================
print("\n  [1/5] Orbital Trajectory...")

fig1, ax1 = plt.subplots(figsize=(10, 10))
pts = ax1.scatter(x_arr, y_arr, c=t_arr, cmap="plasma", s=1.5, alpha=0.8, zorder=2)
plt.colorbar(pts, ax=ax1, label="Time (s)", shrink=0.8)

ax1.plot(0, 0, marker="*", color=SUN, markersize=22, zorder=5,
         markeredgecolor="#b8860b", markeredgewidth=1)
ax1.annotate("Sun (408,670 MeV)", (0, 0), textcoords="offset points",
             xytext=(15, 15), color=SUN, fontsize=10, fontweight="bold")

i_peri = np.argmin(r_arr)
i_aph  = np.argmax(r_arr)
ax1.plot(x_arr[i_peri], y_arr[i_peri], "v", color=RADIAL, markersize=12, zorder=5)
ax1.annotate(f"Perihelion\nr={r_arr[i_peri]:.3f}",
             (x_arr[i_peri], y_arr[i_peri]),
             textcoords="offset points", xytext=(-60, -25),
             color=RADIAL, fontsize=9)
ax1.plot(x_arr[i_aph], y_arr[i_aph], "^", color=AX_COL, markersize=12, zorder=5)
ax1.annotate(f"Aphelion\nr={r_arr[i_aph]:.3f}",
             (x_arr[i_aph], y_arr[i_aph]),
             textcoords="offset points", xytext=(10, 10),
             color=AX_COL, fontsize=9)

# Reference circle
ang = np.linspace(0, 2*np.pi, 500)
ax1.plot(A_ORB*np.cos(ang), A_ORB*np.sin(ang),
         "--", color=DIM, lw=0.8, alpha=0.5, label="Perfect circle (r = 20)")

ax1.set_xlabel("x (grid units)")
ax1.set_ylabel("y (grid units)")
ax1.set_title("Preset 63: Venus Keplerian Ellipse  (e = 0.0067)\n"
              "Colored by simulation time",
              fontsize=14, fontweight="bold", color=VENUS)
ax1.set_aspect("equal")
ax1.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d")
ax1.grid(True, alpha=0.3)
fig1.tight_layout()
p1 = os.path.join(OUTPUT_DIR, "01_venus_trajectory.png")
fig1.savefig(p1, dpi=150, bbox_inches="tight"); plt.close(fig1)
print(f"    -> {p1}")


# ==================================================================
#  FIGURE 2 : Radial Oscillation & Velocity
# ==================================================================
print("  [2/5] Radial Oscillation & Velocity...")

fig2, (ax_r, ax_v) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

ax_r.plot(t_arr, r_arr, color=RADIAL, lw=1.0)
ax_r.axhline(R_PERI, ls="--", color=RADIAL, alpha=0.4, label=f"Perihelion = {R_PERI:.3f}")
ax_r.axhline(R_APH,  ls="--", color=AX_COL, alpha=0.4, label=f"Aphelion = {R_APH:.3f}")
ax_r.axhline(A_ORB,  ls=":",  color=DIM,    alpha=0.3, label=f"a = {A_ORB}")
ax_r.fill_between(t_arr, R_PERI, R_APH, alpha=0.07, color=RADIAL)
ax_r.set_ylabel("r (grid units)")
ax_r.set_title("Radial Distance: The Elliptical Wobble That Broke the Multicollinearity",
               fontsize=12, fontweight="bold", color=RADIAL)
ax_r.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d", fontsize=9)
ax_r.grid(True, alpha=0.3)

ax_v.plot(t_arr, v_mag, color=VENUS, lw=0.8, label="|v| (orbital speed)")
# Vis-viva: v = sqrt(GM * (2/r - 1/a))
v_visviva = np.sqrt(GM_KEPLER * (2.0/r_arr - 1.0/A_ORB))
ax_v.plot(t_arr, v_visviva, "--", color=DIM, lw=1.0, alpha=0.6, label="Vis-viva prediction")
ax_v.set_ylabel("|v|")
ax_v.set_xlabel("Time (s)")
ax_v.set_title("Orbital Speed: Faster at Perihelion, Slower at Aphelion (Kepler II)",
               fontsize=12, fontweight="bold", color=VENUS)
ax_v.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d", fontsize=9)
ax_v.grid(True, alpha=0.3)
fig2.tight_layout()
p2 = os.path.join(OUTPUT_DIR, "02_radial_velocity.png")
fig2.savefig(p2, dpi=150, bbox_inches="tight"); plt.close(fig2)
print(f"    -> {p2}")


# ==================================================================
#  FIGURE 3 : Acceleration Decomposition
# ==================================================================
print("  [3/5] Acceleration Decomposition...")

fig3, (ax_a, ax_res, ax_mag) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

ax_a.plot(t_arr, ax_arr, color=AX_COL, lw=0.6, alpha=0.8, label="ax")
ax_a.plot(t_arr, ay_arr, color=AY_COL, lw=0.6, alpha=0.8, label="ay")
ax_a.set_ylabel("Acceleration")
ax_a.set_title("Centripetal Acceleration Components",
               fontsize=12, fontweight="bold", color=AX_COL)
ax_a.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d")
ax_a.grid(True, alpha=0.3)

# Theoretical: a = -GM * pos / r^3
ax_th = -GM_KEPLER * x_arr / r_arr**3
ay_th = -GM_KEPLER * y_arr / r_arr**3
ax_res.plot(t_arr, ax_arr - ax_th, color=AX_COL, lw=0.5, alpha=0.7, label="dx residual")
ax_res.plot(t_arr, ay_arr - ay_th, color=AY_COL, lw=0.5, alpha=0.7, label="dy residual")
ax_res.set_ylabel("Residual")
ax_res.set_title("Acceleration Residual:  Measured - (-GM * pos/r^3)",
               fontsize=12, fontweight="bold", color="#c9d1d9")
ax_res.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d")
ax_res.grid(True, alpha=0.3)

a_th_mag = GM_KEPLER / r_arr**2
ax_mag.plot(t_arr, a_mag, color=VENUS, lw=0.8, alpha=0.8, label="|a| computed")
ax_mag.plot(t_arr, a_th_mag, "--", color=DIM, lw=1.0, alpha=0.6, label="|a| = GM/r^2")
ax_mag.set_ylabel("|a|")
ax_mag.set_xlabel("Time (s)")
ax_mag.set_title("Acceleration Magnitude vs Newtonian Prediction",
               fontsize=12, fontweight="bold", color=VENUS)
ax_mag.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d")
ax_mag.grid(True, alpha=0.3)
fig3.tight_layout()
p3 = os.path.join(OUTPUT_DIR, "03_acceleration.png")
fig3.savefig(p3, dpi=150, bbox_inches="tight"); plt.close(fig3)
print(f"    -> {p3}")


# ==================================================================
#  FIGURE 4 : SINDy Coefficient Summary
# ==================================================================
print("  [4/5] SINDy Coefficient Summary...")

fig4 = plt.figure(figsize=(16, 9))
gs = GridSpec(2, 2, figure=fig4, hspace=0.35, wspace=0.3)

# ---- Panel A: vx' coefficients ----
ax_vx = fig4.add_subplot(gs[0, 0])
vx_labels = ["x/r^3",  "1/r^3",  "1/d12^3", "1/r^2",
             "1/d12^2", "kappa",   "r",       "Torsion Wy", "Torsion Wx"]
vx_vals   = [-19727.69, -2344.77, -2254.91, -50.32,
             -44.81,     8.43,     0.015,     0.151,         0.065]
cols_vx = [AX_COL if v < -1 else KAPPA if abs(v) > 1 else DIM for v in vx_vals]
ax_vx.barh(range(len(vx_labels)), vx_vals, color=cols_vx, alpha=0.85, edgecolor="#30363d")
ax_vx.set_yticks(range(len(vx_labels))); ax_vx.set_yticklabels(vx_labels)
ax_vx.set_xlabel("Coefficient"); ax_vx.axvline(0, color=DIM, lw=0.5)
ax_vx.set_title("vx'  Coefficients   (R^2 = 1.0000)", fontweight="bold", color=AX_COL)
ax_vx.grid(True, alpha=0.2, axis="x")

# ---- Panel B: vy' coefficients ----
ax_vy = fig4.add_subplot(gs[0, 1])
vy_labels = ["y/r^3",  "1/r^3",  "1/d12^3", "x/r^3",
             "1/r^2",  "1/d12^2", "kappa",   "Torsion Wy", "Torsion Wx"]
vy_vals   = [-19738.34, 56.31,    47.52,     5.87,
             -0.52,    -0.39,    -0.37,      0.14,         -0.02]
cols_vy = [AY_COL if v < -1 else KAPPA if abs(v) > 1 else DIM for v in vy_vals]
ax_vy.barh(range(len(vy_labels)), vy_vals, color=cols_vy, alpha=0.85, edgecolor="#30363d")
ax_vy.set_yticks(range(len(vy_labels))); ax_vy.set_yticklabels(vy_labels)
ax_vy.set_xlabel("Coefficient"); ax_vy.axvline(0, color=DIM, lw=0.5)
ax_vy.set_title("vy'  Coefficients   (R^2 = 1.0000)", fontweight="bold", color=AY_COL)
ax_vy.grid(True, alpha=0.2, axis="x")

# ---- Panel C: r'' coefficients ----
ax_rr = fig4.add_subplot(gs[1, 0])
rr_labels = ["x/r^3", "1/r^3", "1/d12^3", "1/r^2", "1/d12^2", "F_torsion", "Torsion Wy"]
rr_vals   = [131.52,   15.06,   15.00,     0.30,    0.30,       0.025,      -0.017]
cols_rr = [RADIAL if abs(v) > 1 else DIM for v in rr_vals]
ax_rr.barh(range(len(rr_labels)), rr_vals, color=cols_rr, alpha=0.85, edgecolor="#30363d")
ax_rr.set_yticks(range(len(rr_labels))); ax_rr.set_yticklabels(rr_labels)
ax_rr.set_xlabel("Coefficient"); ax_rr.axvline(0, color=DIM, lw=0.5)
ax_rr.set_title("r''  Coefficients   (R^2 = 1.0000)", fontweight="bold", color=RADIAL)
ax_rr.grid(True, alpha=0.2, axis="x")

# ---- Panel D: Summary callout ----
ax_t = fig4.add_subplot(gs[1, 1]); ax_t.axis("off")
agreement = abs(GM_KEPLER - GM_SINDY) / GM_KEPLER * 100
summary = (
    "--------------------------------------------\n"
    "   PRESET 63  RESULTS  SUMMARY\n"
    "--------------------------------------------\n\n"
    f"   GM  (Kepler):    {GM_KEPLER:>10.2f}\n"
    f"   GM  (SINDy):     {GM_SINDY:>10.2f}\n"
    f"   Agreement:       {agreement:>10.3f}%\n\n"
    "   -- Feature Isolation --\n\n"
    "   Torsion / GM  =  0.0008%\n"
    "   (Grid torsion does NOT\n"
    "    drive the orbit)\n\n"
    "   Curvature kappa in vx':  8.43\n"
    "   (Grid bends in response to\n"
    "    perihelion/aphelion wobble)\n\n"
    "   r'' equation:  R^2 = 1.0000\n"
    "   (Radial oscillation fully\n"
    "    captured for the first time)\n"
)
ax_t.text(0.05, 0.95, summary, transform=ax_t.transAxes,
          fontsize=11, va="top", fontfamily="monospace", color="#c9d1d9",
          bbox=dict(boxstyle="round,pad=0.5", fc="#0d1117",
                    ec=VENUS, lw=2))

fig4.suptitle("SINDy Extracted Equations  --  Venus Elliptical Orbit (Preset 63)",
              fontsize=16, fontweight="bold", color=VENUS, y=0.98)
p4 = os.path.join(OUTPUT_DIR, "04_sindy_coefficients.png")
fig4.savefig(p4, dpi=150, bbox_inches="tight"); plt.close(fig4)
print(f"    -> {p4}")


# ==================================================================
#  FIGURE 5 : Multicollinearity Comparison (Circle vs Ellipse)
# ==================================================================
print("  [5/5] Multicollinearity Comparison...")

fig5, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left panel: CIRCLE (what Preset 62 looks like)
th_circ = np.linspace(0, 4*np.pi, 2000)
x_circ  = A_ORB * np.cos(th_circ)
r_circ  = np.full_like(x_circ, A_ORB)
xr3_circ = x_circ / r_circ**3

ax_L = axes[0]
ax_L.scatter(x_circ, xr3_circ, c=th_circ, cmap="coolwarm", s=2, alpha=0.7)
ax_L.set_xlabel("x")
ax_L.set_ylabel("x / r^3")
ax_L.set_title("Preset 62: Perfect Circle\ncorr(x, x/r^3) = 1.0000",
               fontsize=12, fontweight="bold", color=AX_COL)
ax_L.grid(True, alpha=0.3)

# Right panel: ELLIPSE (Preset 63)
xr3_ell = x_arr / r_arr**3
ax_R = axes[1]
sc = ax_R.scatter(x_arr, xr3_ell, c=t_arr, cmap="plasma", s=2, alpha=0.7)
plt.colorbar(sc, ax=ax_R, label="Time (s)", shrink=0.8)
corr = np.corrcoef(x_arr, xr3_ell)[0, 1]
ax_R.set_xlabel("x")
ax_R.set_ylabel("x / r^3")
ax_R.set_title(f"Preset 63: Keplerian Ellipse (e=0.0067)\n"
               f"corr(x, x/r^3) = {corr:.4f}",
               fontsize=12, fontweight="bold", color=RADIAL)
ax_R.grid(True, alpha=0.3)

fig5.suptitle("Why Eccentricity Matters: Breaking the Multicollinearity",
              fontsize=14, fontweight="bold", color="#c9d1d9")
fig5.tight_layout(rect=[0, 0, 1, 0.93])
p5 = os.path.join(OUTPUT_DIR, "05_multicollinearity_comparison.png")
fig5.savefig(p5, dpi=150, bbox_inches="tight"); plt.close(fig5)
print(f"    -> {p5}")


# ==================================================================
#  OPEN ALL PLOTS
# ==================================================================
plots = [p1, p2, p3, p4, p5]
print(f"\n  All plots saved to: {os.path.abspath(OUTPUT_DIR)}")
print("  Opening...\n")
for p in plots:
    a = os.path.abspath(p)
    print(f"    {os.path.basename(p)}")
    webbrowser.open(f"file:///{a}")

print("\n" + "=" * 60)
print("  Done!  5 plots opened in your default image viewer.")
print("=" * 60)
