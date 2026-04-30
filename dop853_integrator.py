from scipy.integrate import solve_ivp
import numpy as np

class DOP853Integrator:
    # solve_ivp,  takes the entire time span and figures out the steps itself.

    def integrate(self, bodies, t_total, dt, gravity, state_vector, sim_data,
                  rtol=1e-10, atol=1e-10):
        # Tighter tolerances = more accurate but slower. NASA uses 1e-12.
        # DOP853 ignores dt. Scipy chooses its own step sizes adaptively.

        # Packing the initial body states into a flat array using StateVector class
        state = state_vector.pack(bodies)

        # Store initial state before loop starts
        t = 0.0
        energy = gravity.compute_total_energy(bodies)
        sim_data.store_step(t, bodies, energy)

        # creates a new function that only takes t and state
        # but also passes bodies along too:
        f = lambda t_diff, state_diff: gravity.compute_derivatives(t_diff, state_diff, bodies)

        # keyword arguments "fun"=f...
        result = solve_ivp(
                fun=f,                 # The function: f(t, state) derivative function
                t_span=(0, t_total),   # (start_time, end_time) tuple
                y0=state,              # initial flat state array
                method='DOP853',       # 'DOP853'
                rtol=rtol,             # relative tolerance
                atol=atol,             # absolute tolerance
                dense_output=False     # whether to allow interpolation between steps
                        )

        # To loop through all steps/results scipy ran:
        # Stores every accepted time point in result.t
        # Stores the corresponding state vector at each point in result.y
        for i in range(len(result.t)):
            # result.t and result.y are numpy arrays
            # transposed shape is (n_state_variables, n_steps)
            t = result.t[i]
            state = result.y[:, i]  # To get state at step i, [all rows, column i]
            # unpack, compute energy, store...
            state_vector.unpack(state, bodies)
            energy = gravity.compute_total_energy(bodies)
            sim_data.store_step(t, bodies, energy)

        print(f"----------------DOP853 Completed----------------")

