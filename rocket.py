from celestData import CelestData
import numpy as np


# Inheriting CelestData
class Rocket(CelestData):

    def __init__(self, name, radius, dry_mass, fuel_mass,
                 max_thrust, exhaust_vel, position, velocity,
                 reactor_power, reactor_fuel_mass,
                 drone_capacity=10, drone_mode='fixed', drone_thrust=None):

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

