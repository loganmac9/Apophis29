import numpy as np


class SimulationData:
    # recording system — it stores everything that happens during the simulation.

    def __init__(self, bodies):
        # Creates a SimulationData object.
        # Sets up all the empty containers based on whatever bodies are passed in:
        self.times = []
        self.energies = []

        self.positions = {body.name: [] for body in bodies}
        self.velocities = {body.name: [] for body in bodies}
        # Empty lists per body name.
        # dictionary comprehension: Short hand for below.
        # self.positions = {}
        # for body in bodies:
        #     self.positions[body.name] = []

    def store_step(self, t, bodies, energy):
        self.times.append(t)
        self.energies.append(energy)

        for body in bodies:
            # Appends current state to all containers
            # (Adds a single item to the end of an existing list)
            # Storing the body's actual position and velocity
            self.positions[body.name].append(body.position.copy())
            self.velocities[body.name].append(body.velocity.copy())

    def get_trajectory(self, body_name):
        # Grab the list of positions for one body by name, then convert to numpy array.
        # "Trajectory" is the new numpy array.
        trajectory = np.array(self.positions[body_name])
        return trajectory

    def get_snapshot(self, index):
        # Returns the state of ALL bodies at one specific time step
        # look up the index in each body's position list
        return {name: positions[index] for name, positions in self.positions.items()}

        # self.positions.items() gives both the key (name) and value (list of positions) at the same time.
        # positions[index] grabs the position at that specific time step

    def print_energy_conservation(self):
        # Prints how much total energy has drifted from start to current
        # Drift meaning small accumulating rounding/approximation errors from discrete steps.
        # DOP853(Verlet) with tight tolerances keeps "drift" extremely small vs Euler for example.
        # Mostly debug
        if len(self.energies) < 2:
            return
        initial = self.energies[0]
        current = self.energies[-1]  # -1 means last element in Python
        drift = abs((current - initial) / initial) * 100
        print(f"Energy drift: {drift:.15f}%")
        # 0.001% drift over a year is acceptable. .15f showing 15 decimal places. It's precise.
        # A 1%> drift means the time step is too large or something is broken
        # ex. If drift is too large → x1,y1,z1 could be thousands of km from x2,y2,z2
        # and rocket misses the asteroid entirely.
