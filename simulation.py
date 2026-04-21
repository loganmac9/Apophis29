from gravity import GravityCalc
from stateVector import StateVector
from simulationData import SimulationData


class Simulation:
    # The conductor, owns all the other objects and ties everything together.
    # Sets up the initial conditions.
    def __init__(self, bodies, integrator):
        # Storing the passed-in arguments as self attributes to be used in other methods later:
        self.bodies = bodies
        self.integrator = integrator

        # Class instances and stored as self so run() can get to them.
        self.gravity = GravityCalc()
        self.state_vector = StateVector()
        self.sim_data = SimulationData(bodies)

    def run(self, t_total, dt):
        # call to actually start the simulation.
        print(f"--------------Simulation Starting--------------")
        # Calling integrate method from rk4 integrator using the integrator instance:
        self.integrator.integrate(self.bodies, t_total, dt, self.gravity, self.state_vector, self.sim_data)
        print(f"--------------Integrator Finished--------------")
        print(f"--------------Simulation Completed--------------")
        # Calling print_energy_conservation to get energy drift
        self.sim_data.print_energy_conservation()

    def get_results(self):
        # getter that returns the simulation data for the visualizer.
        return self.sim_data
