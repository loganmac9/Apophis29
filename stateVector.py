import numpy as np

class StateVector:

    def pack(self, bodies):
        N = len(bodies)

        # Packs positions and velocities into flat array and concat joins them end to end.
        positions = np.concatenate([body.position for body in bodies])
        velocities = np.concatenate([body.velocity for body in bodies])
        state = np.concatenate([positions, velocities])
        # Returning "state" numpy array
        return state

    def unpack(self, state, bodies):
        N = len(bodies)

        # Unpack positions and velocities from flat state array.
        positions = state[:3 * N].reshape(N, 3)  # shape: (N, 3)
        velocities = state[3 * N:].reshape(N, 3)  # shape: (N, 3)
        # Breaks the list into positions and velocities

        # Permanently update instead of a temporary update because why?????
        for i, body in enumerate(bodies):
            body.position = positions[i].copy()
            body.velocity = velocities[i].copy()
            # .copy() gives each body its own independent array
            # # Without it, body.position would be a reference into the state array
            # Also, if the state array changes later, the body's position would change with it unexpectedly.
            # After this method returns, simulation calls store_step()
            # which records body.position into the data arrays
            # Nothing overwrites these, they represent a real accepted time step
