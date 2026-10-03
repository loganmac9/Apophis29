import numpy as np
from simulation import Simulation

class MissionRunner:

    def __init__(self, sun, earth, moon, asteroid, rocket, mission_plan, integrator):
        # stores everything needed across all stages
        # bodies:
        self.sun = sun
        self.earth = earth
        self.moon = moon
        self.asteroid = asteroid
        self.rocket = rocket
        # set before any burns
        self.initial_fuel_mass = rocket.fuel_mass

        # These two should ref back to their methods/class?
        self.mission_plan = mission_plan
        self.integrator = integrator

        # Drone physical specs — roughly 200kg spacecraft
        self.drone_mass = 1e-28  # solar masses
        self.drone_radius = 1e-12  # AU


    def extract_final_state(self, sim_data, bodies):
        # pulls the LAST frame's position/velocity for each body
        # and writes it back onto the body objects
        # (so the next stage can start exactly where the last left off)
        for body in bodies:
            # looks up body's full traj using its name
            # celestData caries the bodies, so body.name
            # get_trajectory returns the full positions array for this body's name
            traj = sim_data.get_trajectory(body.name)

            # velocities stored separately, same name lookup
            vel = np.array(sim_data.velocities[body.name])

            # -1 index ref to last entry
            # Set body.position and body.velocity to that last entry
            # .copy() so body doesn't share memory with the sim_data array
            body.position = traj[-1].copy()
            body.velocity = vel[-1].copy()


    def apply_impulsive_burn(self, rocket, v_required):
        # instantly changes rocket.velocity by delta_v_vector
        # reduces rocket.fuel_mass / rocket.mass via Tsiolkovsky
        # vector direction, v_required being v1 from lambert
        delta_v_vector = v_required - rocket.velocity
        delta_v_mag = np.linalg.norm(delta_v_vector)

        # Tsiolkovsky but for m_f, mass final/mass after burn
        m_f = rocket.mass * np.exp(-delta_v_mag/rocket.exhaust_vel)

        # Mass update
        mass_consumed = rocket.mass - m_f

        # Defensive check — even though find_launch_window already verified
        # feasibility, confirm the rocket actually HAS enough fuel before
        # committing to the burn.
        if mass_consumed > rocket.fuel_mass:
            print(f"Warning: burn requires {mass_consumed:.3e} M☉ fuel, "
                  f"but only {rocket.fuel_mass:.3e} M☉ remains. "
                  f"Burn NOT applied.")
            return None  # signal that the burn failed

        rocket.fuel_mass -= mass_consumed
        rocket.mass = m_f

        # Change the Velocity from the burn
        rocket.velocity = v_required.copy()

        # Return to check against what "find_launch_window" predicted
        return delta_v_mag

    def run_stage_1_prelaunch(self):
        # rocket inert here(not burning)
        # t_total = mission_plan['launch_time']
        bodies = [self.sun, self.earth, self.moon, self.asteroid, self.rocket]

        # how long this stage runs...
        # mission plan already tells you exactly when launch happens:
        t_total = self.mission_plan['launch_time']

        # Create a fresh Simulation object and run it
        sim = Simulation(bodies, self.integrator)
        sim.run(t_total=t_total, dt=1 / (8766 * 4))  # tighter step needed for Moon like object

        # Results from sim:
        sim_data = sim.get_results()

        # Updating the bodies to their end-of-stage state with the method:
        self.extract_final_state(sim_data, bodies)
        # The bodies will hold their launch-moment position/velocity.
        # ready for Stage 2 to pick up from exactly here.

        # Returning so merge_simulation_data can stitch all three stages together later
        return sim_data

    def run_stage_2_transit(self):
        # The rocket leaves Earth and coasts through space to the asteroid.
        # Calling method with "v_required" from mission_plan's v1
        delta_v1_mag = self.apply_impulsive_burn(self.rocket, self.mission_plan['v1'])
        if delta_v1_mag is None:
            print(f"Transit Burn Failed")
            return None

        # then coast — same bodies, t_total = mission_plan['tof']
        bodies = [self.sun, self.earth, self.moon, self.asteroid, self.rocket]
        t_total = self.mission_plan['tof']

        # Create a fresh Simulation object and run it
        sim = Simulation(bodies, self.integrator)
        sim.run(t_total=t_total, dt=1 / (8766 * 4))  # tighter step needed for Moon like object

        # Results from sim:
        sim_data = sim.get_results()

        # Apply arrival burn/Match the asteroid's velocity
        delta_v2_mag = self.apply_impulsive_burn(self.rocket, self.asteroid.velocity)
        if delta_v2_mag is None:
            print(f"Arrival Burn Failed")
            return None

        # So all bodies hold their end-of-transit positions:
        self.extract_final_state(sim_data, bodies)
        return sim_data

    def deploy_drones(self):
        # creates N Drone objects using mission_plan['drone_formation']
        # positioned at rocket's current location, mode='deploying'

        from drone import Drone  # import here to avoid circular imports

        # list of offset vectors computed by compute_drone_formation
        # one per drone, describing where each drone sits relative to the asteroid center.
        formation = self.mission_plan['drone_formation']

        # Get drone count
        drone_count = len(self.mission_plan['drone_formation'])

        # creating drones list
        drones = []

        for i, formation_offset in enumerate(formation):
            position = self.asteroid.position + self.formation_offset

            # moving with the asteroid
            velocity = self.asteroid.velocity.copy()

            drone = Drone(
                drone_id=i,
                mass=self.drone_mass,
                radius=self.drone_radius,
                position=position,
                velocity=velocity,
                parent_rocket=self.rocket,
                target_asteroid=self.asteroid,
                formation_offset=formation_offset,
                lagrange_point=self.mission_plan['lagrange_point']
            )
            drones.append(drone)

        drones = drones
        return drones


    def run_stage_3_capture(self, duration):
        # bodies = [sun, earth, moon, asteroid, rocket] + drones
        # this is the stage that actually exercises the new update() hook
        drones = self.deploy_drones()

        bodies = [self.sun, self.earth, self.moon, self.asteroid, self.rocket] + drones
        bodies.update()

        # Create a fresh Simulation object and run it
        sim = Simulation(bodies, self.integrator)
        sim.run(t_total=duration, dt=1 / (8766 * 4))  # tighter step needed for small objects

        # Results from sim:
        sim_data = sim.get_results()

        # So all bodies hold their end-of-transit positions:
        self.extract_final_state(sim_data, bodies)
        return sim_data

    def merge_simulation_data(self, stage_data_list):
        from simulationData import SimulationData

        # takes the three separate SimulationData objects and joins them
        # into one continuous dataset the visualizer can play back as a single animation.
        # Unpack the incoming list — these were already computed by run_full_mission
        [stage1_data, stage2_data, stage3_data] = stage_data_list

        # Step 1 — shift time arrays so they're continuous
        # Each stage's times start from 0.0 — need offsets so they continue
        # where the previous stage left off rather than resetting to zero
        stage1time = np.array(stage1_data.times)
        stage2time = np.array(stage2_data.times)
        stage3time = np.array(stage3_data.times)

        # No shift needed for stage 1 — already starts at 0
        offset2 = stage1time[-1]  # stage 2 starts where stage 1 ended
        offset3 = stage1time[-1] + stage2time[-1]  # stage 3 starts where stage 2 ended

        stage1Shift = stage1time
        stage2Shift = stage2time + offset2
        stage3Shift = stage3time + offset3

        all_times = np.concatenate([stage1Shift, stage2Shift, stage3Shift])

        # Step 2 — concatenate energies across all three stages
        all_energies = np.concatenate([
            np.array(stage1_data.energies),
            np.array(stage2_data.energies),  # fixed — was stage1 three times
            np.array(stage3_data.energies)
        ])

        # Step 3 — positions and velocities for bodies in ALL three stages
        # Sun, Earth, Moon, Asteroid, Rocket exist throughout — simple concatenation
        all_positions = {}
        all_velocities = {}

        standard_names = ['Sun', 'Earth', 'Moon', self.asteroid.name, 'Rocket']

        for name in standard_names:
            all_positions[name] = np.concatenate([
                np.array(stage1_data.positions[name]),
                np.array(stage2_data.positions[name]),
                np.array(stage3_data.positions[name])]).tolist()

            all_velocities[name] = np.concatenate([
                np.array(stage1_data.velocities[name]),
                np.array(stage2_data.velocities[name]),
                np.array(stage3_data.velocities[name])]).tolist()

        # Step 4 — pad drone data for Stages 1 and 2
        # Drones only exist in Stage 3 — pad earlier stages with the drone's
        # first Stage 3 position repeated for all earlier frames so the
        # visualizer has the same number of frames for every body
        n_pad = len(stage1time) + len(stage2time)  # frames before drones existed

        for drone in self.drones:
            name = drone.name

            # First Stage 3 position/velocity — used for padding
            first_pos = np.array(stage3_data.positions[name][0])
            first_vel = np.array(stage3_data.velocities[name][0])

            # np.tile repeats the row n_pad times → shape (n_pad, 3)
            pad_pos = np.tile(first_pos, (n_pad, 1))
            pad_vel = np.tile(first_vel, (n_pad, 1))

            all_positions[name] = np.concatenate([
                pad_pos,
                np.array(stage3_data.positions[name])
            ]).tolist()

            all_velocities[name] = np.concatenate([
                pad_vel,
                np.array(stage3_data.velocities[name])
            ]).tolist()

        # Step 5 — build merged SimulationData manually
        # Use a small helper class to satisfy SimulationData's __init__
        # which expects a list of objects with a .name attribute
        class _BodyProxy:
            def __init__(self, name):
                self.name = name

        all_names = standard_names + [d.name for d in self.drones]
        fake_bodies = [_BodyProxy(n) for n in all_names]
        merged = SimulationData(fake_bodies)

        # Directly assign the stitched arrays — bypasses store_step()
        merged.times = all_times.tolist()
        merged.energies = all_energies.tolist()
        merged.positions = all_positions
        merged.velocities = all_velocities

        return merged



    def run_full_mission(self):
        # calls everything above in order, returns one combined SimulationData
        print("Running Stage 1: Pre-launch...")
        stage1_data = self.run_stage_1_prelaunch()

        print("Running Stage 2: Transit...")
        stage2_data = self.run_stage_2_transit()
        if stage2_data is None:
            print(f"Error: Stage 2 burn failed")
            return None

        print("Running Stage 3: Capture...")
        stage3_data = self.run_stage_3_capture()
        print(f"Asteroid in capture range. Capture phase finished")

        merged_data = self.merge_simulation_data([stage1_data, stage2_data, stage3_data])

        # Printing key stats: total simulation time covered, number of drones active,
        # asteroid's final distance from Lagrange point,
        # total fuel consumed (initial fuel minus remaining fuel).
        total_time = self.mission_plan['launch_time'] + self.mission_plan['tof'] + 2.0
        print(f"Total simulation time covered: {total_time:.3f} years ({total_time*365.25:.0f} days)")
        print(f"Drones Active: {len(self.drones)}")

        # compute the scalar distance and format it
        asteroid_final_pos = np.array(stage3_data.positions[self.asteroid.name][-1])
        dist_to_lagrange = np.linalg.norm(asteroid_final_pos - self.mission_plan['lagrange_point'])
        print(f"Asteroid's final distance from Lagrange point: {dist_to_lagrange:.4f} AU "
              f"({dist_to_lagrange * 1.496e8:,.0f} km)")

        fuel_consumed = self.initial_fuel_mass - self.rocket.fuel_mass
        print(f"Total fuel consumed is: {fuel_consumed:.3e} M☉")

        # goes directly into Visualizer(merged_data) in main.py
        return merged_data

