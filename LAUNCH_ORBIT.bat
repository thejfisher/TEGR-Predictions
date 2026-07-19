@echo off
echo ===================================================
echo     TEGR: Bodies of Orbit - Cluster Launch
echo ===================================================
echo.

:: Activate the local virtual environment
call "C:\Users\Myna Bird\Physics_Env\Scripts\activate.bat"
cd /d "Z:\TEGR Collider"

echo [CLEANUP] Killing stale SINDy processes on hal...
ssh hal@100.66.100.83 "fuser -k 7777/tcp || true"

echo [LAUNCH] Starting SINDy ZMQ server on hal...
ssh hal@100.66.100.83 "cd ~/hxseq-vsgx4/teleparallel_sim_photons && nohup python3 -u sindy_zmq_server.py --port 7777 --no_llm --galactic_spin 0.0 > sindy_server.log 2>&1 < /dev/null &"

echo [WAIT] Giving HAL 15s to initialize ROCm...
timeout /t 15

echo [LAUNCH] Starting Physics Engine on thejfisher in bodies-of-orbit mode...
ssh thejfisher@100.122.147.67 "cd ~/AI_Vault/'TEGR Collider' && python3 -u teleparallel_collider.py --run_label '63. Bodies of Orbit (Venus Circular)' --mode bodies-of-orbit --num_particles 2 --mass_a 1.0 --mass_b 1.0 --pauli 0.0 --vacuum 0.001 --torsion 1.0 --eraser_active 0 --photon_emission 0 --slit_width 4.0 --slit_separation 6.0 --num_slits 2 --screen_x 20.0 --beam_start_x -25.0 --wall_z_layers 3 --wall_depth 5 --entangled 0 --sink_mass 408670.0 --collapse_radius 20.0 --collapse_G 1.0 --beam_momentum 5.0 --photon_freq 100.0 --work_function 10.0 --impact_parameter 0.5 --amps_cooling_cap 1.0 --dt 0.001 --total_ticks 4000 --batch_size 0 --wave_speed 100.0 --wave_dissipation 0.999 --jitter_amp 0.0 --num_anchors 1 --galactic_spin 0.0 --paper1_exact 0 --spin_coupling 0 --wall_thermal_phase 0 --pauli_power 2 --qed_vacpol 0 --qed_lamb 0 --qed_compton 0 --polarization_mode isotropic --pilot_wave 1 --interpolation_order linear --breit_wheeler 0 --bw_threshold 2.044 --dbb_guidance 0 --dbb_strength 0.01 --reverse_integration 0 --reverse_num_particles 500 --band_source kde --crossing_diagnostics 0 --plane_wave_init 0 --wave_shape plane --wave_freq 0.0 --plane_wave_amp 2.0 --which_path 0 --detector_mass 0.001 --detector_phase thermal --soft_wall 0 --vanish_sink 0 --fdtd_gravity 0 --rae_mode 1 --rae_kappa_scale 1.0 --rae_grad_scale 1.0 --zmq_target 100.66.100.83:7777"

echo.
echo [WAIT] Checking SINDy extraction on hal...
:wait_loop
ssh hal@100.66.100.83 "grep -q 'Server exiting' ~/hxseq-vsgx4/teleparallel_sim_photons/sindy_server.log && echo DONE || echo WAITING"
find "DONE" > nul 2>&1
if errorlevel 1 (
    timeout /t 2 > nul
    goto wait_loop
)

echo [FETCH] SINDy extraction log:
ssh hal@100.66.100.83 "cat ~/hxseq-vsgx4/teleparallel_sim_photons/sindy_server.log"

echo.
echo ===================================================
echo     COMPLETE - Results ready for Jupyter notebook
echo ===================================================
pause
