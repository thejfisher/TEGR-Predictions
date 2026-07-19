Write-Host "--- TRI-NODE PING-PONG PIPELINE INITIATED ---"
Write-Host "Clearing stale processes on 100.66.100.83:7777..."
ssh hal@100.66.100.83 "fuser -k 7777/tcp || true"
Write-Host "[CLEANUP] "
Write-Host ">>> STARTING BUFFER NODE SINDY SERVER (hal@100.66.100.83) <<<"
Write-Host "Server launch: ssh hal@100.66.100.83 cd ~/hxseq-vsgx4/teleparallel_sim_photons && python3 -u sindy_zmq_server.py --port 7777 --no_llm --galactic_spin 0.0"

# Launch SINDy server in background
ssh hal@100.66.100.83 "cd ~/hxseq-vsgx4/teleparallel_sim_photons && nohup python3 -u sindy_zmq_server.py --port 7777 --no_llm --galactic_spin 0.0 > sindy_server.log 2>&1 &"

Write-Host "Waiting 15s for SINDy server to initialize (ROCm first-load)..."
for ($i=1; $i -le 15; $i++) {
    Write-Host "  ... ${i}s"
    Start-Sleep -Seconds 1
}

Write-Host "SINDy server init window complete. Launching physics..."
Write-Host ">>> STARTING PHYSICS ENGINE ON (thejfisher@100.122.147.67) <<<"

$PHYSICS_CMD = "cd ~/AI_Vault/'TEGR Collider' && python3 -u teleparallel_collider.py --run_label '62. True Kepler Orbit Coasting' --mode gravity-sink --num_particles 2 --mass_a 1.0 --mass_b 1.0 --pauli 10.0 --vacuum 0.001 --torsion 1.0 --eraser_active 0 --photon_emission 0 --slit_width 4.0 --slit_separation 6.0 --num_slits 2 --screen_x 20.0 --beam_start_x -25.0 --wall_z_layers 3 --wall_depth 5 --entangled 0 --sink_mass 50000.0 --collapse_radius 20.0 --collapse_G 1.0 --beam_momentum 0.05 --photon_freq 100.0 --work_function 10.0 --impact_parameter 0.5 --amps_cooling_cap 1.0 --dt 0.001 --total_ticks 4000 --batch_size 0 --wave_speed 100.0 --wave_dissipation 0.999 --jitter_amp 0.0 --num_anchors 1 --galactic_spin 0.0 --paper1_exact 0 --spin_coupling 1 --wall_thermal_phase 0 --pauli_power 2 --qed_vacpol 0 --qed_lamb 0 --qed_compton 0 --polarization_mode isotropic --pilot_wave 1 --interpolation_order linear --breit_wheeler 0 --bw_threshold 2.044 --dbb_guidance 0 --dbb_strength 0.01 --reverse_integration 0 --reverse_num_particles 500 --band_source kde --crossing_diagnostics 0 --plane_wave_init 0 --wave_shape plane --wave_freq 0.0 --plane_wave_amp 2.0 --which_path 0 --detector_mass 0.001 --detector_phase thermal --soft_wall 0 --vanish_sink 0 --fdtd_gravity 0 --rae_mode 1 --rae_kappa_scale 1.0 --rae_grad_scale 1.0 --zmq_target 100.66.100.83:7777"

Write-Host "Physics launch: ssh thejfisher@100.122.147.67 $PHYSICS_CMD"

# Run physics node and pipe output
ssh thejfisher@100.122.147.67 "$PHYSICS_CMD"

Write-Host ">>> WAITING FOR BUFFER NODE SINDY EXTRACTION TO FINISH <<<"
# Wait until the SINDy server log says "Server exiting."
while ($true) {
    $done = ssh hal@100.66.100.83 "grep -q 'Server exiting' ~/hxseq-vsgx4/teleparallel_sim_photons/sindy_server.log && echo YES || echo NO"
    if ($done -match "YES") {
        break
    }
    Start-Sleep -Seconds 2
}

# Dump SINDy log
ssh hal@100.66.100.83 "cat ~/hxseq-vsgx4/teleparallel_sim_photons/sindy_server.log"

Write-Host "[PIPELINE] Fetching aggregate_states.npz from thejfisher@100.122.147.67..."
Write-Host "Running: scp thejfisher@100.122.147.67:~/AI_Vault/'TEGR Collider'/aggregate_states.npz ./aggregate_states.npz"
scp "thejfisher@100.122.147.67:~/AI_Vault/'TEGR Collider'/aggregate_states.npz" "./aggregate_states.npz"
Write-Host "[PIPELINE] Successfully downloaded aggregate_states.npz"
