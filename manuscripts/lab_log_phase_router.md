# Lab Log: The Heisenberg Cut & The Phase Router

**Date:** July 18, 2026  
**Experiment:** Mass Sweep (0.1 to 100,000 $m_0$) with Constant Classical Velocity ($v_x = 100.0$)  
**Objective:** Determine if the disappearance of the interference pattern at high masses is due to simulation failure (particles timing out/missing slits) or a genuine physical decoherence into a classical limit.

## 1. Experimental Setup
We ran a 21-step parameter sweep of the particle mass ($m$) from $0.1$ to $100,000.0$, compensating the initial momentum ($p$) proportionally to maintain a constant classical velocity ($v_x = p/m = 100.0$). This ensures particles traverse the simulation space in the exact same number of ticks regardless of mass, ruling out timeout errors. 
* Slit separation: 0.04
* Slit width: 0.01

## 2. Findings: The Classical Asymptote
*   **Hypothesis Tested:** "The interference pattern disappears because particles aren't making it through the slit."
*   **Result:** **Falsified.** Hit rates demonstrated an asymptote confirming classical penetration of the slits.
    *   At very low mass ($m=0.1, p=10.0$), the quantum potential dominates, resulting in wide diffraction and strong interference. Hit rate: ~54%.
    *   At transitional masses ($m=1.0, p=100.0$), the quantum potential actively forces particles into the central barrier. Hit rate: ~20%.
    *   At macroscopic masses ($m \ge 10.0, p \ge 1,000.0$), the quantum potential term $\frac{\nabla^2 R}{2mR}$ shrinks to zero. The wavepacket ceases to expand, and particles travel in purely ballistic, straight lines. The hit rate stabilized exactly at **66.6%** (6,658 / 10,000), which corresponds perfectly to the fraction of a straight classical beam that would physically intersect the two slit openings.

## 3. Discovery: The Phase Router & Bohmian Non-Crossing Theorem
The most significant finding of this lab is the visualization of the hidden variable dynamics via the **Phase Router (Hue vs Final Y)** graphs.

In standard quantum mechanics, the mechanism between the slits and the screen is treated as fundamentally unknowable. However, plotting the final screen coordinate ($Y$) against the initial hidden phase parameter (Hue) reveals a strictly deterministic topology.

1.  **High Mass (Classical Limit):** The phase-space plot shows two smooth, continuous arcs. Because the particles travel in straight lines, their phase winds up linearly. The arcs are simply the macroscopic shadows of the two slits smeared across the phase range.
2.  **Low Mass (Quantum Regime):** As the mass drops, the arcs break into evenly spaced gaps, and the remaining segments form distinct "boxes" of color (e.g., Orange, Yellow, Teal, Light Purple, Dark Purple). 
3.  **The Non-Crossing Mechanism:** The boxes correspond to the discrete interference fringes on the screen. 
    *   The **gaps** correspond to the *dark fringes*, where the quantum potential forms an impassable topological wall.
    *   The **"curved ripples" and crossed arcs** within the boxes are the direct visualization of the *Bohmian Non-Crossing Theorem*. Particle trajectories from the left slit and right slit cannot cross in physical space. Instead, the quantum potential routes the particles strictly by their initial hidden phase into neatly packed fringes, heavily accelerating them laterally to ensure paths never cross. 

## 4. Conclusion
The TEGR Collider successfully simulates the physical mechanism of the quantum-to-classical transition (the Heisenberg Cut). Furthermore, the model has exposed the underlying deterministic topology of quantum interference, providing direct phase-space visualization of how a continuous wave equation sorts discrete particles into interference fringes.

## Next Steps
*   Draft a new manuscript section focusing on Phase-Space Sorting and the Non-Crossing theorem.
*   Isolate individual particle trajectories within a specific "color box" (e.g., the teal central fringe) to trace the exact lateral acceleration applied by the quantum potential.
