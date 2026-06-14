from celestData import CelestData
import numpy as np

class Drone(CelestData):
    # Class represents one drone in the swarm of N drones

    # Has a battery that charges on the rocket and depletes while thrusting
    # Cycles through 4 modes automatically:
    #     charging   → on rocket, battery filling up
    #     deploying  → flying from rocket to asteroid
    #     thrusting  → pushing asteroid
    #     returning  → flying back to rocket to recharge
    # Calling parent __init__ from CelestData
    def __init__(self, drone_id, mass, radius, position, velocity, parent_rocket, target_asteroid,
                 charge_rate=50.0, max_charge=1000.0, charge_level=1, thrust_mag=1e-30, cruise_speed=0.1,
                 formation_offset=None):

        super().__init__(name=f"Drone_{drone_id}", radius=radius, mass=mass,
                            position=position, velocity=velocity)

        # Class attributes:
        self.charge_level = charge_level  # Current battery
        self.max_charge = max_charge  # 1000kWh battery
        self.charge_rate = charge_rate
        # how hard it can push (newtons equivalent in AU units)
        self.thrust_mag = thrust_mag
        # Power = Force × velocity
        #       = thrust_magnitude × drone_speed
        # Full charge lasts 2 hours in AU/year time units
        charge_duration = 2 / (365.25 * 24)  # 2 hours in years
        self.drain_rate = 1.0 / charge_duration
        # Set velocity toward target at drone's cruise speed
        self.cruise_speed = cruise_speed  # AU/year — adjust as needed

        self.mode = 'deploying'
        self.parent_rocket = parent_rocket  # reference to the Rocket object
        self.target_asteroid = target_asteroid  # reference to the asteroid being pushed
        self.thrust_dir = np.zeros(3)  # unit vector — which way it's pushing

        self.formation_offset = formation_offset if formation_offset is not None \
                                else np.zeros(3)
        self.drone_id = drone_id

    @property
    def thrust_vector(self):
        # Used by gravity.py to add thrust acceleration
        if self.mode == 'thrusting' and self.charge_level > 0:
            return self.thrust_mag * self.thrust_dir
        else:
            return np.zeros(3)

    def has_enough_charge_to_return(self):
        # Distance to rocket
        distance_to_rocket = np.linalg.norm(
            self.parent_rocket.position - self.position
        )

        # Time to travel that distance at cruise speed
        travel_time = distance_to_rocket / self.cruise_speed

        # Charge needed for return trip
        charge_needed = (self.drain_rate / self.max_charge) * travel_time

        # Safety margin — keeping 10% extra
        safety_margin = 0.1

        # produces a boolean
        return self.charge_level > (charge_needed + safety_margin)

    # Loops through all the drones in simulation.py
    def update(self, dt):
        if self.mode == 'charging':
            self._update_charging(dt)
        elif self.mode == 'deploying':
            self._update_deploying(dt)
        elif self.mode == 'thrusting':
            self._update_thrusting(dt)
        elif self.mode == 'returning':
            self._update_returning(dt)

    # Checking charge level/ current charge
    def _update_charging(self, dt):
        # If mode is in charging then new max charge will be charge rate over time.
        # update charge_level:
        self.charge_level += (self.charge_rate / self.max_charge) * dt
        self.charge_level = min(1.0, self.charge_level)

        # Stay physically on the rocket while charging
        self.position = self.parent_rocket.position.copy()
        self.velocity = self.parent_rocket.velocity.copy()

        print(f"⚡︎⚡︎⚡︎Charging Battery⚡︎⚡︎⚡︎\nCurrent Drone, {self.drone_id} \nBattery charge: {self.charge_level*100:.1f}%\n\n")
        if self.charge_level >= 1.0:
            self.mode = 'deploying'

    # Drones move by updating their velocity which the integrator uses to update position
    def _update_deploying(self, dt):
        # drones fly toward asteroid, drains battery ->
        # needs a dynamic charge level that is dependent on the distance traveled.
        # If the rocket is too far away the rocket needs to move closer so that the drones don't expend too much power.
        target = self.target_asteroid.position + self.formation_offset
        direction = target - self.position
        distance = np.linalg.norm(direction)

        if distance < 1e-6:
            self.mode = 'thrusting'
            return

        # Emergency return — not enough charge to get back
        if not self.has_enough_charge_to_return():
            self.mode = 'returning'
            print(f"Drone {self.drone_id}: low charge during deployment "
                    f"→ returning early\nCurrent Charge: {self.charge_level*100:.1f}%\n\n")

            return

        self.velocity = (direction / distance) * self.cruise_speed
        self.charge_level -= (self.drain_rate / self.max_charge) * dt
        self.charge_level = max(0.0, self.charge_level)

    def _update_thrusting(self, dt):
        self.position = self.target_asteroid.position + self.formation_offset
        self.velocity = self.target_asteroid.velocity.copy()

        away = self.position - self.target_asteroid.position
        dist = np.linalg.norm(away)
        if dist > 0:
            self.thrust_dir = away / dist

        self.charge_level -= self.drain_rate * dt
        self.charge_level = max(0.0, self.charge_level)

        # Dynamic return check — leave when you have just enough to get back
        if not self.has_enough_charge_to_return():
            self.mode = 'returning'
            self.thrust_dir = np.zeros(3)
            print(f"Drone {self.drone_id}: insufficient charge → returning\n")
            print(f"Charge: {self.charge_level * 100:.1f}%\n"
                  f"Distance to rocket: {np.linalg.norm(self.parent_rocket.position - self.position):.6f} AU\n\n")

    def _update_returning(self, dt):
        # flies back to rocket, drains battery
        # Assuming a charge level of 0.1(10% battery) is when the drone should return to charge.
        # Calc direction to rocket
        direction = self.parent_rocket.position - self.position
        # Normalize direction
        direction = direction / np.linalg.norm(direction)
        # Velocity update for integrator
        self.velocity = direction * self.cruise_speed
        # update charge_level - draining:
        self.charge_level -= (self.drain_rate / self.max_charge) * dt
        distance = np.linalg.norm(self.parent_rocket.position - self.position)
        if distance < 1e-6:
            self.mode = 'charging'
            print(f"Drone {self.drone_id}: at rocket → "
                  f"Starting charge\n Current Charge: {self.charge_level*100:.1f}%\n\n")

    def compute_thrust_direction(self, target_position):
        # direction to push asteroid
        # Takes a target position and returns a unit vector pointing from asteroid toward target.
        displacement_vector = target_position - self.position
        # Magnitude of "displacement_vector"
        distance = np.linalg.norm(displacement_vector)
        if distance == 0:
            return np.zeros(3)
        else:
            return displacement_vector / distance

    def is_at_asteroid(self):
        # checks if close enough to push
        # True if within formation distance of asteroid
        dist = np.linalg.norm(self.position - self.target_asteroid.position)
        # returns a bool
        return dist < 1e-6

    def is_at_rocket(self):
        # checks if close enough to recharge
        # True if within docking distance of rocket
        dist = np.linalg.norm(self.position - self.parent_rocket.position)
        # returns a bool
        return dist < 1e-6

    def __repr__(self):
        return (f"Drone({self.drone_id}, "
                f"mode={self.mode}, "
                f"charge={self.charge_level * 100:.1f}%)")