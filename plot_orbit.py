import numpy as np
import matplotlib.pyplot as plt

data = np.load('electron_trajectory.npy')

# Particle 1 (Venus)
x = data[:, 0, 0]
y = data[:, 0, 1]

plt.figure(figsize=(8, 8))
plt.plot(x[:4000], y[:4000], label='Kinematic Track (0-4000)', color='cyan')
plt.plot(x[4000:], y[4000:], label='Free Flight (4000-8000)', color='magenta')
plt.plot(0, 0, 'yo', label='Sun')
plt.title('Venus Orbit: Kinematic vs Free Flight')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.savefig('venus_orbit_check.png')
print("Plot saved to venus_orbit_check.png")
