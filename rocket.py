from celestData import CelestData
import numpy as np


# Inheriting CelestData
class Rocket(CelestData):

    def __init__(self, name, radius, dry_mass, fuel_mass,
                 max_thrust, exhaust_vel, position, velocity,
                 reactor_power, reactor_fuel_mass,
                 drone_capacity=10, drone_mode='fixed', drone_thrust=None,
                 drone_battery=1000, drone_charge_rate=0):

        # Total mass = dry + fuel * nuclear
        total_mass = dry_mass + fuel_mass + reactor_fuel_mass

        # Calling parent __init__ from CelestData
        super().__init__(name=name, mass=total_mass, radius=radius,
                         position=position, velocity=velocity)

        # Class attributes:
        # Liquid fuel system
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.exhaust_vel = exhaust_vel
        self.max_thrust = max_thrust
        self.throttle = 0.0  # 0=off, 1=full thrust
        self.is_burning = False
        # needed by the thrust_vector property in gravity.py
        self._thrust_direction = np.zeros(3)  # updated when burn() called

        # electrical output (AU²·M☉/year³ — power in AU units)
        self.reactor_power = reactor_power

        # slow consumption reactor fuel
        # (Highly Enriched Uranium? 93% - allows for a much smaller reactor size)
        # OR if using fusion: Deuterium and Tritium (many years away from small enough reactor design)
        # 100 to 500 kilograms of HEW in a submarine for reference
        # 250kg -> solar masses = 1.25696e-28
        self.reactor_fuel_mass = reactor_fuel_mass

        self.phase = 'launched'
        self.target = None

        # default 10
        self.drone_capacity = drone_capacity
        self.drones_deployed = 0
        self.drone_mode = drone_mode  # 'fixed' or 'dynamic'
        self.drone_count = drone_capacity  # used in fixed mode
        self.drone_thrust = drone_thrust or 1e-30  # per drone thrust
        # The Tesla Semi has a 822 kWh usable capacity. Thus, using a 1000kWh battery seems sufficient?
        self.drone_battery = drone_battery
        # Google says 15/30min to charge with the current HEU reactor. Still should calculate it.
        self.drone_charge_rate = drone_charge_rate

    @property
    def thrust_vector(self):
        # Used by gravity.py to add thrust acceleration
        # Returns zero vector if not burning
        # "if self.is_burning" is already a bool so no need for a direct comparison.
        if self.is_burning and self.fuel_mass > 0:
            return self.max_thrust * self.throttle * self._thrust_direction
        else:
            return np.zeros(3)


    def compute_thrust_direction(self, target_position):
        # Takes a target position and returns a unit vector pointing from rocket toward target.
        displacement_vector = target_position - self.position
        # Magnitude of "displacement_vector"
        distance = np.linalg.norm(displacement_vector)
        if distance == 0:
            return np.zeros(3)
        else:
            return displacement_vector/distance


    def burn(self, dt, target_position):
        # Fire engine toward target for time dt
        # Updates fuel_mass and self.mass
        if self.fuel_mass <= 0:
            self.is_burning = False
            return

        # Update thrust direction
        self._thrust_direction = self.compute_thrust_direction(target_position)

        # Mass flow rate = thrust / exhaust_velocity
        mass_flow_rate = self.max_thrust / self.exhaust_vel

        # Fuel consumed this time step
        # more time burning = more fuel consumed
        fuel_consumed = mass_flow_rate * dt

        # Don't consume more fuel than we have:
        fuel_consumed = min(fuel_consumed, self.fuel_mass)

        # Update fuel and total mass
        self.fuel_mass -= fuel_consumed
        # subtract the fuel consumed
        self.mass -= fuel_consumed

    def update_phase(self, earth, asteroid):
        # Checks distances and updates mission phase based on where the rocket is
        earth_dist = np.linalg.norm(self.position - earth.position)
        asteroid_dist = np.linalg.norm(self.position - asteroid.position)

        if self.phase == 'launched':
            # 384,399km, avg distance to moon from earth. Below is in AU.
            # Using a tracked Earth to moon distance here would make sense in the future.
            if earth_dist > 0.00256954861:
                self.phase = 'transit'
                print(f"Rocket phase: launched → transit")

        elif self.phase == 'transit':
            # Virtually right on top of asteroid
            # minus 5km in AU(this simulates how far the rocket would follow. Maybe even less)
            if asteroid_dist < 3.34229e-8:
                self.phase = 'capture'
                print(f"Rocket phase: transit → capture")

        elif self.phase == 'capture':
            # Return triggered manually by interception.py
            # when asteroid is ready to be moved
            pass

        elif self.phase == 'return':
            # Complete when close to Lagrange point
            # Will be computed by interception.py
            pass

    def compute_fixed_drones(self):
        return self.drone_count

    def compute_dynamic_drones(self, asteroid, target_position, time_available):
        # instead of abs() using np. for vectors. Abs() works for scalars
        distance = np.linalg.norm(target_position - asteroid.position)

        # delta-v/velocity change
        delta_v = distance / time_available

        # required force: F= ma -> =m*dv/dt
        force = asteroid.mass * delta_v
        print(f"The amount of force required to move {asteroid.name} is: {force}")

        # drones pushing to produce that force?
        # half of drones charging, half applying force.
        active_fraction = 0.5
        # np.ceil rounds a number up to the nearest integer. int() provides float to int
        drones_needed = int(np.ceil(force / (self.drone_thrust * active_fraction)))

        # practical limits
        min_drones = 4
        max_drones = 50

        return max(min_drones, min(max_drones, drones_needed))

    def get_drone_count(self, asteroid=None, target_position=None, time_available=None):
        # edit: 'is' checks memory identity not value equality. == for String Comparison
        if self.drone_mode == 'fixed':
            return self.compute_fixed_drones()

        elif self.drone_mode == 'dynamic':
            if asteroid is None or target_position is None or time_available is None:
                print("Warning: dynamic mode needs asteroid, target and time. Using fixed.")
                return self.compute_fixed_drones()
            return self.compute_dynamic_drones(asteroid, target_position, time_available)

        else:
            print(f'Warning, Unknown Mode: {self.drone_mode}, will now use mode: Fixed')
            # "drone count" is the default and takes the fixed mode
            return self.drone_count

    def __repr__(self):
        fuel_pct = self.fuel_mass / (self.fuel_mass + self.dry_mass) * 100
        return (f"Rocket({self.name}, "f"phase={self.phase}, "
                f"fuel={fuel_pct:.1f}%, "f"pos={self.position})")
