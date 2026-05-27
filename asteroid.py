import numpy as np
from celestData import CelestData


class Asteroid(CelestData):
    # Inherits all of CelestData because it adds
    # orbital elements and mission-specific data

    def __init__(self, name, mass, radius, position, velocity, a, e, i, Omega, omega, M, epoch=None):
        # Call parent __init__
        super().__init__(name=name, mass=mass, radius=radius, position=position, velocity=velocity)

        # Store orbital elements
        self.semi_major_axis = a
        self.eccentricity = e
        self.inclination = i
        self.long_asc_node = Omega
        self.arg_perihelion = omega
        self.mean_anomaly = M
        self.epoch = epoch

        # Classify and assign target
        self.orbit_type = self.classify_orbit()
        self.target_lagrange = self.assign_lagrange_target()
        self.threat_level = None  # computed later by interception.py

    @classmethod
    def from_orbital_elements(cls, name, mass, radius, a, e, i, Omega, omega, M, epoch=None):
        # Create an Asteroid from database data
        # Convert elements to state vectors
        position, velocity = cls._elements_to_state(a, e, i, Omega, omega, M)
        return cls(name=name, mass=mass, radius=radius, position=position, velocity=velocity,
                   a=a, e=e, i=i, Omega=Omega, omega=omega, M=M, epoch=epoch)

    @staticmethod
    def _elements_to_state(a, e, i, Omega, omega, M):
        #               Stage 1 — solve Kepler's equation M=E−esin(E)
        # Initial guess and convert M to radians
        M_rad = np.radians(M)
        E = M_rad
        tolerance = 1e-10
        # Iterate until converged. Using "while" to find the convergence:
        while True:
            E_new = E - (E - e * np.sin(E) - M_rad) / (1 - e * np.cos(E))
            # Convergence Check
            # Typically converges in 5-10 iterations.
            if abs(E_new - E) < tolerance:
                break
            E = E_new
        E = E_new
        # E is now the eccentric anomaly in radians

        #               Stage 2 — position in orbital plane
        xOrbit = a * (np.cos(E) - e)
        yOrbit = a * np.sqrt(1 - e**2) * np.sin(E)
        # 3D array - z-component 0.0
        r_orbit = np.array([xOrbit, yOrbit, 0.0])


        #               Stage 3 — velocity in orbital plane
        # Where n is the mean motion(n is the average angular speed of the orbit),
        # Invoking Kepler's 3rd.
        # n=sqrt(GMsun/a^3) = 2pi/T
        # In AU units with G=4π², n simplifies to: n=2pi/a^3/2
        n = (2*np.pi)/(a**(3/2))
        vxOrbit = (-a * n * np.sin(E)) / (1 - e*np.cos(E))
        vyOrbit = (a*n*np.sqrt(1 - e**2)*np.cos(E))/(1 - e * np.cos(E))
        v_orbit = np.array([vxOrbit, vyOrbit, 0.0])
        #

        #               Stage 4 — rotate to 3D ecliptic frame
        # Converting from perifocal PQW to geocentric equatorial IJK coordinates
        # transforms orbital vectors position r and velocity v from an orbital plane frame
        # to an Earth-centered inertial frame.

        # Conversion to rad
        i_rad = np.radians(i)
        Omega_rad = np.radians(Omega)
        omega_rad = np.radians(omega)

        # build rotation matrices then multiply
        def Rz(theta):
            c, s = np.cos(theta), np.sin(theta)
            return np.array([[c, -s, 0.0],
                             [s, c, 0.0],
                             [0.0, 0.0, 1.0]])

        def Rx(theta):
            c, s = np.cos(theta), np.sin(theta)
            return np.array([[1.0, 0.0, 0.0],
                             [0.0, c, -s],
                             [0.0, s, c]])

        # Combined rotation matrix, perifocal to ecliptic
        # Apply: argument of perihelion → inclination → ascending node
        Q = Rz(Omega_rad) @ Rx(i_rad) @ Rz(omega_rad)

        # Rotate to 3D ecliptic frame. @ is matrix multiplication.
        # Proper dot product row-by-column multiplication that rotation matrices require.
        position = Q @ r_orbit
        velocity = Q @ v_orbit
        return position, velocity

    def classify_orbit(self):
        # Needs to be fine-tuned to
        # eccentricity, perihelion and aphelion distances in the future.
        if self.semi_major_axis < 1.0:
            return 'Aten'
        elif self.semi_major_axis < 1.017:
            return 'Apollo'
        elif self.semi_major_axis < 1.3:
            return 'Amor'
        elif self.semi_major_axis < 4.0:
            # MBA = Main Belt Asteroid
            return 'MBA'
        elif self.semi_major_axis < 5.5:
            return 'Jupiter Trojan'
        else:
            return 'Trans Neptunian'

    def assign_lagrange_target(self):
        if self.orbit_type in ['Aten', 'Apollo', 'Amor']:
            return 'L4'  # Earth-Sun L4 — stable, good for NEAs
        elif self.orbit_type == 'MBA':
            return 'L4_Mars'  # Mars-Sun L4 — future development
        else:
            return 'L4'  # default

    def __repr__(self):
        return (f"Asteroid({self.name}, "
                f"a={self.semi_major_axis:.4f} AU, "
                f"e={self.eccentricity:.4f}, "
                f"i={self.inclination:.2f}°, "
                f"type={self.orbit_type}, "
                f"target={self.target_lagrange})")

