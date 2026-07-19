import os

file_path = 'teleparallel_gui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the combo box string
content = content.replace('"58. Aspelmeyer Sweep (RAE Double-Slit)"', '"58. The Heisenberg Cut (Mass Sweep)"')

# 2. Update the elif condition
content = content.replace('elif text == "Aspelmeyer Sweep (RAE Double-Slit)":', 'elif text == "The Heisenberg Cut (Mass Sweep)":')

# 3. Update the comments inside the preset
content = content.replace('PRESET 58: Aspelmeyer Mass Sweep - Batched 20-Run Campaign', 'PRESET 58: The Heisenberg Cut - Batched Mass Sweep Campaign')
content = content.replace('Compare TEGR kinematic phase-shearing (RAE Kuramoto overflow)', 'Compare TEGR kinematic phase-shearing (Cost of Existence overflow)')
content = content.replace('10 -> 50,000 (heavy particle -> boundary test)', '10 -> 100,000 (heavy particle -> boundary test)')
content = content.replace('10000.0, 50000.0,                # Boundary test', '10000.0, 50000.0, 100000.0,      # Boundary test')
content = content.replace('label = f"Aspelmeyer Sweep m={m}"', 'label = f"Heisenberg Cut Sweep m={m}"')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("GUI patched successfully.")
