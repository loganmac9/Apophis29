from dataclasses import dataclass, field
import numpy as np


# Learned that the @dataclass decorator auto-generates __init__
# so I don't have to write it manually
@dataclass
class CelestData:
    name: str
    mass: float
    radius: float

    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    #@property turns a method into a computed attribute
    #It will be called like an attribute, no parentheses:
    #earth.kinetic_energy, not earth.getKE()
    @property
    def kinetic_energy(self):
        #1/2mv^2
        return (1/2)*self.mass*np.dot(self.velocity, self.velocity)

    @property
    def speed(self):
        return np.linalg.norm(self.velocity)

    # Useful for debugging: Controls what prints when I  do, print(earth), str(earth).
    # gets something like:CelestData(Earth, mass=5.972e+24, pos=[1.496e+11, 0. 0.]) rather than:
    # <CelestData object at 0x7f3a2b1c4d90>
    def __repr__(self):
        return f"CelestData({self.name}, mass={self.mass:.3e}, pos={self.position})"
