import math

print("-----------------------------------------------------------")
print("Calculating the orbital velocity via Vis-Viva")


class VisVivaEarth:
    """
    Vis-Viva calculates the orbital velocity of a Keplarian object
    at any specific radius between two objects centers of mass.

    Use inheritance for other visviva calculations... variables will have to be public.
    """
    """
    --> numPoints, however many positions that are calculated between perihelion and aphelion
        If numPoints = 100, the code calculates:
        Position 1: at perihelion
        Position 2: slightly farther out
        Position 3: even farther
        ...
        Position 100: at aphelion
    --> gConst, the universal gravitational constant
    --> mass, the mass of the sun
    --> semiMajorAxis, the distance from perihelion to aphelion
    """
    def __init__(self, gConst, mass, semiMajorAxis, eccentricity, numPoints, logger):
        self.logger = logger
        self.gConst = gConst
        self.mass = mass
        self.semiMajorAxis = semiMajorAxis
        self.eccentricity = eccentricity
        self.numPoints = numPoints
        self.velocity = None
        self.radius = None

        # Arrays for visualization
        self.radii = []
        self.velocities = []
        self.results = []

        # Calculate perihelion and aphelion from orbital parameters
        self.perihelion = semiMajorAxis * (1 - eccentricity)
        self.aphelion = semiMajorAxis * (1 + eccentricity)

    def getVelocity(self):
        """Calculate velocities at various radii from perihelion to aphelion"""
        self.results = []
        self.radii = []
        self.velocities = []

        # Generate points from perihelion to aphelion
        for i in range(self.numPoints):
            # Linear interpolation for radius
            radius = self.perihelion + (self.aphelion - self.perihelion) * (i / (self.numPoints - 1))

            # Vis-viva equation: v = sqrt(GM * (2/r - 1/a))
            velocity = math.sqrt((self.gConst * self.mass) * ((2 / radius) - (1 / self.semiMajorAxis)))

            self.logger.info(f"The orbital velocity is: {velocity}, at a radius of {radius}")

            # Append to arrays
            self.radii.append(radius)
            self.velocities.append(velocity)
            self.results.append((radius, velocity))

        # Store last calculated values
        if self.radii:
            self.radius = self.radii[-1]
            self.velocity = self.velocities[-1]

    def printVal(self):
        """Print orbital parameters"""
        print("Gravitational Constant (G): ", self.gConst)
        print("Mass: ", self.mass)
        print("Semi-Major Axis: ", self.semiMajorAxis)
        print("Eccentricity: ", self.eccentricity)
        print("Perihelion: ", self.perihelion)
        print("Aphelion: ", self.aphelion)
        if self.velocity and self.radius:
            print(f"Sample orbital velocity: {self.velocity} m/s at radius {self.radius} m")
        print(f"Calculated {len(self.radii)} orbital points")