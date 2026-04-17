import numpy as np

class GravityCalc:
    G = 6.674e-11

    def compute_accelerations(self, bodies):
        # acceleration done by: a_i = G(SUM(j!=i)(m_j/[r_ij]^3)r_ij)
        accelerations = []  # Initializing an acceleration Collection List?

        for i, body_i in enumerate(bodies):  # enumerate gives index AND value
            a = np.zeros(3)  # numpy zero vector for this body
            for j, body_j in enumerate(bodies):
                if i == j:
                    continue
                r_ij = body_j.position - body_i.position
                d = np.linalg.norm(r_ij)  # Pythagorean theorem(scalar distance)
                if d == 0:
                    continue
                a += self.G * (body_j.mass/d**3) * r_ij
            # (Adds a single item to the end of an existing list)
            accelerations.append(a)      # store this body's total acceleration
        return accelerations

        """
        For each body (Sun, Earth, Moon, Apophis, Rocket):
        Start with zero acceleration vector [0,0,0]

        For every OTHER body:
            Compute the pull direction (r_ij)
            Compute the distance (d)
            Compute how strong the pull is and add it to this body's acceleration
        
        Store this body's total accumulated acceleration

        Return list of all accelerations — one per body, same order as input
        """

    # scipy's "solve_ivp" requires the signature to be f(t, state). That's where "t" will be used.
    def compute_derivatives(self, t, state, bodies):
        # State array passed in.
        N = len(bodies) # Counts how many bodies are in the "bodies" list.
        # Used to know how to slice the flat state array correctly.
        # ex. Where positions end and velocities begin in the list.

        # Unpack positions and velocities from flat state array.
        positions = state[:3 * N].reshape(N, 3)  # shape: (N, 3)
        velocities = state[3 * N:].reshape(N, 3)  # shape: (N, 3)
        # Breaks the list into positions and velocities for derivation.
        # Before reshape —> flat, hard to work with:
        #[xs, ys, zs, xe, ye, ze, xm, ym, zm]
        # After .reshape(3, 3) — one row per body:
        #[[xs, ys, zs],  # row 0 = Sun
        # [xe, ye, ze],  # row 1 = Earth
        # [xm, ym, zm]]  # row 2 = Moon

        # Temporarily update body positions so compute_accelerations
        # uses the current integrator state, not the stored body state.
        for i, body in enumerate(bodies):
            body.position = positions[i]
            body.velocity = velocities[i]
        # Without this update:
        # compute_accelerations reads body.position = Earth's position at t=0
        # even when integrator is testing a trial state halfway through the step
        # With this update:
        # compute_accelerations reads body.position = trial position
        # integrator gets accurate derivatives for that trial state
        # (temp)Intermediate guesses that don't represent real moments in time.
        # Just needed bodies updated long enough to compute accelerations

        # Get accelerations using your method above.
        accelerations = self.compute_accelerations(bodies)

        # Pack derivatives back into flat array. From 2D array to flat(9,)
        # Then concatenate joins the multiple arrays end to end.
        derivatives = np.concatenate([velocities.flatten(), np.array(accelerations).flatten()])

        return derivatives

    def compute_total_energy(self, bodies):
        # The energy conservation check.
        KE = sum(body.kinetic_energy for body in bodies)
        # Calls the KE from before that has been added to the bodies already.

        PE = 0.0
        # range(len(bodies)) gives index numbers i and j for the number of bodies.
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):  # i+1 avoids double counting
                r_ij = bodies[j].position - bodies[i].position
                d = np.linalg.norm(r_ij) # Changes r_ij to a scalar distance, not a vector.
                PE += -self.G*bodies[i].mass*bodies[j].mass/d  # -G*mi*mj / distance
                # This is accumulating the PE of each body "+="
        return KE + PE
