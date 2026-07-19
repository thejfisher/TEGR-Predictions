# Lab Notes: Project "Mavity"

**Date:** July 18, 2026
**Topic:** Extracting the "Cost of Existence" PDE via SINDy from a discrete topological matrix.
**Objective:** Explore how macroscopic gravity ($G_{eff}$) might emerge from a topological field (the WeitzenbÃ¶ck lattice) by extracting the field's underlying Partial Differential Equation (PDE).

---

## 1. The Core Hypothesis

In classical physics engines, gravity is hardcoded using Newton's Universal Gravitational Constant ($G = 6.674 \times 10^{-11}$). 

In the TEGR (Teleparallel Equivalent of General Relativity) Colliderâ€”building upon Einstein's 1928 exploration of teleparallelism (torsion without curvature)â€”we do not hardcode gravity. Instead, we define a flat topological geometry (the expanded WeitzenbÃ¶ck matrix, $\phi$). Mass defects placed in this lattice cause it to warp. The localized processing the matrix must perform to accommodate these defects is the **Cost of Existence**.

We have already observed that this emergent topology creates an effective gravitational constant:
$$G_{eff} \approx 0.04828$$
(for a wave speed of $c=100.0$ and dissipation $\alpha=0.999$)

Our goal is to use Sparse Identification of Nonlinear Dynamics (PySINDy) to blindly discover the PDE that governs this continuous, localized spatial processing.

## 2. Experimental Setup: The Reference Frame Problem

To find the PDE, we must feed PySINDy the spatial grid telemetry ($\phi$). But *how* we record this telemetry changes the physics.

**The Lagrangian Mistake (Moving Camera)**
If we center our telemetry crop on the moving tracker particle (Venus), we place PySINDy in a non-inertial reference frame. The stationary matrix would appear to be flowing backward past the camera. SINDy would interpret this grid movement as massive advection currents ($\vec{v} \cdot \nabla\phi$) and pollute the foundational PDE with artificial velocity gradients.

**The Eulerian Solution (Anchored Camera)**
We must center our telemetry crop on the static anchor defect (the Sun) at the origin. This locks the camera to the inertial rest frame of the WeitzenbÃ¶ck lattice. SINDy will observe the pure, unpolluted diffusion and torsion PDEs as Venus sweeps *through* the stationary frame.

## 3. Data Extraction Pipeline (Code Annotations)

To prevent memory overflow (saving an 800x800 grid 8,000 times = ~20 GB), we implemented a localized "tracking crop" in `teleparallel_collider.py`.

### A. The Telemetry Export Logic
```python
# --- PDE Grid Export Buffer ---
# We initialize a buffer and define a bounding box centered on the origin (the Sun).
pde_buffer = []
if args.export_pde_grid:
    pde_half_phys = args.pde_crop_size / 2.0  # e.g., 30 units
    pde_half_px = int(pde_half_phys / DX)     
    pde_center = GRID_RES // 2                # Anchored to the Sun (Eulerian frame)
    pde_i0 = max(0, pde_center - pde_half_px)
    pde_i1 = min(GRID_RES, pde_center + pde_half_px)

# ... inside the main physics loop ...

# --- PDE Grid Export: Crop 2D z-slice ---
if args.export_pde_grid and tick % args.pde_save_interval == 0:
    # We only take a 2D slice through the orbital plane (z_center).
    # This bypasses the curse of dimensionality for PySINDy while capturing all diffusion.
    z_center = GRID_RES // 2
    phi_slice = phi_curr[0, 0, pde_i0:pde_i1, pde_i0:pde_i1, z_center].cpu().numpy().copy()
    pde_buffer.append(phi_slice)
```
*Why we did this:* We need finite differences to compute $\nabla^2 \phi$. PySINDy cannot compute a Laplacian from a single point measurement; it needs the surrounding pixels. The 2D crop provides exactly enough spatial context without overloading RAM. We subsample every 10 ticks to keep the dataset in the "Goldilocks zone" (dense enough to avoid aliasing, sparse enough for STLSQ to solve).

### B. The PySINDy Discovery Script
We built `sindy_pde_discovery.py` to read `pde_telemetry.npz`.

