import numpy as np

class RK4Integrator:
    # RK4 takes the current state and marches it forward one time step
    # by evaluating the derivative function 4 times at different points,
    # then combines them into one weighted average update.
    # RK4 is a learning tool and debugging companion. DOP853(k1-k13) is the production engine.

    def step(self, t, state, dt, derivative_func):
        # Calling the derivative_func from gravity.py
        # Computes k1, k2, k3, k4 and returns the new state.
        # derivative_func("trial time", "trial_state")

        # k1: the derivative at the initial position.
        k1 = derivative_func(t, state)
        # k2: is the derivative at a half step forward using k1
        k2 = derivative_func(t + dt/2, state + (dt/2) * k1)
        # k3: is the derivative at a half step forward using k2 instead
        k3 = derivative_func(t + dt/2, state + (dt/2) * k2)
        # k4: is the derivative at a full step forward using k3
        k4 = derivative_func(t + dt, state + dt * k3)

        # weighted average of all four trial states
        new_state = state + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
        return new_state

    def integrate(self, bodies, t_total, dt, gravity, state_vector, sim_data):
        # gravity: GravityCalc instance
        # state_vector: StateVector instance
        # sim_data: SimulationData instance

        # Packing the initial body states into a flat array using StateVector class
        state = state_vector.pack(bodies)
        t = 0.0
        # creates a new function that only takes t and state
        # but also passes bodies along too:
        f = lambda t_diff, state_diff: gravity.compute_derivatives(t_diff, state_diff, bodies)

        while t < t_total:
            # New state is stepped through.
            new_state = self.step(t, state, dt, f)
            # New state set as main state.
            state = new_state
            # Unpacks the "new_state" flat array back into individual body objects,
            # permanently updating each body's position and velocity for this time step.
            state_vector.unpack(state, bodies)
            # "energy" set to the computed total energy of "any" passed in bodies.
            energy = gravity.compute_total_energy(bodies)
            # This new stepped state then is stored for simulation; passing in the time step t,
            # "any" bodies, and the total energy calculated.
            sim_data.store_step(t, bodies, energy)
            t = t + dt  # Time step(dt) towards whatever t_total will be passed in as(simulation clock).
