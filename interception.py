import numpy as np
from rocket import Rocket
from asteroid import Asteroid
from drone import Drone
from simulationData import SimulationData

class InterceptionCalculator:

    # G in AU³/(M☉·year²)
    G = 4 * np.pi ** 2

    # GM_sun = G × 1 solar mass
    MU = 4 * np.pi ** 2

    def __init__(self, rocket, asteroid, bodies):
        # stores references to everything
        self.rocket = rocket
        self.asteroid = asteroid
        self.bodies = bodies

        # Find Sun and Earth from bodies list
        self.sun = next(b for b in bodies if b.name == 'Sun')
        self.earth = next(b for b in bodies if b.name == 'Earth')

    def find_launch_window(self, search_days=365):
        # searches through possible launch dates to find the one that minimizes total delta-v.
        # The optimal launch date is when the geometry between them minimizes the fuel needed for the trip.
        # Meaning, when the Earth and target asteroid are at their closest approach.
        # Get trajectories from simulation data
        earth_traj = self.sim_data.get_trajectory('Earth')
        asteroid_traj = self.sim_data.get_trajectory(self.asteroid.name)
        times = self.sim_data.times  # in years

        best_dv = np.inf
        best_launch = None
        best_tof = None
        best_v1 = None

        # Search over launch dates, hourly steps
        for i, t_launch in enumerate(times[:search_days * 24]):

            r1 = earth_traj[i]

            # Search over flight times, 0.5 to 3 years
            for tof in np.arange(0.5, 3.0, 0.1):

                # Arrival index
                arrival_hours = int(tof * 365.25 * 24)
                j = i + arrival_hours
                if j >= len(times):
                    continue

                r2 = asteroid_traj[j]  # asteroid position at arrival

                # Solve Lambert's problem
                v1, v2 = self.compute_lambert(r1, r2, tof)
                if v1 is None:
                    continue  # Lambert failed for this geometry

                # Delta-v needed at Earth departure
                dv_launch = self.compute_delta_v(
                    self.earth.velocity, v1
                )

                # Delta-v needed at asteroid arrival
                dv_arrival = self.compute_delta_v(
                    self.asteroid.velocity, v2  # approximate
                )

                total_dv = dv_launch + dv_arrival

                if total_dv < best_dv:
                    best_dv = total_dv
                    best_launch = t_launch
                    best_tof = tof
                    best_v1 = v1

            return {
                'launch_time': best_launch,
                'tof': best_tof,
                'delta_v': best_dv,
                'v1': best_v1
            }

    def compute_lambert(self, r1_vec, r2_vec, tof):
        # Solves Lambert's problem iteratively using the Universal Variable Method
        # Given two positions and a travel time (tof),
        # what velocity do you need to get from point A to point B?
        # Converts the nonlinear Kepler equations into a generalized
        # time-of-flight equation that works for:
        #   elliptic orbits  (χ real, z = χ²/a > 0)
        #   parabolic orbits (z = 0)
        #   hyperbolic orbits (z < 0)

        mu = self.MU  # 4π² in AU/year units

        r1 = np.linalg.norm(r1_vec)
        r2 = np.linalg.norm(r2_vec)

        # 1. Calculate Initial Geometric Constants
        #    r1_norm, r2_norm already computed above
        #    cos_dnu = angle between r1 and r2 vectors
        #    A = sqrt(r1*r2*(1+cos_dnu)) ← key geometric parameter
        cos_dnu = np.dot(r1_vec, r2_vec) / (r1 * r2)
        sin_dnu = np.sqrt(1 - cos_dnu ** 2)

        if sin_dnu == 0:
            return None, None  # 180° transfer — undefined

        A = np.sqrt(r1 * r2 * (1 + cos_dnu))

        if A == 0:
            return None, None  # degenerate case

        # 2. Set initial guess for the Universal Variable z
        #    z = 0.0 is a safe starting point for elliptic orbits
        z = 0.0
        tolerance = 1e-8

        # 3. Compute the Stumpff Functions C(z) and S(z)
        #    These are generalized trig functions:
        #    z > 0: C(z) = (1-cos√z)/z       S(z) = (√z-sin√z)/z^(3/2)
        #    z = 0: C(z) = 1/2               S(z) = 1/6
        #    z < 0: C(z) = (cosh√-z-1)/-z   S(z) = (sinh√-z-√-z)/(-z)^(3/2)
        def stumpff_C(z):
            if z > 1e-6:
                return (1 - np.cos(np.sqrt(z))) / z
            elif z < -1e-6:
                return (np.cosh(np.sqrt(-z)) - 1) / (-z)
            else:
                return 0.5  # limit as z→0

        def stumpff_S(z):
            if z > 1e-6:
                sq = np.sqrt(z)
                return (sq - np.sin(sq)) / (sq ** 3)
            elif z < -1e-6:
                sq = np.sqrt(-z)
                return (np.sinh(sq) - sq) / (sq ** 3)
            else:
                return 1 / 6  # limit as z→0

        # 4. Evaluate Time of Flight (Δt) and iterate to find z
        #    tof = (1/sqrt(MU)) * chi³ * S(z) + A*sqrt(y)
        #    where y = r1 + r2 - A*(1 - z*S(z))/sqrt(C(z))
        for _ in range(1000):
            C = stumpff_C(z)
            S = stumpff_S(z)

            # y function
            y = r1 + r2 - A * (1 - z * S) / np.sqrt(C)

            if y < 0:
                z += 0.1
                continue

            # χ from y
            chi = np.sqrt(y / C)

            # Time of flight at current z
            t = (chi ** 3 * S + A * np.sqrt(y)) / np.sqrt(mu)

            # Derivative dt/dz for Newton's method
            if abs(z) > 1e-6:
                dtdz = (chi ** 3 * (0.5 / z) * (C - 1.5 * S / C) +
                        0.375 * A / z * (np.sqrt(y) + A * np.sqrt(C / (2 * y)))) / np.sqrt(mu)
            else:
                dtdz = np.sqrt(2) / 40 * y ** 1.5 / np.sqrt(mu)

            # 5. Update z using Newton's method root finder
            #    z_new = z - f(z)/f'(z)  where f(z) = t(z) - tof
            z_new = z + (tof - t) / dtdz

            if abs(z_new - z) < tolerance:
                z = z_new
                break
            z = z_new

        else:
            # for/else — runs only if loop never hit break (did not converge)
            print(f"Warning: Lambert's solver did not converge for tof={tof:.3f} years")
            return None, None

        # 6. Compute Velocity Vectors — returning v1 (departure) and v2 (arrival)
        #    Lagrange coefficients:
        #    f    = 1 - y/r1
        #    g    = A * sqrt(y/MU)
        #    gdot = 1 - y/r2
        #    v1   = (r2_vec - f*r1_vec) / g
        #    v2   = (gdot*r2_vec - r1_vec) / g
        C = stumpff_C(z)
        S = stumpff_S(z)
        y = r1 + r2 - A * (1 - z * S) / np.sqrt(C)

        f = 1 - y / r1
        g = A * np.sqrt(y / mu)
        gdot = 1 - y / r2

        v1 = (r2_vec - f * r1_vec) / g
        v2 = (gdot * r2_vec - r1_vec) / g

        return v1, v2

    def compute_delta_v(self, v_current, v_required):
        # magnitude of velocity change needed Δv = (v_final - v_initial)
        return np.linalg.norm(v_required - v_current)

    def compute_transfer_to_lagrange(self, lagrange_point):
        # plans return trajectory
        pass

    def compute_drone_formation(self, n_drones):
        # positions drones around asteroid
        pass

    def compute_lagrange_point(self, point='L4'):
        # computes L4/L5 position
        # L4 and L5 are points that form an equilateral triangle with the Sun and Earth.
        # They sit exactly 60° ahead (L4) or behind (L5) Earth in its orbit,
        # always at the same distance from the Sun as Earth.
        # arctan2 handles all 4 quadrants, handles the division internally
        earth_angle = np.arctan2(self.earth.position[1], self.earth.position[0])

        L4 = earth_angle + np.radians(60)
        L5 = earth_angle - np.radians(60)

        # Just magnitude of Earth's position because Sun is at origin
        sun_to_earth = np.linalg.norm(self.earth.position)

        if point == 'L4':
            angle = L4
        else:
            angle = L5
        x = sun_to_earth * np.cos(angle)
        y = sun_to_earth * np.sin(angle)
        z = 0  # everything is in the ecliptic plane

        return np.array([x, y, z])

    def plan_mission(self):
        # master method — calls everything above
        # returns complete mission plan
        pass

