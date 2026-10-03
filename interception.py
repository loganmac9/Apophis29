import numpy as np
from rocket import Rocket
from asteroid import Asteroid

class InterceptionCalculator:

    # G in AU³/(M☉·year²)
    G = 4 * np.pi ** 2

    # GM_sun = G × 1 solar mass
    MU = 4 * np.pi ** 2

    def __init__(self, rocket, asteroid, bodies, sim_data):
        # stores references to everything
        self.rocket = rocket
        self.asteroid = asteroid
        self.bodies = bodies
        self.sim_data = sim_data

        # Find Sun and Earth from bodies list
        self.sun = next(b for b in bodies if b.name == 'Sun')
        self.earth = next(b for b in bodies if b.name == 'Earth')

    def find_launch_window(self, search_days=365):
        # searches through possible launch dates to find the one that minimizes total delta-v.
        # The optimal launch date is when the geometry between them minimizes the fuel needed for the trip.
        # Minimum delta-v occurs when orbital geometry is most favorable
        # Get trajectories from simulation data
        earth_traj = self.sim_data.get_trajectory('Earth')
        asteroid_traj = self.sim_data.get_trajectory(self.asteroid.name)
        asteroid_vel = np.array(self.sim_data.velocities[self.asteroid.name])
        earth_vel = np.array(self.sim_data.velocities['Earth'])

        times = self.sim_data.times  # in years

        best_dv = np.inf
        best_launch = None
        best_tof = None
        best_v1 = None
        best_v2 = None

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
                dv_launch = self.compute_delta_v(earth_vel[i], v1)

                # Delta-v needed at asteroid arrival, use asteroid velocity at arrival frame j
                dv_arrival = self.compute_delta_v(asteroid_vel[j], v2)

                # Add temporarily for debugging — print first successful result
                if v1 is not None and best_dv == np.inf:
                    print(f"First Lambert success:")
                    print(f"  launch frame i={i}, t_launch={t_launch:.4f} years")
                    print(f"  tof={tof:.1f} years")
                    print(f"  Earth vel at launch:    {earth_vel[i]}")
                    print(f"  v1 from Lambert:        {v1}")
                    print(f"  dv_launch magnitude:    {np.linalg.norm(earth_vel[i] - v1):.4f} AU/yr")
                    print(f"  Asteroid vel at arrival: {asteroid_vel[j]}")
                    print(f"  v2 from Lambert:         {v2}")
                    print(f"  dv_arrival magnitude:    {np.linalg.norm(asteroid_vel[j] - v2):.4f} AU/yr")

                total_dv = dv_launch + dv_arrival

                if total_dv < best_dv:
                    best_dv = total_dv
                    best_launch = t_launch
                    best_tof = tof
                    best_v1 = v1
                    best_v2 = v2

        if best_launch is None:
            print("No valid launch window found in search period")
            return None

        # Tsiolkovsky rocket equation — max delta-v rocket can achieve
        dv_max = self.rocket.exhaust_vel * np.log(
            (self.rocket.dry_mass + self.rocket.fuel_mass) / self.rocket.dry_mass
        )
        feasible = best_dv <= dv_max

        if not feasible:
            print(f"Warning: required Δv ({best_dv:.4f} AU/yr) exceeds "
                  f"rocket capability ({dv_max:.4f} AU/yr)")

        return {
                'launch_time': best_launch,
                'arrival_time': best_launch + best_tof,
                'tof': best_tof,
                'delta_v': best_dv,
                'v1': best_v1,
                'v2': best_v2,
                'feasible': feasible,
                'dv_max': dv_max
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
        cos_dnu = np.clip(cos_dnu, -1.0, 1.0)  # guard floating point errors

        # Determines transfer direction
        # Cross product z-component tells us if transfer is prograde or retrograde
        cross_z = r1_vec[0] * r2_vec[1] - r1_vec[1] * r2_vec[0]
        sin_dnu = np.sqrt(max(0.0, 1 - cos_dnu ** 2))
        if cross_z < 0:
            sin_dnu = -sin_dnu  # retrograde — negate to select prograde solution

        if abs(sin_dnu) < 1e-10:
            return None, None  # 180° or 0° transfer — undefined

        # Key geometric parameter — ALWAYS positive for prograde
        # sin_dnu negative → retrograde → A flips sign which selects retrograde solution
        # Force prograde by ensuring A is always positive
        A = np.sqrt(r1 * r2 * (1 + cos_dnu))

        if sin_dnu < 0:
            A = -A  # retrograde case needs negative A

        if A == 0:
            return None, None  # degenerate case

        # 2. Set initial guess for the Universal Variable z
        # z = 0.0 is a safe starting point for elliptic orbits

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
                term1 = chi ** 3 * ((1 / (2 * z)) * (C - 1.5 * S / C) + (3 * S ** 2) / (4 * C))
                term2 = (A / 8) * ((3 * S / C) * np.sqrt(y) + A * np.sqrt(C / y))
                dtdz = (term1 + term2) / np.sqrt(mu)
            else:
                term1 = (np.sqrt(2) / 40) * y ** 1.5
                term2 = (A / 8) * (np.sqrt(y) + A * np.sqrt(1 / (2 * y)))
                dtdz = (term1 + term2) / np.sqrt(mu)
            if abs(dtdz) < 1e-12:
                z += 0.1  # nudge and retry rather than dividing by near-zero
                continue


            # 5. Update z using Newton's method root finder
            #    z_new = z - f(z)/f'(z)  where f(z) = t(z) - tof
            #    Damped — prevents wild overshoot into extreme hyperbolic z values
            #    that would overflow cosh/sinh
            raw_step = (tof - t) / dtdz

            max_step = 10.0  # empirically safe bound for this unit system
            step = np.clip(raw_step, -max_step, max_step)

            z_new = z + step

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
        g = A * np.sqrt(y / mu)
        f = 1 - y / r1
        gdot = 1 - y / r2

        # If g is negative, flip both velocity results
        # Physical validity checks, reject degenerate solutions
        if g == 0 or abs(f) > 100 or abs(gdot) > 100:
            return None, None

        print(f"  Lambert internals: A={A:.4f}, y={y:.4f}, g={g:.4f}, f={f:.4f}, gdot={gdot:.4f}")

        v1 = (r2_vec - f * r1_vec) / g
        v2 = (gdot * r2_vec - r1_vec) / g

        # velocities should be reasonable for inner solar system
        # Earth orbits at ~6.28 AU/yr so anything over 50 is degenerate
        v1_mag = np.linalg.norm(v1)
        v2_mag = np.linalg.norm(v2)
        if v1_mag > 50 or v2_mag > 50:
            return None, None

        return v1, v2

    def compute_delta_v(self, v_current, v_required):
        # magnitude of velocity change needed Δv = (v_final - v_initial)
        return np.linalg.norm(v_required - v_current)

    def compute_transfer_to_lagrange(self, lagrange_point):
        # return trajectory
        # current position
        r1 = self.asteroid.position
        # end position
        r2 = lagrange_point

        distance = np.linalg.norm(lagrange_point - self.asteroid.position)
        rough_tof = distance / 0.1  # AU / (AU/year) = years

        velocities = self.compute_lambert(r1, r2, rough_tof)

        # If Lambert fails velocities is (None, None) and velocities[0] crashes
        if velocities[0] is None:
            print("Warning: Lambert failed for Lagrange transfer")
            return None

        delta_v = self.compute_delta_v(self.asteroid.velocity, velocities[0])

        return {
                'tof': rough_tof,
                'delta_v': delta_v,
                'v1': velocities[0],
                'v2': velocities[1],
                'lagrange_point': lagrange_point,
        }

    def compute_drone_formation(self, n_drones, lagrange_point):
        # Computes where each drone should position itself around the asteroid
        # in a formation behind the asteroid pointing towards the target destination.

        # Direction from asteroid toward target
        to_target = lagrange_point - self.asteroid.position
        dist_to_target = np.linalg.norm(to_target)

        if dist_to_target == 0:
            thrust_direction = np.array([1.0, 0.0, 0.0])
        else:
            thrust_direction = to_target / dist_to_target

        # how far each drone hovers from the asteroid center
        standoff = self.asteroid.radius * 10

        # Formation center — BEHIND asteroid opposite to target
        formation_center = self.asteroid.position - thrust_direction * standoff

        # Build perpendicular ring around formation center
        # Need two vectors perpendicular to thrust_direction
        # Use Gram-Schmidt to find them
        arbitrary = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(thrust_direction, arbitrary)) > 0.9:
            arbitrary = np.array([0.0, 1.0, 0.0])

        perp1 = np.cross(thrust_direction, arbitrary)
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(thrust_direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)

        # Divide a full circle (2π radians) equally among n_drones
        offsets = []
        # ring tighter than standoff distance
        ring_radius = standoff * 0.5

        # For each drone compute its offset from asteroid center,
        # place them in a ring in the y-z plane (perpendicular to x which is the thrust direction)
        for i in range(n_drones):
            angle = 2 * np.pi * i / n_drones
            offset = (formation_center - self.asteroid.position +
                      ring_radius * (np.cos(angle) * perp1 +
                                     np.sin(angle) * perp2))

            offsets.append(offset)

        # Return a list of offset vectors — one per drone. These get stored in each Drone object as formation_offset
        return offsets

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

        # Search 180 days -> launch window call... Default: self.find_launch_window()
        launch_window = self.find_launch_window(search_days=180)
        if launch_window is None:
            print(f'Error!! Launch Window Not Found')
            return None

        lagrange_pos = self.compute_lagrange_point(point=self.asteroid.target_lagrange)

        transfer = self.compute_transfer_to_lagrange(lagrange_pos)
        time_available = 2.0  # years — estimate for capture phase
        drone_count = self.rocket.get_drone_count(self.asteroid, lagrange_pos, time_available)
        formation = self.compute_drone_formation(drone_count, lagrange_pos)

        # Total delta-v across all mission phases
        dv_launch = launch_window['delta_v']
        dv_return = transfer['delta_v']
        dv_total = dv_launch + dv_return

        # Mission summary
        print(f"\n{'=' * 50}")
        print(f"MISSION PLAN: {self.asteroid.name}")
        print(f"{'=' * 50}")
        print(f"Launch time:     {launch_window['launch_time']:.3f} years")
        print(f"Arrival time:    {launch_window['arrival_time']:.3f} years")
        print(f"Flight time:     {launch_window['tof']:.3f} years")
        print(f"ΔV launch:       {dv_launch * 4.74057:.2f} km/s")
        print(f"ΔV return:       {dv_return * 4.74057:.2f} km/s")
        print(f"ΔV total:        {dv_total * 4.74057:.2f} km/s")
        print(f"Drones needed:   {drone_count}")
        print(f"Target:          {self.asteroid.target_lagrange}")
        print(f"Feasible:        {launch_window['feasible']}")
        print(f"{'=' * 50}\n")

        return {
            'launch_time': launch_window['launch_time'],
            'arrival_time': launch_window['arrival_time'],
            'tof': launch_window['tof'],
            'delta_v_launch': dv_launch,
            'delta_v_return': dv_return,
            'delta_v_total': dv_total,
            'feasible': launch_window['feasible'],
            'n_drones': drone_count,
            'drone_formation': formation,
            'lagrange_point': lagrange_pos,
            'v1': launch_window['v1'],
            'v2': launch_window['v2'],
        }