```python
def compute_finite_differences(phi, dx, dt):
    # We manually compute centered finite differences because the grid is uniform.
    # We trim the outer 2 pixels to ensure we don't have boundary artifacts.
    phi_tt = (phi[t_lo+1:t_hi+1, ...] - 2.0 * phi_int + phi[t_lo-1:t_hi-1, ...]) / (dt ** 2)
    phi_xx = (phi[..., x_lo+1:x_hi+1, ...] - 2.0 * phi_int + phi[..., x_lo-1:x_hi-1, ...]) / (dx ** 2)
    phi_yy = (phi[..., y_lo+1:y_hi+1] - 2.0 * phi_int + phi[..., y_lo-1:y_hi-1]) / (dx ** 2)
    laplacian = phi_xx + phi_yy
```
*Why we did this:* PySINDy's `PDELibrary` is powerful but can be finicky with custom 3D tensors. By manually computing the exact spatial derivatives ($\phi_{xx}, \phi_{yy}$) and the temporal target ($\phi_{tt}$), we can feed a perfectly clean feature matrix into a sparse regression solver (STLSQ) and guarantee we know exactly how the derivatives were formed.

## 4. The Expected Equation

We expect the sparse regression to kill off all terms except the Laplacian ($\nabla^2\phi$), a damping term ($\phi_t$), and potentially a mass/source term.

$$\ddot{\phi} = c^2 \nabla^2 \phi - \alpha \dot{\phi} + S(\vec{x}_{\text{defect}})$$

If the algorithm succeeds, it will independently derive the wave speed ($c^2$) and the decay rate ($\alpha$) just by watching the topological wake dissipate. This provides encouraging evidence that the system is self-consistent and that gravity could be emergent.

## 5. SINDy Extraction Results

After correcting the sampling rate to 1-tick resolution, exporting the raw 3D Laplacian directly from the engine, and spatially masking out the central singularity (the Sun's hardcoded mass), PySINDy executed a sparse STLSQ regression on **47.6 million** discrete grid points representing pure topological wave propagation. 

The mathematical results were highly encouraging:

```text
============================================================
EXTRACTED PDE (Cost of Existence):
============================================================

  phi_tt = 10211.149 * laplacian - 82.696 * phi_t - 1075.494 * phi 

  R^2 = 0.96199796

============================================================
PHYSICAL INTERPRETATION:
============================================================

  Laplacian coefficient: 10211.149
  => Extracted wave speed: c = sqrt(10211.149) = 101.050
  (Expected c = 100.0)

  phi_t coefficient (damping): -82.696
  => Energy dissipation ('cost of existence')

  phi coefficient (restoring): -1075.494
  => Klein-Gordon type mass term
```

### Analysis of the Mathematical Structure
The extracted sparse equation is a continuous **Damped Klein-Gordon Equation**:
$$ \frac{\partial^2 \phi}{\partial t^2} = c^2 \nabla^2 \phi - \alpha \frac{\partial \phi}{\partial t} - \beta \phi $$

This is an encouraging finding. The WeitzenbÃ¶ck lattice geometry behaves far more complexly than a simple acoustic medium. 
1. **$c^2 \nabla^2 \phi$**: The spatial tension propagates at approximately the speed of light ($c=100$). The SINDy extraction yielded 101.05, a striking 99% alignment given that the raw FDTD tensors were noisy and fully discrete.
2. **$-\alpha \phi_t$**: The damping term directly corresponds to our `wave_dissipation=0.999`. This is the literal "cost of existence"â€”the geometry requires energy to process and propagate topological waves over time.
3. **$-\beta \phi$**: The restoring force (a Klein-Gordon mass term) suggests that the space actively resists being "dented" by mass. It attempts to spring back to $\phi = 0$. 

By identifying this PDE purely from data-driven telemetry, we have found promising evidence that macroscopic Newtonian gravity might be modeled as a low-energy emergent property of a topological Klein-Gordon field.

## 2. The Heisenberg Cut Sweep
On July 18, 2026, we successfully launched the batch mass-sweep campaign ("The Heisenberg Cut") via the GUI to find the precise numerical threshold where the Weitzenböck matrix's stiffness (Cost of Existence) overwhelms the wave. The sweep iterates through a log-scale mass range from 0.1 to 100,000.0, evaluating the collapse of interference fringes in a double-slit geometry.
